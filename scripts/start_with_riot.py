"""Start the local server with a hidden Riot key prompt and file-based logs."""
import argparse
import getpass
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import socket
import sys
import threading
from urllib.request import ProxyHandler, build_opener
import warnings


ROOT = Path(__file__).resolve().parents[1]


def hidden_input_available():
    if not sys.stdin.isatty():
        return False
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetStdHandle.argtypes = [wintypes.DWORD]
        kernel.GetStdHandle.restype = wintypes.HANDLE
        kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetConsoleMode.restype = wintypes.BOOL
        mode = wintypes.DWORD()
        return bool(kernel.GetConsoleMode(kernel.GetStdHandle(wintypes.DWORD(-10)), ctypes.byref(mode)))
    return True


def announce_ready(port):
    url = f'http://127.0.0.1:{port}'
    try:
        with build_opener(ProxyHandler({})).open(url + '/healthz', timeout=5) as response:
            healthy = json.load(response).get('status') == 'ok'
    except (OSError, ValueError):
        healthy = False
    if healthy:
        print(f'Servidor pronto: {url}/', flush=True)
        print('Abra o link no navegador e selecione uma lane para consultar a Riot.', flush=True)
    else:
        print('O servidor nao respondeu. Consulte instance/server-error.log.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=5005)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error('Use uma porta entre 1024 e 65535.')
    with socket.socket() as probe:
        probe.settimeout(1)
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            print(f'A porta {args.port} ja esta em uso. Pare a instancia anterior ou use --port 5006.')
            return 1

    key = os.environ.get('RIOT_API_KEY', '')
    if not key:
        if not hidden_input_available():
            print('Execute este comando em um PowerShell aberto para digitar a chave com seguranca.')
            return 1
        print('Cole a chave com o botao direito ou Shift+Insert; depois pressione Enter.', flush=True)
        print('O texto da chave fica oculto; no Python 3.14 aparecem apenas asteriscos.', flush=True)
        try:
            with warnings.catch_warnings():
                # Never fall back to echoing a credential in an unsupported terminal.
                warnings.simplefilter('error', getpass.GetPassWarning)
                options = {'echo_char': '*'} if sys.version_info >= (3, 14) else {}
                key = getpass.getpass('Chave Riot: ', **options)
        except (getpass.GetPassWarning, EOFError, OSError):
            print('Execute este comando em um PowerShell aberto para digitar a chave com seguranca.')
            return 1
    if not key or not key.isascii() or any(not 33 <= ord(character) <= 126 for character in key):
        parser.error('Entrada invalida: copie a chave novamente e cole com o botao direito ou Shift+Insert.')
    os.environ['RIOT_API_KEY'] = key

    log_path = ROOT / 'instance/server-error.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(log_path, maxBytes=512_000, backupCount=1, encoding='utf-8')
    handler.namer = lambda name: name + '.log'
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
        handlers=[handler],
    )
    sys.path.insert(0, str(ROOT))
    from lane_coach import create_app
    from waitress.server import create_server

    try:
        server = create_server(create_app(), host='127.0.0.1', port=args.port,
                               threads=4, max_request_body_size=16384)
    except OSError:
        print(f'Nao foi possivel iniciar na porta {args.port}. Pare a instancia anterior ou use --port 5006.')
        return 1
    print('Mantenha esta janela aberta. Ctrl+C encerra o servidor.', flush=True)
    threading.Thread(target=announce_ready, args=(args.port,), daemon=True).start()
    try:
        server.run()
    finally:
        server.close()
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
