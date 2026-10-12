# Lane Coach

Catálogo completo: 173 campeões do Data Dragon 16.20.1, com habilidades, imagens locais, perfis e seleção pesquisável dos dois campeões. A consulta combina dois arquivos em memória, sem cadastrar guias por confronto. Flask + HTML/CSS; SQLite legado preservado.

**Estado:** versão local 0.10, com consulta de estatísticas por campeão/adversário/rota. Role, classe e dano continuam independentes; o rótulo editorial Agressivo/Passivo saiu da tela e foi substituído pela tendência estatística do confronto quando há amostra suficiente. Sem dados, não se inventa uma tendência. HABILIDADES mantém ícone, tecla, nome e recarga, com espaço para uma evolução futura; USO/LIMITE saíram da interface e continuam nos JSON. Planos antigos permanecem na base/CLI. Visual Seleção competitiva preservado.

Os 171 campeões disponíveis têm perfis e notas editoriais preservados na base. Aphelios e Hwei permanecem em manutenção. Role, classe, dano e orientações de jungle continuam sem revisão especializada; fontes do kit não comprovam estratégia. Descrições oficiais permanecem na base, sem aparecer na interface. Consulta sem IA, cadastro ou histórico de visitantes; Groq continua somente CLI. Sem deploy público.

Os 173 registros têm `classification`, incluindo os dois em manutenção. Posição é uma referência editorial, sem afirmar popularidade. Tendência agressiva/passiva e sua condição continuam na base como conteúdo antigo, sem alimentar o rótulo visível. Para os 40 campeões com referência Jungle, invasão/gank/risco editorial permanecem. Classe usa Controller/Fighter/Mage/Marksman/Slayer/Tank/Specialist; tags oficiais intactos. Dano predominante não é AD/AP nem medição percentual; builds e dano verdadeiro podem alterar a composição do dano.

Classificações registram patch de conteúdo, data de autoria, fontes do kit e `editorial_unreviewed`; essas fontes não comprovam popularidade de posição ou vantagem no confronto. Atualizar o catálogo preserva a classificação e seu patch original, exigindo revisão editorial separada. Novos registros sem classificação completa são rejeitados pelo carregamento; não recebem valores automáticos por classe.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Abra http://127.0.0.1:5000. O Waitress escuta apenas neste computador por padrão. Ctrl+C encerra. Não é necessário ativar a venv.

A página inicial mostra Yone/Ahri. Ao selecionar uma lane, a página e `GET /api/statistics?champion=Yone&opponent=Ahri&lane=mid` consultam os resumos salvos e podem iniciar uma coleta limitada em segundo plano. Busca/troca preservam o outro campeão e a lane; o servidor valida a seleção e mantém a consulta útil durante falhas. Sem JavaScript, resultados já salvos são renderizados no servidor; uma coleta nova fica disponível após recarregar. Composições permanece futura.

HABILIDADES continua como título único preto/centralizado, com dez ícones locais, nomes, teclas e recargas. USO/LIMITE e descrições ficam somente na base. Avisos/links/fontes removidos não foram restaurados. Passivas sem valor e valores zero do catálogo são identificados; recargas não acompanham a partida. O espaço reservado nas habilidades não contém dados provisórios.

Os JSON são carregados no início; reinicie após alterá-los. SQLite legado guarda guias antigos e continua necessário à inicialização/healthz. Estatísticas usam um banco separado `instance/match-statistics.sqlite3`, sem modificar os dados legados. Não há histórico de consultas de visitantes nem geração de IA na página.

## Estatísticas: recorte e interpretação

Recorte inicial: BR1, ranked solo/duo (fila 420), Summoner's Rift, patch local 16.20 e eventos até 15 minutos, sem filtro de elo. Apenas partidas completas com duração mínima de 15 minutos; remakes e encerramento precoce são excluídos. Posição vem de `teamPosition`; uma posição ausente/inválida não entra na comparação.

