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
const rosterSearch = document.querySelector('#roster-search');
if (rosterSearch) {
  const selects = [...document.querySelectorAll('.champion-selector select')];
  const options = selects.map((select) => [...select.options].map((option) => option.cloneNode(true)));
  const normalize = (value) => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const filter = () => {
    const term = normalize(rosterSearch.value);
    let matches = 0;
    selects.forEach((select, index) => {
      const selected = select.value;
      const visible = options[index].filter((option) => normalize(option.textContent).includes(term));
      if (index === 0) matches = visible.length;
      const retained = options[index].filter((option) => option.value === selected || visible.some((match) => match.value === option.value));
      select.replaceChildren(...retained.map((option) => option.cloneNode(true)));
      select.value = selected;
    });
    document.querySelector('#search-status').textContent = `${matches} campeões encontrados. As escolhas atuais permanecem disponíveis.`;
  };
  rosterSearch.addEventListener('input', filter);
  window.addEventListener('pageshow', filter);
}
if (form) {
  const button = form.querySelector('button');
  form.addEventListener('submit', () => { button.disabled = true; button.textContent = 'Buscando perfis…'; });
  window.addEventListener('pageshow', () => { button.disabled = false; button.textContent = 'Ver perfis dos campeões ↗'; });
}
