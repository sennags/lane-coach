# Lane Coach

Catálogo completo: 173 campeões do Data Dragon 16.20.1, com habilidades, imagens locais, perfis e seleção pesquisável dos dois campeões. A consulta combina dois arquivos em memória, sem cadastrar guias por confronto. Flask + HTML/CSS; SQLite legado preservado.

**Estado:** versão local 0.7, com Plano direto integrado ao visual Seleção competitiva. A tela tem duas seções: fases do jogo e HABILIDADES. Cada fase usa recurso, ação e cuidado, com “Seu plano” à esquerda e “Como responder” à direita. Lane phase trata do uso e da resposta aos kits; mid/late tratam de mapa, time, objetivos e pressão lateral. Não há seção separada de pontos fortes/vulnerabilidades ou biblioteca de micro; seus dados anteriores foram preservados.

Seis perfis editoriais específicos: Yone, Ahri, Yasuo, Zed, Akshan e Aatrox, com notas de uso/limite nas habilidades. Os outros 167 são iniciais por classe; Aphelios e Hwei continuam em manutenção, deixando 165 perfis por classe disponíveis. Neles, as habilidades mostram ícone, tecla, nome e recarga base, com aviso de notas ainda não preparadas. Descrições oficiais não aparecem na interface; permanecem nos JSON como base mecânica. Toda estratégia aguarda revisão especializada. Dados independentes por campeão, sem análise validada da dupla ou adaptação por rota. Consulta sem IA, cadastro ou histórico de visitantes. Experimento Groq continua somente CLI, sem teste real do provedor. Sem deploy público ou conteúdo copiado do MOBAFire.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Abra http://127.0.0.1:5000. O Waitress escuta apenas neste computador por padrão. Ctrl+C encerra. Não é necessário ativar a venv.

A página inicial mostra Yone e Ahri. A seção inferior apresenta somente as habilidades dos dois lados, sempre visíveis, sob um único título HABILIDADES preto e centralizado, sem repetir nomes, rótulos de lado, identidades ou dicas do catálogo. Cada habilidade mostra ícone oficial local, tecla, nome e recarga base por nível da habilidade, importada do Data Dragon 16.20.1. Passivas indicam recarga não informada; valores zero são identificados como valores do catálogo. Aceleração e efeitos do kit podem alterar os tempos, e esta lista não acompanha a partida. Nos seis perfis preparados, uso e limite ficam visíveis. Os demais mostram ícone, tecla e nome, sem inventar notas. Descrições oficiais e o aviso geral de revisão foram removidos da tela, preservando os dados de fonte, patch e revisão na base. As fontes oficiais são mantidas. **Trocar campeão** abre uma seleção pesquisável com os 173 campeões; a escolha consulta o Flask e atualiza os dois perfis. A seleção impede repetir o adversário, e o servidor valida todas as entradas. A lane (Top, Jungle, Mid, ADC ou Support) é escolhida em uma barra compacta com ícones vetoriais locais, centralizada abaixo do VS. A seleção fica vermelha e é preservada ao trocar campeão e ao voltar pelo navegador. Os botões funcionam por teclado; sem JavaScript, permanece o seletor nativo. Ela registra o contexto; os planos atuais ainda são gerais por campeão e não mudam conforme a rota. As abas Lane phase, Mid game e Late game alternam os planos dos dois lados sem rede. O adversário mostra recurso, ação de resposta e cuidado; o trecho extra Plano para quem joga foi removido da interface, mantendo os dados no JSON. Sem JavaScript, seletores nativos e um botão de consulta permanecem disponíveis, e as três fases são exibidas. Composições é uma possibilidade futura, sem análise implementada.

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

`GET /` mostra os perfis iniciais. `GET /matchup?champion=Yone&opponent=Ahri&lane=general` retorna os perfis selecionados; `lane=mid` é aceito por compatibilidade. Entradas inválidas, repetidas ou com parâmetros extras: 400; rota inexistente: 404; falha de banco: 503. `GET /healthz` verifica o SQLite legado. O catálogo mantém os 173 campeões. Aphelios e Hwei estão em manutenção: aparecem identificados e desabilitados na seleção e consultas diretas retornam 503, sem orientação sobre seus kits. Os 171 disponíveis podem ser selecionados em pares distintos. A direção troca quais dicas são selecionadas; não são interações específicas comprovadas entre os dois kits.

