/**
 * Theme toggle utility.
 * - Stores the user's preference in localStorage under the key 'theme'.
 * - Applies the theme by setting a `data-theme` attribute on the <html> element.
 * - Respects system preference via `prefers-color-scheme` when no explicit preference is stored.
 * - Defaults to dark theme.
 */

const THEME_KEY = 'theme';
const DARK = 'dark';
const LIGHT = 'light';

/**
 * Apply the given theme.
 * @param {string} theme - Either 'dark' or 'light'.
 */
function applyTheme(theme) {
    const root = document.documentElement;
    if (theme === LIGHT) {
        root.setAttribute('data-theme', LIGHT);
    } else {
        // Ensure dark theme when theme === DARK or any unexpected value
        root.setAttribute('data-theme', DARK);
    }
}

/**
 * Determine the initial theme based on localStorage or system preference.
 * @returns {string} - 'dark' or 'light'.
 */
function getInitialTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === DARK || stored === LIGHT) {
        return stored;
    }

    // No stored preference – respect system setting
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return prefersDark ? DARK : LIGHT;
}

/**
 * Toggle between dark and light themes, persisting the choice.
 */
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || DARK;
    const next = current === DARK ? LIGHT : DARK;
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
}

// Initialise theme on page load
(function initTheme() {
    const initialTheme = getInitialTheme();
    applyTheme(initialTheme);
    // Ensure the stored value reflects the applied theme (useful when system preference changes)
    localStorage.setItem(THEME_KEY, initialTheme);
})();

// Expose toggle function globally for UI elements (e.g., a button)
window.toggleTheme = toggleTheme;