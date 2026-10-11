# Lane Coach

Consulta de guias de lane: Yone contra Ahri, Yasuo ou Zed, na rota mid. Flask + HTML/CSS + SQLite.

**Estado:** primeira versão local. Os três textos são demonstrações próprias, sem revisão de gameplay ou patch validado. Ainda não há IA nem deploy público. Nenhum guia ou comentário do MOBAFire foi copiado.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Abra http://127.0.0.1:5000. O Waitress escuta apenas neste computador por padrão. Ctrl+C encerra. Não é necessário ativar a venv.

O banco `instance/lane-coach.sqlite3` é criado no primeiro início. Reiniciar preserva conteúdo existente; editar o JSON inicial não altera registros já salvos.

## Testes e backup

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m flask --app lane_coach backup-db instance/backup-01.sqlite3
```

O backup usa a API SQLite e recusa sobrescrever arquivos. Para restaurar, pare o servidor e configure `DATABASE_PATH` para uma cópia do backup. Nunca publique bancos ou backups no Git.

## Estrutura

- `lane_coach/__init__.py`: rotas, validação e cabeçalhos de segurança.
- `lane_coach/db.py`: persistência e backup.
- `lane_coach/data/guides.json`: conteúdo inicial demonstrativo.
- `lane_coach/templates/` e `static/`: interface e imagens locais.
- `tests/`: consultas, validação, privacidade, persistência, backup e falha do banco.

`GET /matchup?champion=Yone&opponent=Ahri&lane=mid` retorna o guia. Entradas inválidas: 400; confrontos sem conteúdo: 404; falha de banco: 503. `GET /healthz` verifica o banco. Confrontos inversos não são inferidos.

## Proteção de dados

Sem cadastro, cookies, analytics, conta Riot ou chamadas a IA. O banco guarda somente campeões e guias. Imagens são servidas localmente. A seleção aparece na URL e pode ficar no histórico do navegador; não inclua dados pessoais. O aplicativo não registra consultas nem configura logs de acesso. Erros de banco registram apenas a classe da exceção.

Validação no servidor, SQL parametrizado, escape de templates e CSP restritiva. Não há credenciais necessárias nesta etapa. `.env`, bancos e ambientes locais são ignorados pelo Git. Revise arquivos antes de publicar.

## Deploy e próximos passos

Ainda não existe URL pública da aplicação. Use uma hospedagem Python com HTTPS e disco persistente, em uma instância. Configure `HOST=0.0.0.0`, `PORT` conforme a plataforma e `DATABASE_PATH` no disco persistente. Instale `requirements.txt` e execute `python server.py`. Não use SQLite em disco efêmero. Configure backup e revise retenção de logs/IPs na hospedagem antes da abertura pública.

Próximos passos: revisar os três guias com fontes e patch; publicar a versão determinística; testar Groq com chave somente no servidor, timeout, validação e cota persistente. Não há limite de IA implementado porque ainda não existe geração por IA.

## Créditos

Ilustrações da Riot Games obtidas do Data Dragon em 2026-10-11: `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{Champion}_0.jpg`, para Yone, Ahri, Yasuo e Zed. Esses endereços não fixam patch e não são fonte das recomendações. Textos demonstrativos próprios.

Lane Coach isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties, are trademarks or registered trademarks of Riot Games, Inc.
