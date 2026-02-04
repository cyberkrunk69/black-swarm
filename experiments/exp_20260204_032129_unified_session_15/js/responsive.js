/**
 * responsive.js - Handles sidebar collapse/expand for touch devices.
 * Attach this script to the page after the DOM is ready.
 */

document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.querySelector('.sidebar');
  const toggleBtn = document.querySelector('.sidebar-toggle');

  if (!sidebar || !toggleBtn) {
    // No sidebar or toggle button present; nothing to do.
    return;
  }

  // Initialize state based on viewport width
  function initSidebar() {
    if (window.innerWidth <= 768) {
      sidebar.classList.remove('open');
    } else {
      sidebar.classList.add('open');
    }
  }

  // Toggle sidebar visibility
  function toggleSidebar() {
    sidebar.classList.toggle('open');
  }

  // Event listeners
  toggleBtn.addEventListener('click', toggleSidebar);
  window.addEventListener('resize', initSidebar);

  // Initial setup
  initSidebar();
});