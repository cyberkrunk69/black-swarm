/**
 * Theme toggle utility
 * - Reads/writes user preference from localStorage ('theme')
 * - Applies CSS class to <html> element (dark-theme / light-theme)
 * - Defaults to dark theme, but respects system preference via CSS media queries
 */

(function () {
  const STORAGE_KEY = 'theme';
  const ROOT = document.documentElement;
  const LIGHT_CLASS = 'light-theme';
  const DARK_CLASS = 'dark-theme';

  function applyTheme(theme) {
    ROOT.classList.remove(LIGHT_CLASS, DARK_CLASS);
    if (theme === 'light') {
      ROOT.classList.add(LIGHT_CLASS);
    } else {
      ROOT.classList.add(DARK_CLASS);
    }
  }

  function getStoredTheme() {
    return localStorage.getItem(STORAGE_KEY);
  }

  function setStoredTheme(theme) {
    localStorage.setItem(STORAGE_KEY, theme);
  }

  function initTheme() {
    const stored = getStoredTheme();
    if (stored) {
      applyTheme(stored);
    } else {
      // No explicit preference – default to dark (CSS media query will adjust UI)
      applyTheme('dark');
    }
  }

  function toggleTheme() {
    const isDark = ROOT.classList.contains(DARK_CLASS);
    const newTheme = isDark ? 'light' : 'dark';
    applyTheme(newTheme);
    setStoredTheme(newTheme);
  }

  // Expose a global helper (optional)
  window.toggleTheme = toggleTheme;

  // Auto‑initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }

  // If a button with id="theme-toggle" exists, wire it up automatically
  document.addEventListener('DOMContentLoaded', function () {
    const btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', toggleTheme);
    }
  });
})();