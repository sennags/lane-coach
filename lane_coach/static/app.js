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
if (form) {
  const button = form.querySelector('button');
  form.addEventListener('submit', () => { button.disabled = true; button.textContent = 'Buscando guia…'; });
  window.addEventListener('pageshow', () => { button.disabled = false; button.textContent = 'Ver guia do confronto ↗'; });
}
