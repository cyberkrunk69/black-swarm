/* responsive.js – sidebar toggle for touch devices */

document.addEventListener('DOMContentLoaded', function () {
    const toggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');

    if (!toggleBtn || !sidebar) {
        // No sidebar or toggle button present – nothing to do.
        return;
    }

    // Toggle the 'open' class which controls visibility via CSS
    toggleBtn.addEventListener('click', function () {
        sidebar.classList.toggle('open');
    });

    // Optional: close sidebar when clicking outside of it (mobile UX)
    document.addEventListener('click', function (e) {
        if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
            sidebar.classList.remove('open');
        }
    });

    // Close sidebar on orientation change to avoid stale state
    window.addEventListener('orientationchange', function () {
        if (window.innerWidth > 768) {
            // Desktop view – ensure sidebar is visible
            sidebar.classList.remove('open');
            sidebar.style.transform = '';
        }
    });
});