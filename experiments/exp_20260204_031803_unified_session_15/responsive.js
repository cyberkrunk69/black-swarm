/* responsive.js – Handles sidebar toggle for touch devices */

document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.getElementById('sidebar');
  const toggleBtn = document.getElementById('sidebar-toggle');
  const overlay = document.createElement('div');
  overlay.id = 'sidebar-overlay';
  document.body.appendChild(overlay);

  function openSidebar() {
    sidebar.classList.add('collapsed');
    overlay.style.display = 'block';
  }

  function closeSidebar() {
    sidebar.classList.remove('collapsed');
    overlay.style.display = 'none';
  }

  // Toggle button click
  if (toggleBtn) {
    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      if (sidebar.classList.contains('collapsed')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  // Click outside sidebar closes it
  overlay.addEventListener('click', closeSidebar);

  // Optional: swipe gestures for touch devices
  let startX = null;
  document.addEventListener('touchstart', function (e) {
    startX = e.touches[0].clientX;
  }, {passive: true});

  document.addEventListener('touchend', function (e) {
    if (startX === null) return;
    const endX = e.changedTouches[0].clientX;
    const diff = endX - startX;

    // Swipe right to open, left to close (threshold 50px)
    if (diff > 50 && !sidebar.classList.contains('collapsed')) {
      openSidebar();
    } else if (diff < -50 && sidebar.classList.contains('collapsed')) {
      closeSidebar();
    }
    startX = null;
  }, {passive: true});
});