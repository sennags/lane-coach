# Lane Coach

Catálogo completo: 173 campeões do Data Dragon 16.20.1, com habilidades, imagens locais, perfis e seleção pesquisável dos dois campeões. A consulta combina dois arquivos em memória, sem cadastrar guias por confronto. Flask + HTML/CSS; SQLite legado preservado.

**Estado:** versão local 0.9, com categorias independentes por campeão no visual Seleção competitiva. A ficha substitui os planos e abas de fases: role principal, tendência agressiva/passiva, classe funcional e dano predominante (Físico/Mágico/Misto). HABILIDADES permanece abaixo. Os planos antigos continuam nos JSON e no contexto CLI, sem aparecer na tela.

Os 171 campeões disponíveis têm perfis editoriais individuais e notas de uso/limite em P/Q/W/E/R. Os seis perfis anteriores foram preservados; os outros 165 receberam notas baseadas no snapshot mecânico oficial, com papéis condicionais por campeão em combate. Aphelios e Hwei permanecem em manutenção e não são apresentados como prontos. Toda orientação estratégica continua sem revisão especializada; “perfil individual” não significa confronto validado, estatística ou adaptação por rota. Descrições oficiais permanecem na base, sem aparecer na interface. Consulta sem IA, cadastro ou histórico de visitantes; experimento Groq continua somente CLI. Sem deploy público.

Os 173 registros têm `classification`, incluindo os dois em manutenção. A posição é uma referência editorial, sem afirmar frequência estatística no patch. A tendência indica uma leitura inicial do kit, não uma regra para todas as partidas; a condição que a sustenta fica na base. Para os 40 campeões cuja posição de referência é Jungle, a ficha mostra possibilidade de invasão, preparação de gank e risco de sofrer invasão, sem inventar minutos ou garantir duelos. Classe usa Controller/Fighter/Mage/Marksman/Slayer/Tank/Specialist como taxonomia editorial; os tags oficiais permanecem intactos. Dano predominante não é AD/AP, não é medição percentual e não classifica como misto qualquer mago que também dê ataques básicos. Builds e dano verdadeiro podem alterar a composição do dano.

Classificações registram patch de conteúdo, data de autoria, fontes do kit e `editorial_unreviewed`; essas fontes não comprovam popularidade de posição ou vantagem no confronto. Atualizar o catálogo preserva a classificação e seu patch original, exigindo revisão editorial separada. Novos registros sem classificação completa são rejeitados pelo carregamento; não recebem valores automáticos por classe.

## Executar no Windows

Requer Python 3.10 ou superior (testado com 3.14).

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe server.py
```

Abra http://127.0.0.1:5000. O Waitress escuta apenas neste computador por padrão. Ctrl+C encerra. Não é necessário ativar a venv.

A página inicial mostra Yone e Ahri. Cada lado apresenta quatro categorias e, abaixo, Passiva/Q/W/E/R sempre visíveis, com ícone oficial local, tecla, nome, recarga base e notas de uso/limite. HABILIDADES continua como título único preto e centralizado. Passivas sem número e valores zero do catálogo são identificados; recargas não acompanham a partida. O aviso geral sobre recargas, descrições oficiais e linhas de fonte/patch/data ao final das habilidades continuam removidos; fontes e revisão permanecem na base.

**Trocar campeão** abre busca nos dois lados; a seleção preserva o outro campeão e a lane e impede campeões iguais. A barra de Top/Jungle/Mid/ADC/Support fica abaixo de VS, com seleção vermelha. A lane selecionada registra contexto, sem recalcular categorias. As categorias funcionam também sem JavaScript, com seletores nativos e botão de consulta. Composições permanece futura.

O visual preserva navegação lateral, vermelho, retratos inclinados e adversário à direita. Não há abas de fases, planos por fase ou subtítulos oficiais sob os nomes.

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
- `lane_coach/classification.py`: categorias permitidas e validação de contexto/proveniência.
- `lane_coach/generation.py`: avaliação Groq somente por CLI.
- `lane_coach/data/guides.json`: conteúdo legado preservado da versão 0.1.
- `lane_coach/templates/` e `static/`: interface e imagens locais.
- `tests/`: consultas, validação, privacidade, persistência, backup e falha do banco.

`GET /` mostra os perfis iniciais. `GET /matchup?champion=Yone&opponent=Ahri&lane=general` retorna os perfis selecionados; `lane=mid` é aceito por compatibilidade. Entradas inválidas, repetidas ou com parâmetros extras: 400; rota inexistente: 404; falha de banco: 503. `GET /healthz` verifica o SQLite legado. O catálogo mantém os 173 campeões. Aphelios e Hwei estão em manutenção: aparecem identificados e desabilitados na seleção e consultas diretas retornam 503, sem orientação sobre seus kits. Os 171 disponíveis podem ser selecionados em pares distintos. As fichas acompanham o campeão de cada lado e permanecem independentes da dupla; não são interações específicas comprovadas entre os kits.

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
- Após publicar: validar HTTPS, página inicial, seleção de dois campeões, categorias, habilidades, imagens locais, celular e respostas 400/404. Registrar URL pública neste README.

Verificação local da ficha: 89 testes pytest passaram; após o ajuste editorial de Naafiri para referência Jungle, 15 testes de categorias/catálogo passaram. A suíte verifica validação, proveniência, isolamento entre consultas, manutenção, escape HTML, seleção, privacidade, persistência e preservação de classificações na importação sem atribuir uma revisão ao patch novo. Comparação com Git dos 173 registros confirmou que somente `classification` foi acrescentado: habilidades, recargas, tags, fontes, perfis e dicas anteriores preservados. Playwright/Edge headless verificou Yone/Ahri, Lee Sin/Evelynn, Ashe/Sona e Poppy/Naafiri em 1440px/390px/320px: duas fichas, quatro categorias por lado, habilidades, busca/troca, lane preservada, manutenção e fallback sem JavaScript. Sem overflow, cookies, chamadas externas, falhas de recursos ou erros JavaScript no fluxo verificado. Capturas das fichas em desktop/celular inspecionadas. Esses testes não validam as classificações editoriais, a estratégia competitiva ou hospedagem pública.

Próximos passos: decidir hospedagem, publicar e verificar a versão determinística; revisar categorias e notas por campeão com fontes e patch. IA analítica e builds permanecem futuras. Não há limite de IA implementado porque ainda não existe geração por IA na página.

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