## Proteção de dados

Na página: sem cadastro, cookies, analytics, conta Riot ou chamadas a IA. O banco guarda somente campeões e guias. Imagens são servidas localmente. A seleção aparece na URL e pode ficar no histórico do navegador; não inclua dados pessoais. O aplicativo não registra consultas nem configura logs de acesso. Erros de banco registram apenas a classe da exceção.

Validação no servidor, SQL parametrizado, escape de templates e CSP restritiva. Não há credenciais necessárias nesta etapa. `.env`, bancos e ambientes locais são ignorados pelo Git. Revise arquivos antes de publicar.

## Deploy e próximos passos

Ainda não existe URL pública da aplicação. Use uma hospedagem Python com HTTPS e disco persistente, em uma instância. Configure `HOST=0.0.0.0`, `PORT` conforme a plataforma e `DATABASE_PATH` no disco persistente. Instale `requirements.txt` e execute `python server.py`. Não use SQLite em disco efêmero. Configure backup e revise retenção de logs/IPs na hospedagem antes da abertura pública.

O lançamento deve ser totalmente gratuito. Cloudflare e Supabase foram sugeridos; a arquitetura final ainda precisa de adaptação e validação antes do deploy. A versão Flask/Waitress com SQLite local não será enviada sem adaptação. O foco é consulta rápida para quem já escolheu seu campeão, com dicas diretas e detalhes secundários recolhidos. O Supabase é opcional para dados dinâmicos futuros; o catálogo JSON atual não exige banco remoto. Preparação independente da plataforma:

- Instalação: `python -m pip install -r requirements.txt`.
- Inicialização: `python server.py`, com `HOST=0.0.0.0` e `PORT` definido pela plataforma.
- Persistência: `DATABASE_PATH` deve apontar para o arquivo SQLite em um volume persistente gravável. A base de campeões vem do Git e não precisa de escrita em produção. O SQLite é legado, mas ainda é inicializado e consultado pelo health check.
- Saúde: `/healthz` deve responder 200 e `{"status":"ok"}`.
- Backup: usar o comando `backup-db`, guardar cópia fora da instância e validar restauração; configurar periodicidade na hospedagem escolhida.
- Privacidade: conferir retenção de logs do provedor e evitar registrar query strings. Não configurar chaves de IA para a versão pública atual.
- Após publicar: validar HTTPS, página inicial, seleção de dois campeões, fases, habilidades, imagens locais, celular e respostas 400/404. Registrar URL pública neste README.

Verificação local: 74 testes pytest passaram. Recargas e remoções conferidas adicionalmente em Akshan/Aatrox, Yuumi/Singed e Yone/Ahri, 1440px/390px/320px e sem JavaScript. Playwright com Edge headless conferiu Yone/Ahri, Akshan/Aatrox, Yasuo/Zed e Yuumi/Singed em 1440px, 768px, 390px e 320px: duas seções, três fases, dez habilidades, imagens, busca/troca de campeão, preservação da lane, manutenção e fallback sem JavaScript. Sem overflow, cookies, chamadas externas, falhas de recursos ou erros JavaScript no fluxo verificado. Capturas desktop/celular de Akshan/Aatrox foram inspecionadas. Testes também cobrem rejeição de notas incompletas, independência da dupla/rota e preservação de notas na importação somente quando patch e descrição mecânica permanecem iguais. Isso não valida estratégia competitiva nem hospedagem pública.

Próximos passos: decidir hospedagem, publicar e verificar a versão determinística; revisar os perfis gerais com fontes e patch. IA analítica e builds permanecem futuras. Não há limite de IA implementado porque ainda não existe geração por IA na página.

## Créditos

Ilustrações da Riot Games obtidas do Data Dragon em 2026-10-11: `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{Champion}_0.jpg`, para os IDs listados em `lane_coach/data/roster.json`. Esses endereços não fixam patch e não são fonte das recomendações. Planos editoriais próprios; habilidades e dicas do catálogo são atribuídas à Riot.

Lane Coach isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties, are trademarks or registered trademarks of Riot Games, Inc.

## Base e avaliação da IA

