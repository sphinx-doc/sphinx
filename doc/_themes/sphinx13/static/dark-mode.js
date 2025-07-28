document.addEventListener('DOMContentLoaded', () => {
  const toggleBtn = document.getElementById('toggle-theme');
  const htmlTag = document.documentElement;

  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    htmlTag.classList.add('dark-mode');
    toggleBtn.textContent = '☀️ Light Mode';
  }

  toggleBtn?.addEventListener('click', () => {
    const isDark = htmlTag.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    toggleBtn.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
  });
});
