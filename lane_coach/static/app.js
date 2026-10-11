document.querySelectorAll('.champion-selector select').forEach((select) => {
  select.addEventListener('change', () => {
    const selected = select.selectedOptions[0];
    const card = select.closest('.champion-card');
    card.querySelector('.champion-art').src = selected.dataset.image;
    card.querySelector('.champion-name').textContent = selected.textContent;
    card.querySelector('.champion-title').textContent = selected.dataset.title;
  });
});
const form = document.querySelector('#matchup-form');
const normalize = (value) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
document.querySelectorAll('.champion-selector').forEach((selector) => {
  const search = selector.querySelector('input[type="search"]');
  const select = selector.querySelector('select');
  const status = selector.querySelector('[role="status"]');
  const options = [...select.options].map((option) => option.cloneNode(true));
  const filter = () => {
    const term = normalize(search.value);
    const selected = select.value;
    const matches = options.filter((option) => normalize(option.textContent).includes(term));
    const visible = options.filter((option) => option.value === selected || matches.some((match) => match.value === option.value));
    select.replaceChildren(...visible.map((option) => option.cloneNode(true)));
    select.value = selected;
    status.textContent = `${matches.length} campeões encontrados. Sua escolha atual permanece disponível.`;
  };
  search.addEventListener('input', filter);
  window.addEventListener('pageshow', filter);
});
if (form) {
  const button = form.querySelector('button');
  form.addEventListener('submit', () => { button.disabled = true; button.textContent = 'Buscando perfis…'; });
  window.addEventListener('pageshow', () => { button.disabled = false; button.textContent = 'Ver perfis dos campeões ↗'; });
}
