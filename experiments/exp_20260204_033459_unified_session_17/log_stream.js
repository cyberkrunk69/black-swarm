/**
 * Live Log Stream Panel
 * Tails the last 50 lines from grind_logs/ in real-time.
 * Color-codes by log level:
 *   START → blue
 *   DONE  → green
 *   FAIL  → red
 *   SKIP  → gray
 * Auto‑scrolls, but pauses when the user hovers over the panel.
 */

(() => {
  const LOG_URL = '/grind_logs/latest.log'; // Adjust if a different file is used
  const REFRESH_INTERVAL = 2000; // ms
  const MAX_LINES = 50;

  const logContainer = document.getElementById('log-panel');
  if (!logContainer) return;

  let pause = false;
  let timerId = null;

  const levelColors = {
    START: 'color: #1e90ff;', // blue
    DONE:  'color: #28a745;', // green
    FAIL:  'color: #dc3545;', // red
    SKIP:  'color: #6c757d;'  // gray
  };

  // Parse a line and wrap it in a span with appropriate color
  function colorizeLine(line) {
    const match = line.match(/\\b(START|DONE|FAIL|SKIP)\\b/);
    if (match) {
      const level = match[1];
      const style = levelColors[level] || '';
      return `<span style="${style}">${escapeHtml(line)}</span>`;
    }
    return escapeHtml(line);
  }

  // Simple HTML escaper
  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, (c) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    })[c]);
  }

  async function fetchLog() {
    try {
      const resp = await fetch(LOG_URL, { cache: 'no-store' });
      if (!resp.ok) throw new Error('Network response was not ok');
      const text = await resp.text();
      const lines = text.split(/\\r?\\n/).filter(l => l.trim() !== '');
      const tail = lines.slice(-MAX_LINES);
      const html = tail.map(colorizeLine).join('\\n');
      logContainer.innerHTML = html;
      if (!pause) {
        logContainer.scrollTop = logContainer.scrollHeight;
      }
    } catch (e) {
      console.error('Failed to fetch log:', e);
    }
  }

  function start() {
    fetchLog(); // initial load
    timerId = setInterval(() => {
      if (!pause) fetchLog();
    }, REFRESH_INTERVAL);
  }

  function stop() {
    if (timerId) clearInterval(timerId);
  }

  // Hover handling
  logContainer.addEventListener('mouseenter', () => { pause = true; });
  logContainer.addEventListener('mouseleave', () => { pause = false; });

  // Start the loop when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();