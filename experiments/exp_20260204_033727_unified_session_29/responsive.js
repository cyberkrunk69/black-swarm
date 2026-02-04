// responsive.js - Handles sidebar toggle for touch devices and small screens

document.addEventListener('DOMContentLoaded', function () {
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');

    // If toggle button doesn't exist, create it (useful for pages that didn't include it)
    if (!toggleBtn) {
        const btn = document.createElement('button');
        btn.id = 'sidebar-toggle';
        btn.innerHTML = '&#9776;'; // hamburger icon
        document.body.appendChild(btn);
    }

    const button = document.getElementById('sidebar-toggle');

    // Toggle sidebar visibility
    button.addEventListener('click', function (e) {
        e.stopPropagation();
        sidebar.classList.toggle('active');
    });

    // Close sidebar when clicking outside (on small screens)
    document.addEventListener('click', function (e) {
        if (window.innerWidth <= 768 && sidebar.classList.contains('active')) {
            if (!sidebar.contains(e.target) && e.target !== button) {
                sidebar.classList.remove('active');
            }
        }
    });

    // Optional: close sidebar on resize if moving to larger screen
    window.addEventListener('resize', function () {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
        }
    });
});