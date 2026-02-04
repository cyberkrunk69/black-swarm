// responsive.js – Simple sidebar toggle for touch devices
// Attach this script after the DOM is loaded (e.g., at the end of body)

document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.querySelector('.sidebar');
  const toggleBtn = document.createElement('button');
  toggleBtn.className = 'sidebar-toggle';
  toggleBtn.setAttribute('aria-label', 'Toggle navigation');
  toggleBtn.innerHTML = '&#9776;'; // Hamburger icon

  // Insert toggle button as first child of body
  document.body.appendChild(toggleBtn);

  // Toggle handler
  toggleBtn.addEventListener('click', function () {
    if (sidebar) {
      sidebar.classList.toggle('open');
    }
  });

  // Optional: close sidebar when clicking outside (mobile)
  document.addEventListener('click', function (e) {
    if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target) && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
    }
  });
});