As porcentagens contam **partidas** com pelo menos um abate ou morte diretamente entre adversários da mesma posição, em qualquer região do mapa, até 900.000 ms inclusive. Vários abates na mesma partida contam uma vez; matar e morrer podem ocorrer juntos, portanto as porcentagens não precisam somar 100. Abate sem assistência não é prova de duelo puro. Abates de outros adversários e mortes para torres não entram nessas métricas.

Amostra mínima operacional: 30 partidas únicas por dupla/posição. “Abates mais frequentes”, “Mortes mais frequentes” ou “Sem tendência clara” usam um intervalo de Wilson de 95% sobre partidas discordantes (matou sem morrer versus morreu sem matar). Não classifica agressividade, causalidade, vencedor ou recomendação de troca. Esse método e a amostra precisam de avaliação com partidas reais antes de conclusões competitivas.

Itens: até três itens mais frequentes no inventário final, disponíveis no catálogo do patch e com custo total de pelo menos 2.000 de ouro. Cada item exige presença em ao menos cinco partidas da amostra; exibe frequência, vitória e contagem. Não calcula sequência de compra, venda/undo, item core ideal ou efeito causal de um item; itens transformados não elegíveis no catálogo podem ficar fora. Não há runas ou importação de sites de builds.

A coleta alterna tiers da ladder pública do BR: IRON a DIAMOND na divisão IV/páginas 1–3, e MASTER/GRANDMASTER/CHALLENGER. Escolhe um jogador transitório por lote e examina até oito partidas de seus 20 jogos recentes. A amostra é de conveniência, **não representativa de todos os elos**; a posição atual na ladder não comprova o elo histórico da partida. Não existe busca direta por dupla na Match-V5: confrontos raros podem demorar a formar amostra.

## Configurar Riot e coletar

A chave fica somente no processo do servidor. Não cole a chave no chat, no Git ou no navegador. O aplicativo não lê `.env` automaticamente. No PowerShell, dentro da pasta do projeto, execute:

```powershell
.\.venv\Scripts\python.exe scripts/start_with_riot.py
```

Quando aparecer `Chave Riot:`, cole a chave e pressione Enter. A entrada fica oculta. O comando verifica `/healthz` e mostra `Servidor pronto: http://127.0.0.1:5005/`; abra esse endereço, mantenha o PowerShell aberto e selecione uma lane. Ctrl+C encerra. Ao iniciar novamente, será necessário fornecer a chave de novo, salvo se `RIOT_API_KEY` já estiver no ambiente. O comando também funciona a partir de outra pasta quando os caminhos do Python e do script são absolutos.

O aviso `waitress.queue: Task queue depth is 1` indica tarefas aguardando atendimento; sozinho não comprova erro da Riot. O inicializador grava avisos/erros em `instance/server-error.log` (até 512 KB e uma cópia anterior) para evitar que a escrita no terminal bloqueie a fila do servidor. Não há log de acesso. Se a porta estiver ocupada, pare a instância anterior com Ctrl+C ou use `--port 5006`; o comando não encerra outros processos.

Sem chave, fichas/habilidades continuam úteis; resultados já persistidos ainda podem ser consultados. Para coleta manual num terminal com RIOT_API_KEY configurada: `.\.venv\Scripts\python.exe -m flask --app lane_coach collect-stats`. Cada lote é limitado; outra tentativa durante intervalo/cota não inicia coleta. A página consulta/atualiza resultados em segundo plano, sem rebaixar uma amostra salva a zero quando o provedor falha.

Limites locais persistidos e atômicos: até 18 chamadas/segundo e 90/120 segundos; uma coleta global por vez, intervalo mínimo de 60 segundos, até oito partidas por lote. Timeout de seis segundos por chamada; sem redirecionamento de credenciais ou retry automático. HTTP 429 respeita Retry-After; 401/403 pausa por uma hora. Chaves compartilhadas com outras ferramentas também podem atingir a cota do provedor.

Resumos anônimos persistidos: hash de partida para deduplicação, patch, datas, pares/posição, indicadores de abate/morte/assistência, vitória e IDs dos itens finais. Nenhum nome, PUUID, Riot ID, payload bruto ou posição dos eventos é salvo. Retenção máxima: 30 dias desde coleta e 5.000 partidas; dados antigos deixam a amostra. Cache de amostra suficiente permanece fresco por até seis horas; dados anteriores são preservados enquanto atualiza. A validade não muda o patch ou revisa conteúdo.

