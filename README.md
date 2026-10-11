# Lane Coach

Catálogo completo: 173 campeões do Data Dragon 16.20.1, com habilidades, imagens locais, perfis e seleção pesquisável dos dois campeões. A consulta combina dois arquivos em memória, sem cadastrar guias por confronto. Flask + HTML/CSS; SQLite legado preservado.

**Estado:** versão local 0.5, com o design Seleção competitiva integrado. Dois perfis lado a lado, com comportamento típico e plano por fase; o perfil adversário inclui orientações de resposta. As dicas de micro específicas anteriores aparecem quando há conteúdo editorial disponível para os campeões selecionados. Os quatro perfis originais são específicos por campeão. Os outros 169 têm habilidades e dicas do catálogo oficial, quando disponíveis, e planos gerais pela classe principal da Riot. A interface identifica o plano por classe. Todo conteúdo estratégico ainda aguarda revisão especializada. A tela não usa IA; existe um comando de avaliação opcional com Groq, sem teste real do provedor ainda. Sem deploy público. Nenhum conteúdo do MOBAFire foi copiado.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Abra http://127.0.0.1:5000. O Waitress escuta apenas neste computador por padrão. Ctrl+C encerra. Não é necessário ativar a venv.

A página inicial mostra Yone e Ahri. **Trocar campeão** abre uma seleção pesquisável com os 173 campeões; a escolha consulta o Flask e atualiza os dois perfis. A seleção impede repetir o adversário, e o servidor valida todas as entradas. As abas Lane phase, Mid game e Late game alternam os planos dos dois lados sem rede. Sem JavaScript, seletores nativos e um botão de consulta permanecem disponíveis, e as três fases são exibidas. Composições é uma possibilidade futura, sem análise implementada.

O visual usa navegação lateral, destaque vermelho, corte inclinado nas imagens, adversário alinhado à direita e fases centralizadas. Não há subtítulos oficiais sob os nomes dos campeões.

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

`GET /` mostra os perfis iniciais. `GET /matchup?champion=Yone&opponent=Ahri&lane=general` retorna os perfis selecionados; `lane=mid` é aceito por compatibilidade. Entradas inválidas, repetidas ou com parâmetros extras: 400; rota inexistente: 404; falha de banco: 503. `GET /healthz` verifica o SQLite legado. Todos os 173 campeões podem ser selecionados em pares distintos. A direção troca quais dicas são selecionadas; não são interações específicas comprovadas entre os dois kits.

## Proteção de dados

Na página: sem cadastro, cookies, analytics, conta Riot ou chamadas a IA. O banco guarda somente campeões e guias. Imagens são servidas localmente. A seleção aparece na URL e pode ficar no histórico do navegador; não inclua dados pessoais. O aplicativo não registra consultas nem configura logs de acesso. Erros de banco registram apenas a classe da exceção.

Validação no servidor, SQL parametrizado, escape de templates e CSP restritiva. Não há credenciais necessárias nesta etapa. `.env`, bancos e ambientes locais são ignorados pelo Git. Revise arquivos antes de publicar.

## Deploy e próximos passos

Ainda não existe URL pública da aplicação. Use uma hospedagem Python com HTTPS e disco persistente, em uma instância. Configure `HOST=0.0.0.0`, `PORT` conforme a plataforma e `DATABASE_PATH` no disco persistente. Instale `requirements.txt` e execute `python server.py`. Não use SQLite em disco efêmero. Configure backup e revise retenção de logs/IPs na hospedagem antes da abertura pública.

A hospedagem será decidida antes de iniciar o deploy. Preparação independente da plataforma:

- Instalação: `python -m pip install -r requirements.txt`.
- Inicialização: `python server.py`, com `HOST=0.0.0.0` e `PORT` definido pela plataforma.
- Persistência: `DATABASE_PATH` deve apontar para o arquivo SQLite em um volume persistente gravável. A base de campeões vem do Git e não precisa de escrita em produção. O SQLite é legado, mas ainda é inicializado e consultado pelo health check.
- Saúde: `/healthz` deve responder 200 e `{"status":"ok"}`.
- Backup: usar o comando `backup-db`, guardar cópia fora da instância e validar restauração; configurar periodicidade na hospedagem escolhida.
- Privacidade: conferir retenção de logs do provedor e evitar registrar query strings. Não configurar chaves de IA para a versão pública atual.
- Após publicar: validar HTTPS, página inicial, seleção de dois campeões, fases, habilidades, imagens locais, celular e respostas 400/404. Registrar URL pública neste README.

