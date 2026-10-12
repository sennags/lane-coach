# Lane Coach

Consulta local de campeões de League of Legends com Flask, HTML/CSS/JavaScript e arquivos JSON. A seleção combina os dados dos dois campeões sem buscar serviços externos.

**Estado: versão 0.11.** Catálogo local do patch 16.20.1 com 173 campeões; 171 disponíveis. Aphelios e Hwei estão em manutenção. A ficha mostra role principal, classe e dano predominante; campeões de jungle conservam notas editoriais de invasão, gank e risco. HABILIDADES mostra ícone, tecla, nome e recarga, com espaço para uma evolução futura. USO/LIMITE, descrições e planos antigos permanecem nos JSON, sem renderização.

Os dados são editoriais e continuam sem revisão especializada. A posição é uma referência, e dano Físico/Mágico/Misto não equivale a AD/AP. Fontes, patch e autoria permanecem na base; não comprovam vantagem em um confronto. O comportamento Agressivo/Passivo antigo também permanece nos JSON, sem aparecer na tela.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14). Dentro da pasta do projeto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PORT = '5003'
.\.venv\Scripts\python.exe server.py
```

Abra [a aplicação local](http://127.0.0.1:5003/). Mantenha o terminal aberto; Ctrl+C encerra. Não é necessário ativar a venv ou configurar credenciais. Sem PORT, o padrão é 5000; HOST é 127.0.0.1.

A página inicial mostra Yone/Ahri. Busca/troca e seleção de lane preservam o contexto e funcionam com teclado; sem JavaScript, os seletores e o botão de consulta permanecem disponíveis. O servidor valida entradas, rejeita campeões iguais e informa manutenção. A rota selecionada não altera as categorias independentes nem calcula vantagem da dupla.

## Dados e manutenção

- `lane_coach/data/champions/`: dados por campeão, fatos do kit, categorias editoriais, notas e proveniência.
- `lane_coach/data/roster.json`: catálogo local e patch.
- `lane_coach/data/cooldown_rules.json`: fontes e condições das notas complementares de recarga.
- `lane_coach/static/champions/` e `lane_coach/static/abilities/`: imagens locais e registros de origem.
- `lane_coach/knowledge.py`, `classification.py` e `cooldowns.py`: composição e validação dos dados locais.
- `lane_coach/templates/` e `static/`: interface.
- `lane_coach/db.py`: SQLite legado e backup.

Atualizações são manuais. Preserve as fontes, o patch e o estado de revisão; verifique dados e imagens antes de reiniciar o servidor. Alterar a versão do catálogo não revisa estratégia automaticamente. Recargas são valores de referência do kit, sem acompanhamento da partida.

O SQLite legado `instance/lane-coach.sqlite3` conserva três guias demonstrativos antigos e é usado na inicialização e no health check. A consulta atual usa os JSON carregados em memória. Não há coleta de partidas, estatísticas, geração de conteúdo, cadastro, cookies, analytics ou histórico de visitantes.

## Verificação e backup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flask --app lane_coach backup-db instance/backup-01.sqlite3
```

O backup usa o SQLite e recusa sobrescrever um arquivo existente. Para restaurar, pare a aplicação e configure DATABASE_PATH para uma cópia do backup. Nunca publique bancos ou backups.

`GET /` mostra a seleção inicial. `GET /matchup?champion=Yone&opponent=Ahri&lane=mid` mostra os perfis locais; lanes aceitas: general, top, jungle, mid, adc e support. Entradas inválidas: 400; rota inexistente: 404; manutenção: 503; método não permitido: 405. `GET /healthz` verifica o banco legado e retorna `{"status":"ok"}` quando disponível.

## Hospedagem e proteção de dados

Ainda não houve deploy público. Hospedagem totalmente gratuita continua sendo requisito; a solução final permanece pendente. Flask/Waitress e SQLite exigem Python e disco persistente. Configure HOST/PORT conforme a hospedagem, DATABASE_PATH em volume persistente, HTTPS e backup antes da publicação.

Validação no servidor, SQL parametrizado, escape de templates e CSP restritiva continuam ativos. A seleção pode aparecer no histórico do navegador; não inclua dados pessoais. O aplicativo não registra consultas nem configura logs de acesso. Erros de banco registram somente a classe da exceção. Revise retenção de logs da hospedagem e os arquivos enviados antes de publicar.