Cada campeão contém `facts` (descrições oficiais de habilidades), `tips` (dicas editoriais com IDs de evidência), `source` (URL, patch dos dados e data de acesso) e `profile`: `identity`, `strengths`, `weaknesses`, `phases` e estado de revisão. Em cada fase (`lane`, `mid`, `late`), `typical` descreve o comportamento habitual, `plan` orienta quem joga com o campeão e `against` orienta quem o enfrenta. Campos opcionais `resource` e `caution` refinam o Plano direto; sem eles, recurso usa `typical`, ação usa `plan`/`against` e cuidado usa vulnerabilidades na lane ou riscos de mapa nas fases posteriores. Cada fato pode conter `coaching` com `use` e `limit`; notas incompletas são rejeitadas. O importador preserva essas notas apenas no mesmo patch e com descrição inalterada; após mudança, as notas deixam de aparecer até nova revisão. A base rejeita perfis sem fases ou campos obrigatórios e revisão sem data. Adicionar um campeão exige conteúdo completo e ilustração local; não basta acrescentar um nome ao seletor. A fonte da habilidade não comprova a estratégia nem interações especiais. O patch 16.20.1 identifica o snapshot dos dados, não uma revisão competitiva das dicas. O contexto não contém nível, vida ou cooldown atual: orientações devem ser condicionais. Os perfis são gerais e não indicam a melhor rota de cada campeão. O parâmetro `lane=general` é usado pela tela; `lane=mid` é mantido por compatibilidade.

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

Para baixar apenas os ícones de Passiva/Q/W/E/R do patch local, sem alterar os textos ou perfis:

```powershell
.\.venv\Scripts\python.exe scripts/import_ability_icons.py --patch 16.20.1
```

São usadas as propriedades `passive.image.full` e `spells[].image.full` do JSON oficial. Os PNGs ficam em `lane_coach/static/abilities/{patch}/{Champion}/{key}.png`; `sources.json` na pasta do patch registra a URL oficial de cada ícone. A consulta serve as imagens localmente. O script só copia o conjunto para a aplicação após concluir todos os downloads, com até três tentativas para falhas transitórias de rede; erros HTTP de cliente, incluindo limite de requisições, interrompem a importação.

Para atualizar também o conteúdo do catálogo:

```powershell
.\.venv\Scripts\python.exe scripts/import_roster.py --patch 16.20.1
```

Execute a importação com o servidor parado e revise o diff antes de publicar. Ela baixa o catálogo, dados, ícones oficiais das habilidades e imagens ausentes com concorrência limitada; valida a base completa em uma pasta temporária antes de copiar os arquivos. Preserva perfis específicos e dicas editoriais existentes. Não chama IA nem exige uma chave Riot. O patch é explícito; arquivos JSON em cache opcionais devem corresponder à versão solicitada.

`lane_coach/data/roster.json` registra a lista e as fontes do snapshot. `profile_templates.json` contém os planos editoriais por classe usados para perfis iniciais; eles não são análises individualizadas. As dicas oficiais `allytips` e `enemytips` podem estar ausentes ou conter orientações antigas, inclusive após reworks. São identificadas como dicas do catálogo, sem declaração de revisão competitiva. O importador não fabrica dicas oficiais quando elas estão vazias.

O snapshot não se atualiza sozinho: novos campeões ou patches exigem nova importação e revisão. A seleção inteira funciona sem rede externa durante o uso, sem chave de IA e sem gerar todas as combinações. Os testes verificam correspondência com o manifesto, habilidades, imagens, preservação dos quatro perfis e uma consulta por campeão.

Fontes: [Data Dragon — documentação oficial](https://developer.riotgames.com/docs/lol#data-dragon), [catálogo pt_BR 16.20.1](https://ddragon.leagueoflegends.com/cdn/16.20.1/data/pt_BR/champion.json). Ilustrações do elenco usam a mesma origem oficial indicada nos créditos.

## Atualizar apenas recargas

Com o servidor parado, execute `python scripts/import_cooldowns.py`. O script consulta os snapshots oficiais indicados nas fontes locais e adiciona somente o campo `cooldown`, preservando perfis, dicas, descrições e notas. `--cache-dir` é opcional; mantenha esse cache fora do repositório. O importador completo também inclui recargas em futuras importações. Valores ausentes ou com formato inválido não viram um tempo estimado.
