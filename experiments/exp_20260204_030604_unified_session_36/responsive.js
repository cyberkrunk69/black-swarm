/*
 * responsive.js - Handles sidebar toggle for mobile/tablet breakpoints
 * Assumes existence of elements:
 *   #sidebar          - the navigation sidebar
 *   #sidebar-toggle   - button inserted by CSS (or rendered server‑side)
 *
 * This script adds the required event listeners and ensures that
 * clicking outside the sidebar closes it on small screens.
 */

document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');

    if (!sidebar) {
        console.warn('Responsive script: #sidebar element not found.');
        return;
    }

    // Create toggle button if not present (useful when CSS hides it)
    if (!toggleBtn) {
        const btn = document.createElement('button');
        btn.id = 'sidebar-toggle';
        btn.innerHTML = '&#9776;'; // hamburger
        btn.setAttribute('aria-label', 'Toggle navigation');
        document.body.appendChild(btn);
    }

    const button = document.getElementById('sidebar-toggle');

    // Toggle sidebar open/close
    button.addEventListener('click', function (e) {
        e.stopPropagation();
        sidebar.classList.toggle('open');
    });

    // Close sidebar when clicking outside (only for small screens)
    document.addEventListener('click', function (e) {
        const isSmallScreen = window.innerWidth <= 768;
        if (isSmallScreen && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && e.target !== button) {
                sidebar.classList.remove('open');
            }
        }
    });

    // Optional: close on ESC key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
        }
    });

    // Adjust on resize (remove open state when moving to large screens)
    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
        }
    });
});