const form = document.querySelector('#matchup-form');
const dialog = document.querySelector('#champion-dialog');
const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
if (form && dialog && typeof dialog.showModal === 'function') {
  const selects = [...form.querySelectorAll('#champion, #opponent')];
  const search = document.querySelector('#champion-search');
  const list = document.querySelector('#champion-results');
  const status = document.querySelector('#search-status');
  let editing;
  let opener;
  const results = () => {
    const term = normalize(search.value);
    const other = selects.find(select => select !== editing);
    const matches = [...editing.options].filter(option => normalize(option.textContent).includes(term));
    list.replaceChildren();
    for (const option of matches) {
      const button = document.createElement('button');
      button.type = 'button';
      const image = document.createElement('img'); image.src = option.dataset.image; image.alt = ''; image.loading = 'lazy';
      const label = document.createElement('span'); label.textContent = option.textContent;
      button.append(image, label); button.disabled = option.disabled || option.value === other.value;
      button.addEventListener('click', () => { editing.value = option.value; dialog.close(); form.requestSubmit(); });
      list.append(button);
    }
    status.textContent = matches.length ? `${matches.length} campeões encontrados.` : 'Nenhum campeão encontrado.';
  };
  form.querySelectorAll('[data-pick]').forEach(button => button.addEventListener('click', () => {
    editing = document.getElementById(button.dataset.pick); opener = button;
    document.querySelector('#dialog-title').textContent = editing.name === 'champion' ? 'Escolha seu campeão' : 'Escolha o adversário';
    search.value = ''; results(); dialog.showModal(); search.focus();
  }));
  document.querySelector('#lane').addEventListener('change', () => form.requestSubmit());
  form.querySelectorAll('[data-lane]').forEach(button => button.addEventListener('click', () => {
    const lane = document.querySelector('#lane');
    if (lane.value === button.dataset.lane) return;
    lane.value = button.dataset.lane;
    form.querySelectorAll('[data-lane]').forEach(option => option.setAttribute('aria-pressed', String(option === button)));
    form.requestSubmit();
  }));
  search.addEventListener('input', results);
  document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('keydown', event => { if (event.key === 'Escape') { event.preventDefault(); dialog.close(); } });
  dialog.addEventListener('close', () => opener?.focus());
  form.addEventListener('submit', () => {
    form.querySelectorAll('[data-pick], [data-lane]').forEach(button => { button.disabled = true; });
    document.querySelector('#selection-status').textContent = 'Carregando perfis…';
  });
  window.addEventListener('pageshow', () => {
    form.querySelectorAll('[data-pick], [data-lane]').forEach(button => { button.disabled = false; });
    // History can restore the form value after pageshow; align the bar with the URL.
    setTimeout(() => {
      const lane = document.querySelector('#lane');
      const value = new URLSearchParams(window.location.search).get('lane') || 'general';
      lane.value = [...lane.options].some(option => option.value === value) ? value : 'general';
      form.querySelectorAll('[data-lane]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.lane === lane.value)));
    }, 0);
  });
  document.documentElement.classList.add('js');
}
const statisticsPanel = document.querySelector('#matchup-statistics');
if (statisticsPanel && new URL(statisticsPanel.dataset.url, location.origin).searchParams.get('lane') !== 'general') {
  let statisticsAttempts = 0;
  const refreshStatistics = async () => {
    statisticsAttempts += 1;
    try {
      const response = await fetch(statisticsPanel.dataset.url, { headers: { Accept: 'application/json' } });
      if (!response.ok) throw new Error('Statistics unavailable');
      const result = await response.json();
      statisticsPanel.innerHTML = result.html;
      document.querySelectorAll('[data-stat-side]').forEach(label => {
        label.textContent = result.state === 'ready' ? result.sides[Number(label.dataset.statSide)].tendency : 'Aguardando dados';
      });
      if (result.state === 'loading' && statisticsAttempts < 20) setTimeout(refreshStatistics, 3000);
    } catch {
      const message = document.createElement('p');
      message.className = 'statistics-status';
      if (statisticsPanel.querySelector('.statistics-result')) {
        message.textContent = 'Não foi possível atualizar. Dados salvos preservados.';
      } else {
        statisticsPanel.replaceChildren();
        message.textContent = 'Estatísticas temporariamente indisponíveis.';
      }
      statisticsPanel.append(message);
    }
  };
  refreshStatistics();
}