Verificação local da versão 0.5: 52 testes pytest; Playwright com os 173 campeões nos seletores, buscas normalizadas, perspectiva dos planos, fases, habilidades, volta do navegador, desktop/celular, Escape e navegação sem JavaScript. Sem cookies, chamadas externas ou erros JavaScript no fluxo testado. Isso não substitui a verificação na hospedagem.

Próximos passos: decidir hospedagem, publicar e verificar a versão determinística; revisar os perfis gerais com fontes e patch. IA analítica e builds permanecem futuras. Não há limite de IA implementado porque ainda não existe geração por IA na página.

## Créditos

Ilustrações da Riot Games obtidas do Data Dragon em 2026-10-11: `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{Champion}_0.jpg`, para os IDs listados em `lane_coach/data/roster.json`. Esses endereços não fixam patch e não são fonte das recomendações. Planos editoriais próprios; habilidades e dicas do catálogo são atribuídas à Riot.

Lane Coach isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties, are trademarks or registered trademarks of Riot Games, Inc.

## Base e avaliação da IA

Cada campeão contém `facts` (descrições oficiais de habilidades), `tips` (dicas editoriais com IDs de evidência), `source` (URL, patch dos dados e data de acesso) e `profile`: `identity`, `strengths`, `weaknesses`, `phases` e estado de revisão. Em cada fase (`lane`, `mid`, `late`), `typical` descreve o comportamento habitual, `plan` orienta quem joga com o campeão e `against` orienta quem o enfrenta. A base rejeita perfis sem fases ou campos obrigatórios e revisão sem data. Adicionar um campeão exige conteúdo completo e ilustração local; não basta acrescentar um nome ao seletor. A fonte da habilidade não comprova a estratégia nem interações especiais. O patch 16.20.1 identifica o snapshot dos dados, não uma revisão competitiva das dicas. O contexto não contém nível, vida ou cooldown atual: orientações devem ser condicionais. Os perfis são gerais e não indicam a melhor rota de cada campeão. O parâmetro `lane=general` é usado pela tela; `lane=mid` é mantido por compatibilidade.

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

## Atualizar o elenco oficial

```powershell
.\.venv\Scripts\python.exe scripts/import_roster.py --patch 16.20.1
```

Execute a importação com o servidor parado e revise o diff antes de publicar. Ela baixa o catálogo, dados e imagens ausentes com concorrência limitada; valida a base completa em uma pasta temporária antes de copiar os arquivos. Preserva perfis específicos e dicas editoriais existentes. Não chama IA nem exige uma chave Riot. O patch é explícito; arquivos JSON em cache opcionais devem corresponder à versão solicitada.

`lane_coach/data/roster.json` registra a lista e as fontes do snapshot. `profile_templates.json` contém os planos editoriais por classe usados para perfis iniciais; eles não são análises individualizadas. As dicas oficiais `allytips` e `enemytips` podem estar ausentes ou conter orientações antigas, inclusive após reworks. São identificadas como dicas do catálogo, sem declaração de revisão competitiva. O importador não fabrica dicas oficiais quando elas estão vazias.

O snapshot não se atualiza sozinho: novos campeões ou patches exigem nova importação e revisão. A seleção inteira funciona sem rede externa durante o uso, sem chave de IA e sem gerar todas as combinações. Os testes verificam correspondência com o manifesto, habilidades, imagens, preservação dos quatro perfis e uma consulta por campeão.

Fontes: [Data Dragon — documentação oficial](https://developer.riotgames.com/docs/lol#data-dragon), [catálogo pt_BR 16.20.1](https://ddragon.leagueoflegends.com/cdn/16.20.1/data/pt_BR/champion.json). Ilustrações do elenco usam a mesma origem oficial indicada nos créditos.
