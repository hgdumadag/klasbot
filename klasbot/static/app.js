const form = document.getElementById('generate-form');
const output = document.getElementById('output');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  output.textContent = '';

  const prompt = document.getElementById('prompt').value.trim();
  const url = `/generate?prompt=${encodeURIComponent(prompt)}`;
  const source = new EventSource(url);

  source.onmessage = (event) => {
    output.textContent += event.data;
  };

  source.addEventListener('done', () => {
    source.close();
  });

  source.onerror = () => {
    output.textContent += '\n\n[Stream closed]';
    source.close();
  };
});
