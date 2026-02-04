/**
 * Theme Toggle Module
 * - Reads/writes user preference to localStorage ("theme": "dark" | "light")
 * - Applies the theme by setting data-theme attribute on <html>
 * - Respects system preference via CSS media query when no explicit preference exists
 */

(function () {
  const THEME_KEY = 'theme';
  const DARK = 'dark';
  const LIGHT = 'light';
  const root = document.documentElement;

  // Apply a given theme
  function applyTheme(theme) {
    if (theme === DARK) {
      root.setAttribute('data-theme', DARK);
    } else if (theme === LIGHT) {
      root.setAttribute('data-theme', LIGHT);
    } else {
      // Remove attribute to let CSS media query decide
      root.removeAttribute('data-theme');
    }
  }

  // Load stored preference or fall back to system/default
  function initTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === DARK || stored === LIGHT) {
      applyTheme(stored);
    } else {
      // No stored pref – let CSS handle prefers-color-scheme (default dark)
      applyTheme(null);
    }
  }

  // Toggle between dark and light, store new pref
  function toggleTheme() {
    const current = root.getAttribute('data-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? DARK : LIGHT);
    const newTheme = current === DARK ? LIGHT : DARK;
    applyTheme(newTheme);
    localStorage.setItem(THEME_KEY, newTheme);
  }

  // Expose toggle function for UI
  window.toggleTheme = toggleTheme;

  // Initialise on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();