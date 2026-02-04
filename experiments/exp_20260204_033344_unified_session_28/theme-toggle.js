/**
 * Theme Toggle Module
 * - Reads/writes theme preference to localStorage ('theme')
 * - Applies theme by setting data-theme attribute on <html>
 * - Defaults to dark if no preference and no system preference match
 * - Respects system preference via prefers-color-scheme media query
 */

(() => {
  const STORAGE_KEY = 'theme';
  const THEME_ATTR = 'data-theme';
  const VALID_THEMES = ['light', 'dark'];

  /**
   * Apply given theme to the document.
   * @param {string} theme - 'light' or 'dark'
   */
  function applyTheme(theme) {
    if (!VALID_THEMES.includes(theme)) return;
    document.documentElement.setAttribute(THEME_ATTR, theme);
    localStorage.setItem(STORAGE_KEY, theme);
  }

  /**
   * Detect system preference.
   * @returns {string} 'light' | 'dark'
   */
  function getSystemPreference() {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    if (window.matchMedia('(prefers-color-scheme: light)').matches) {
      return 'light';
    }
    // Fallback
    return 'dark';
  }

  /**
   * Initialize theme based on stored preference, system preference, or default.
   */
  function initTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (VALID_THEMES.includes(stored)) {
      applyTheme(stored);
      return;
    }

    // No stored preference; use system preference; default to dark if undetectable
    const system = getSystemPreference();
    applyTheme(system);
  }

  /**
   * Toggle between light and dark themes.
   */
  function toggleTheme() {
    const current = document.documentElement.getAttribute(THEME_ATTR) || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
  }

  // Expose toggle function globally for UI elements (e.g., button onclick)
  window.toggleTheme = toggleTheme;

  // Run initialization on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTheme);
  } else {
    initTheme();
  }
})();