`STATISTICS_DATABASE` pode ser definido no ambiente ou configuração Flask para um caminho persistente alternativo. Backup: `.\.venv\Scripts\python.exe -m flask --app lane_coach backup-db --statistics instance/stats-backup.sqlite3`. Para restaurar, pare a aplicação e substitua o banco de estatísticas por uma cópia do backup; nunca publique bancos/backups. Não compartilhar o banco entre hosts independentes sem reavaliar os limites.

Após atualizar e revisar o elenco, execute `python scripts/import_statistics_catalog.py --patch 16.20.1` com a versão local correta. O script importa apenas IDs e rótulos oficiais de itens; não altera classificações/habilidades. O patch da base estatística deve acompanhar o catálogo local.

A documentação foi conferida; **não houve teste autenticado com Riot nesta entrega**, pois não havia chave configurada. Os testes usam respostas simuladas e identificadas. Não publicar a coleta com chave de desenvolvimento/pessoal: conferir acesso e chave de produção antes de abrir ao público. [Match-V5](https://developer.riotgames.com/apis#match-v5/GET_getTimeline), [League-V4](https://developer.riotgames.com/apis#league-v4), [chaves e limites](https://developer.riotgames.com/docs/portal).

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
- `lane_coach/classification.py`: categorias permitidas e validação de contexto/proveniência.
- `lane_coach/riot.py` e `statistics.py`: cliente Riot, limites, coleta e agregação anônima.
- `lane_coach/data/statistics_catalog.json`: IDs oficiais de campeões e rótulos de itens do patch local.
- `lane_coach/generation.py`: avaliação Groq somente por CLI.
- `lane_coach/data/guides.json`: conteúdo legado preservado da versão 0.1.
- `lane_coach/templates/` e `static/`: interface e imagens locais.
- `tests/`: consultas, validação, privacidade, persistência, backup e falha do banco.

`GET /` mostra os perfis iniciais. `GET /matchup?champion=Yone&opponent=Ahri&lane=general` retorna os perfis selecionados; `lane=mid` é aceito por compatibilidade. Entradas inválidas, repetidas ou com parâmetros extras: 400; rota inexistente: 404; falha de banco: 503. `GET /healthz` verifica o SQLite legado. O catálogo mantém os 173 campeões. Aphelios e Hwei estão em manutenção: aparecem identificados e desabilitados na seleção e consultas diretas retornam 503, sem orientação sobre seus kits. Os 171 disponíveis podem ser selecionados em pares distintos. As fichas acompanham o campeão de cada lado e permanecem independentes da dupla; não são interações específicas comprovadas entre os kits.

## Proteção de dados

Na página: sem cadastro, cookies, analytics, conta Riot de visitante ou chamadas a IA. Coleta Riot acontece somente no backend; dados de jogadores são transitórios. O banco guarda somente campeões e guias. Imagens são servidas localmente. A seleção aparece na URL e pode ficar no histórico do navegador; não inclua dados pessoais. O aplicativo não registra consultas nem configura logs de acesso. Erros de banco registram apenas a classe da exceção.

Validação no servidor, SQL parametrizado, escape de templates e CSP restritiva. A consulta de fichas/habilidades funciona sem credenciais; a coleta requer chave Riot somente no servidor. `.env`, bancos e ambientes locais são ignorados pelo Git. Revise arquivos antes de publicar.

## Deploy e próximos passos

Ainda não existe URL pública da aplicação. Use uma hospedagem Python com HTTPS e disco persistente, em uma instância. Configure `HOST=0.0.0.0`, `PORT` conforme a plataforma e `DATABASE_PATH` no disco persistente. Instale `requirements.txt` e execute `python server.py`. Não use SQLite em disco efêmero. Configure backup e revise retenção de logs/IPs na hospedagem antes da abertura pública.

O lançamento deve ser totalmente gratuito. Cloudflare e Supabase foram sugeridos; a arquitetura final ainda precisa de adaptação e validação antes do deploy. A versão Flask/Waitress com SQLite local não será enviada sem adaptação. O foco é consulta rápida para quem já escolheu seu campeão, com dicas diretas e detalhes secundários recolhidos. O Supabase é opcional para dados dinâmicos futuros; o catálogo JSON atual não exige banco remoto. Preparação independente da plataforma:

- Instalação: `python -m pip install -r requirements.txt`.
- Inicialização: `python server.py`, com `HOST=0.0.0.0` e `PORT` definido pela plataforma.
- Persistência: `DATABASE_PATH` deve apontar para o arquivo SQLite em um volume persistente gravável. A base de campeões vem do Git e não precisa de escrita em produção. O SQLite é legado, mas ainda é inicializado e consultado pelo health check.
- Saúde: `/healthz` deve responder 200 e `{"status":"ok"}`.
- Backup: usar o comando `backup-db`, guardar cópia fora da instância e validar restauração; configurar periodicidade na hospedagem escolhida.
- Privacidade: conferir retenção de logs do provedor e evitar registrar query strings. Não configurar chaves de IA para a versão pública atual.
- Após publicar: validar HTTPS, página inicial, seleção de dois campeões, categorias, habilidades, imagens locais, celular e respostas 400/404. Registrar URL pública neste README.

Verificação local da versão 0.10: 113 testes pytest passaram, incluindo deduplicação, denominadores e duas perspectivas, recortes, timeline inválida, amostra mínima, itens, privacidade, quotas concorrentes, lease persistente, backup/reinício e falha do provedor preservando dados. Casos de Riot são simulados; não equivalem a teste do provedor ou validação competitiva.

Próximos passos: configurar chave Riot local e validar coleta com partidas reais, avaliar amostra e método, depois decidir hospedagem e verificar a URL pública. Sequência de builds, runas e IA analítica continuam futuras. Nenhuma geração de IA na página.

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

## Recargas repetidas e condições

Quando todos os níveis têm o mesmo tempo base, a interface mostra um único número. Tempos que variam continuam em ordem por nível da habilidade. Notas só são importadas quando a descrição oficial relaciona explicitamente a recarga à condição: Yone W com Velocidade de Ataque, Veigar W com acúmulos da passiva. Escalamento de dano ou velocidade concedida não é tratado como escalamento de recarga. Fórmulas e limites numéricos ausentes na descrição não são estimados; ausência de nota não prova que a mecânica não tenha outros ajustes.

Os novos perfis registram `content_patch` e `authored_at`, mantendo `editorial_unreviewed` e revisão sem data. A estratégia é interpretação editorial do kit, não uma conclusão estatística. Em nova importação, revisar a estratégia preservada por campeão: atualizar a fonte não revisa automaticamente as orientações.

### Recargas ligadas à velocidade de ataque

O snapshot curto do Data Dragon omite algumas relações. `lane_coach/data/cooldown_rules.json` complementa cinco habilidades com fontes específicas: Yone Q e Yasuo Q (4 s base, mínimo 1,33 s por Velocidade de Ataque adicional), Yone W (14 s base, mínimo 6 s), Zeri Q (intervalo por Velocidade de Ataque total, limite normal de 1,5 disparos/s com exceção da ultimate) e Bel'Veth Q (intervalo entre usos separado da recarga por direção, que reduz por Velocidade de Ataque).

As regras só são aplicadas ao patch 16.20.1 e aos arrays base esperados. Novo patch ou base diferente descarta a anotação específica até revisão. Links da LoL Wiki e linhas de fonte/patch/consulta ao final das habilidades foram removidos da interface; sua proveniência continua na base. Isso não converte a LoL Wiki em fonte oficial Riot. A revisão usou informações públicas e o snapshot local, sem teste no cliente do jogo. Bel'Veth usa também as notas oficiais 26.15: a conversão foi alterada de 0,25 para 0,2 e o intervalo entre usos mudou; não usar o valor antigo de páginas históricas. Os arrays oficiais de recarga são preservados. Reduções por acertar ataques são uma categoria diferente de recarga que escala diretamente com o atributo.
