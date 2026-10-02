const search = document.querySelector('#symptom-search');
if (search) {
  const options = [...document.querySelectorAll('.symptom-option')];
  search.addEventListener('input', () => {
    const term = search.value.toLowerCase().trim();
    options.forEach(option => { option.hidden = !option.textContent.toLowerCase().includes(term); });
    document.querySelector('#no-results').hidden = options.some(option => !option.hidden);
  });
  options.forEach(option => option.querySelector('input').addEventListener('change', () => {
    const count = options.filter(item => item.querySelector('input').checked).length;
    document.querySelector('#selection-count').textContent = `${count} selected`;
    options.forEach(item => { const input = item.querySelector('input'); input.disabled = count >= 15 && !input.checked; });
  }));
}
