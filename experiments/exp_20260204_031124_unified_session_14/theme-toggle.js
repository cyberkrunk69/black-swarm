/**
 * Theme Toggle Utility
 *
 * - Reads stored preference from localStorage.
 * - Falls back to system preference via prefers-color-scheme.
 * - Default theme is dark.
 * - Exposes `toggleTheme()` for UI interaction.
 */

(function () {
  const THEME_KEY = 'theme-preference';
  const DARK = 'dark';
  const LIGHT = 'light';

  /**
   * Apply a theme to the document root.
   * @param {string} theme - 'dark' | 'light'
   */
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(THEME_KEY, theme);
  }

  /**
   * Determine the initial theme.
   * Order: localStorage > system preference > default (dark)
   */
  function getInitialTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === DARK || stored === LIGHT) {
      return stored;
    }
    const prefersLight = window.matchMedia('(prefers-color-scheme: light)').matches;
    return prefersLight ? LIGHT : DARK;
  }

  /**
   * Toggle between dark and light themes.
   */
  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || DARK;
    const next = current === DARK ? LIGHT : DARK;
    applyTheme(next);
  }

  // Initialize theme on page load
  document.addEventListener('DOMContentLoaded', () => {
    const initialTheme = getInitialTheme();
    document.documentElement.setAttribute('data-theme', initialTheme);
  });

  // Expose toggle function globally (e.g., attach to a button)
  window.toggleTheme = toggleTheme;
})();