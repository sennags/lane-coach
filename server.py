"""Local by default. Set HOST and PORT explicitly when deploying."""
import os

from waitress import serve

from lane_coach import create_app


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))
    print(f'Lane Coach: http://{host}:{port}', flush=True)
    serve(create_app(), host=host, port=port, threads=4, max_request_body_size=16384)
