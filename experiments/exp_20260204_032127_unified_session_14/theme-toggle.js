(() => {
    const THEME_KEY = 'theme';
    const root = document.documentElement;
    const toggleBtn = document.getElementById('theme-toggle');

    // Determine initial theme
    function getStoredTheme() {
        return localStorage.getItem(THEME_KEY);
    }

    function getSystemPreference() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function applyTheme(theme) {
        if (theme === 'dark') {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.removeAttribute('data-theme');
        }
    }

    function initTheme() {
        const stored = getStoredTheme();
        if (stored) {
            applyTheme(stored);
        } else {
            // Default to dark if no preference and system prefers light
            const system = getSystemPreference();
            const defaultTheme = system === 'dark' ? 'dark' : 'dark';
            applyTheme(defaultTheme);
        }
    }

    function toggleTheme() {
        const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
        localStorage.setItem(THEME_KEY, next);
    }

    // Initialize
    initTheme();

    // Attach event
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }
})();