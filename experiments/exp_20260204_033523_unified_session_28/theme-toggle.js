(() => {
  const THEME_KEY = "theme-preference";
  const DARK = "dark";
  const LIGHT = "light";

  // Determine initial theme
  function getInitialTheme() {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === DARK || stored === LIGHT) {
      return stored;
    }
    // No stored preference, respect system setting
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    return prefersDark ? DARK : LIGHT;
  }

  // Apply theme to document
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
  }

  // Toggle theme and persist
  function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme") || DARK;
    const next = current === DARK ? LIGHT : DARK;
    applyTheme(next);
    localStorage.setItem(THEME_KEY, next);
  }

  // Initialize
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  // Expose toggle function (e.g., for a button)
  document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("theme-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", toggleTheme);
    }
  });

  // Optional: listen to system preference changes if no explicit user choice
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQuery.addEventListener("change", (e) => {
    const stored = localStorage.getItem(THEME_KEY);
    if (!stored) {
      const newTheme = e.matches ? DARK : LIGHT;
      applyTheme(newTheme);
    }
  });
})();