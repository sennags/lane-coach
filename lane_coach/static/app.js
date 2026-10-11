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
      button.append(image, label); button.disabled = option.value === other.value;
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
  search.addEventListener('input', results);
  document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('keydown', event => { if (event.key === 'Escape') { event.preventDefault(); dialog.close(); } });
  dialog.addEventListener('close', () => opener?.focus());
  form.addEventListener('submit', () => {
    form.querySelectorAll('[data-pick]').forEach(button => { button.disabled = true; });
    document.querySelector('#selection-status').textContent = 'Carregando perfis…';
  });
  window.addEventListener('pageshow', () => { form.querySelectorAll('[data-pick]').forEach(button => { button.disabled = false; }); });
  document.documentElement.classList.add('js');
}
const phaseButtons = [...document.querySelectorAll('[data-phase-button]')];
const showPhase = phase => {
  document.querySelectorAll('.phase-panel[data-phase]').forEach(panel => { panel.hidden = panel.dataset.phase !== phase; });
  phaseButtons.forEach(button => { const active = button.dataset.phaseButton === phase; button.classList.toggle('active', active); button.setAttribute('aria-pressed', active); });
};
if (document.documentElement.classList.contains('js') && phaseButtons.length) {
  phaseButtons.forEach(button => button.addEventListener('click', () => showPhase(button.dataset.phaseButton)));
  showPhase('lane');
}
