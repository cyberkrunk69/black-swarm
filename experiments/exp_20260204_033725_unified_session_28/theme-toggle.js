/**
 * Theme Toggle Module
 * - Handles dark/light theme switching
 * - Persists user preference in localStorage ('theme')
 * - Defaults to dark theme
 * - Respects system preference via prefers-color-scheme when no preference stored
 */

(function () {
  const STORAGE_KEY = 'theme';
  const DARK_CLASS = 'dark-theme';
  const LIGHT_CLASS = 'light-theme';

  // Determine initial theme
  function getStoredTheme() {
    return localStorage.getItem(STORAGE_KEY);
  }

  function getSystemPreference() {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function applyTheme(theme) {
    const root = document.documentElement;
    root.classList.remove(DARK_CLASS, LIGHT_CLASS);
    if (theme === 'light') {
      root.classList.add(LIGHT_CLASS);
    } else {
      root.classList.add(DARK_CLASS);
    }
  }

  function initTheme() {
    const stored = getStoredTheme();
    const theme = stored || getSystemPreference() || 'dark';
    applyTheme(theme);
  }

  // Toggle between light and dark
  function toggleTheme() {
    const current = document.documentElement.classList.contains(LIGHT_CLASS) ? 'light' : 'dark';
    const next = current === 'light' ? 'dark' : 'light';
    applyTheme(next);
    localStorage.setItem(STORAGE_KEY, next);
  }

  // Expose toggle function globally (optional)
  window.toggleTheme = toggleTheme;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();