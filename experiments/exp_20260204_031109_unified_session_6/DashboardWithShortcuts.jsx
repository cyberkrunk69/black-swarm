import React, { useEffect, useState, useCallback } from 'react';
import Dashboard from '../../src/components/Dashboard';
import Header from '../../src/components/Header';
import HelpOverlay from '../../src/components/HelpOverlay';

// Mapping of view modes
const VIEW_MODES = {
  GRID: 'grid',
  LOG: 'log',
  TREE: 'tree',
};

const HelpContent = `
Keyboard Shortcuts:
  g – Switch to Grid view
  l – Switch to Log view
  t – Switch to Tree view
  Space – Pause/Resume auto‑refresh
  r – Force refresh now
  ? – Show this help overlay
`;

const DashboardWithShortcuts = () => {
  const [viewMode, setViewMode] = useState(VIEW_MODES.GRID);
  const [autoRefreshPaused, setAutoRefreshPaused] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  // Handlers for each shortcut
  const switchToGrid = useCallback(() => setViewMode(VIEW_MODES.GRID), []);
  const switchToLog = useCallback(() => setViewMode(VIEW_MODES.LOG), []);
  const switchToTree = useCallback(() => setViewMode(VIEW_MODES.TREE), []);
  const toggleAutoRefresh = useCallback(() => setAutoRefreshPaused((p) => !p), []);
  const forceRefresh = useCallback(() => {
    // Assuming Dashboard exposes a static method to trigger refresh
    if (Dashboard.refresh) Dashboard.refresh();
  }, []);
  const toggleHelp = useCallback(() => setShowHelp((h) => !h), []);

  // Global key listener
  useEffect(() => {
    const handler = (e) => {
      // Ignore when typing in inputs/textareas
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
        return;
      }

      switch (e.key) {
        case 'g':
        case 'G':
          e.preventDefault();
          switchToGrid();
          break;
        case 'l':
        case 'L':
          e.preventDefault();
          switchToLog();
          break;
        case 't':
        case 'T':
          e.preventDefault();
          switchToTree();
          break;
        case ' ':
          e.preventDefault();
          toggleAutoRefresh();
          break;
        case 'r':
        case 'R':
          e.preventDefault();
          forceRefresh();
          break;
        case '?':
          e.preventDefault();
          toggleHelp();
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [switchToGrid, switchToLog, switchToTree, toggleAutoRefresh, forceRefresh, toggleHelp]);

  // Pass autoRefreshPaused state to Dashboard if it supports it
  const dashboardProps = {
    viewMode,
    paused: autoRefreshPaused,
    // any other props the original Dashboard expects
  };

  return (
    <>
      <Header>
        <div style={{ marginLeft: 'auto', fontWeight: 'bold' }}>
          Mode: {viewMode.charAt(0).toUpperCase() + viewMode.slice(1)}
          {autoRefreshPaused ? ' (Paused)' : ''}
        </div>
      </Header>
      <Dashboard {...dashboardProps} />
      {showHelp && (
        <HelpOverlay onClose={toggleHelp}>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{HelpContent}</pre>
        </HelpOverlay>
      )}
    </>
  );
};

export default DashboardWithShortcuts;