/**
 * Theme Toggle Module
 * Handles dark/light theme switching, persisting preference in localStorage,
 * and respecting system color scheme when no explicit preference is set.
 */

(function () {
  const THEME_KEY = 'preferred-theme';
  const DARK = 'dark';
  const LIGHT = 'light';

  /**
   * Apply the given theme by setting a data attribute on <html>.
   * @param {string} theme - 'dark' or 'light'
   */
  function applyTheme(theme) {
    const root = document.documentElement;
    if (theme === LIGHT) {
      root.setAttribute('data-theme', LIGHT);
    } else {
      // Remove attribute for dark (default) to allow prefers-color-scheme fallback
      root.removeAttribute('data-theme');
    }
  }

  /**
   * Determine the initial theme:
   *   1. Check localStorage.
   *   2. If none, check system preference.
   *   3. Default to dark.
   */
  function getInitialTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === LIGHT || stored === DARK) {
      return stored;
    }

    const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    return prefersLight ? LIGHT : DARK;
  }

  /**
   * Toggle between dark and light themes, persisting the choice.
   */
  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') === LIGHT ? LIGHT : DARK;
    const next = current === LIGHT ? DARK : LIGHT;
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  }

  // Initialize theme on page load
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  // Expose toggle function globally for UI bindings
  window.toggleTheme = toggleTheme;

  // Optional: listen to system changes if no explicit preference is stored
  const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
  mediaQuery.addEventListener('change', (e) => {
    const stored = localStorage.getItem(THEME_KEY);
    if (!stored) {
      applyTheme(e.matches ? LIGHT : DARK);
    }
  });
})();