# Lane Coach

Perfis de Yone, Ahri, Yasuo e Zed: pontos fortes, fracos, habilidades e plano para lane phase, mid e late game. A combinação dos arquivos de cada campeão atende às 12 duplas direcionais, sem cadastrar guias por confronto. Flask + HTML/CSS; SQLite legado preservado.

**Estado:** versão local 0.3. Dois perfis lado a lado, com comportamento típico e plano por fase; o perfil adversário inclui orientações de resposta. As dicas de micro anteriores continuam em seção expansível. Dicas editoriais ainda sem revisão especializada. A tela não usa IA; existe um comando de avaliação opcional com Groq, sem teste real do provedor ainda. Sem deploy público. Nenhum conteúdo do MOBAFire foi copiado.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Abra http://127.0.0.1:5000. O Waitress escuta apenas neste computador por padrão. Ctrl+C encerra. Não é necessário ativar a venv.

A base atual fica em `lane_coach/data/champions/*.json` e é carregada em memória no início. Reinicie o servidor depois de editar os arquivos. A versão da base é calculada pelo conteúdo. Não há geração antecipada de combinações nem histórico de consultas. O SQLite da primeira versão é preservado para não perder conteúdo anterior; seus guias não alimentam mais a tela. Não há cache de respostas de IA nesta etapa.

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
- `lane_coach/data/champions/`: um JSON por campeão, com fatos oficiais, fonte e dicas editoriais separadas.
- `lane_coach/knowledge.py`: composição determinística da perspectiva escolhida.
- `lane_coach/generation.py`: avaliação Groq somente por CLI.
- `lane_coach/data/guides.json`: conteúdo legado preservado da versão 0.1.
- `lane_coach/templates/` e `static/`: interface e imagens locais.
- `tests/`: consultas, validação, privacidade, persistência, backup e falha do banco.

`GET /matchup?champion=Yone&opponent=Ahri&lane=mid` retorna o guia. Entradas inválidas: 400; confrontos sem conteúdo: 404; falha de banco: 503. `GET /healthz` verifica o banco. A direção troca quais dicas são selecionadas; não são interações específicas comprovadas entre os dois kits. As 12 duplas locais estão disponíveis.

## Proteção de dados

Na página: sem cadastro, cookies, analytics, conta Riot ou chamadas a IA. O banco guarda somente campeões e guias. Imagens são servidas localmente. A seleção aparece na URL e pode ficar no histórico do navegador; não inclua dados pessoais. O aplicativo não registra consultas nem configura logs de acesso. Erros de banco registram apenas a classe da exceção.

Validação no servidor, SQL parametrizado, escape de templates e CSP restritiva. Não há credenciais necessárias nesta etapa. `.env`, bancos e ambientes locais são ignorados pelo Git. Revise arquivos antes de publicar.

## Deploy e próximos passos

Ainda não existe URL pública da aplicação. Use uma hospedagem Python com HTTPS e disco persistente, em uma instância. Configure `HOST=0.0.0.0`, `PORT` conforme a plataforma e `DATABASE_PATH` no disco persistente. Instale `requirements.txt` e execute `python server.py`. Não use SQLite em disco efêmero. Configure backup e revise retenção de logs/IPs na hospedagem antes da abertura pública.

Próximos passos: revisar os três guias com fontes e patch; publicar a versão determinística; testar Groq com chave somente no servidor, timeout, validação e cota persistente. Não há limite de IA implementado porque ainda não existe geração por IA.

## Créditos

Ilustrações da Riot Games obtidas do Data Dragon em 2026-10-11: `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{Champion}_0.jpg`, para Yone, Ahri, Yasuo e Zed. Esses endereços não fixam patch e não são fonte das recomendações. Textos demonstrativos próprios.

Lane Coach isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties, are trademarks or registered trademarks of Riot Games, Inc.

## Base e avaliação da IA

Cada campeão contém `facts` (descrições oficiais de habilidades), `tips` (dicas editoriais com IDs de evidência), `source` (URL, patch dos dados e data de acesso) e `profile`: `identity`, `strengths`, `weaknesses`, `phases` e estado de revisão. Em cada fase (`lane`, `mid`, `late`), `typical` descreve o comportamento habitual, `plan` orienta quem joga com o campeão e `against` orienta quem o enfrenta. A base rejeita perfis sem fases ou campos obrigatórios e revisão sem data. Adicionar um campeão exige conteúdo completo e ilustração local; não basta acrescentar um nome ao seletor. A fonte da habilidade não comprova a estratégia nem interações especiais. O patch 16.20.1 identifica o snapshot dos dados, não uma revisão competitiva das dicas. O contexto não contém nível, vida ou cooldown atual: orientações devem ser condicionais.

Para inspecionar o contexto sem rede, chave ou custo:

```powershell
.\.venv\Scripts\python.exe -m flask --app lane_coach preview-ai Yone Ahri
```

Para avaliar o Groq, configure `GROQ_API_KEY` e `GROQ_MODEL` somente no ambiente local. O aplicativo não lê `.env` automaticamente. Nunca envie a chave ao chat, ao Git ou ao navegador. Uma forma de fornecer a chave sem gravá-la no histórico do PowerShell:

```powershell
$groqCredential = Read-Host 'Chave Groq' -AsSecureString
$env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', $groqCredential).Password
$env:GROQ_MODEL = Read-Host 'ID do modelo habilitado na sua conta e compatível com JSON Object Mode'
.\.venv\Scripts\python.exe -m flask --app lane_coach preview-ai Yone Ahri --generate
Remove-Item Env:GROQ_API_KEY
```

`--generate` envia o contexto dos dois campeões ao Groq e pode consumir cota/créditos da conta. Não transmite dados de visitantes. Faz uma tentativa, com timeout de rede de 20 segundos e limite de resposta. A saída vai ao terminal, identificada como não revisada; não é salva no banco nem exibida automaticamente no site. Respostas incompletas, campos inválidos e IDs de evidência inexistentes são rejeitados. Validar formato e IDs **não comprova correção estratégica**. Nenhuma promessa de gratuidade ou disponibilidade.

Documentação oficial: [API compatível](https://console.groq.com/docs/openai), [formatos estruturados e JSON Object Mode](https://console.groq.com/docs/structured-outputs), [modelos disponíveis](https://console.groq.com/docs/models). O modelo é configurável; confira suporte e condições na sua conta.

Os testes do adaptador usam respostas simuladas para sucesso, timeout, cota, JSON inválido, truncamento, tamanho e evidências. Não equivalem a uma chamada real ou avaliação de qualidade do modelo.

A consulta principal é independente de IA, chave e orçamento de geração. Os perfis não calculam vencedor, dano, vantagem por nível, builds ou resultados garantidos. O comando Groq abaixo é uma ferramenta experimental do operador para uma etapa futura.
