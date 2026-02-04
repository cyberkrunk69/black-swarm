import React, { useState, useEffect, useRef } from 'react';
import Fuse from 'fuse.js';
import './command_palette.css';

// Define available admin commands
const COMMANDS = [
  {
    name: 'restart swarm',
    description: 'Restart the entire swarm of workers',
    endpoint: '/api/admin/restart-swarm',
    method: 'POST',
  },
  {
    name: 'clear logs',
    description: 'Clear all system logs',
    endpoint: '/api/admin/clear-logs',
    method: 'POST',
  },
  {
    name: 'export stats',
    description: 'Export current statistics as JSON',
    endpoint: '/api/admin/export-stats',
    method: 'GET',
  },
  {
    name: 'pause workers',
    description: 'Pause all active workers',
    endpoint: '/api/admin/pause-workers',
    method: 'POST',
  },
];

// Fuse.js options for fuzzy searching
const fuseOptions = {
  keys: ['name', 'description'],
  threshold: 0.4,
};

const fuse = new Fuse(COMMANDS, fuseOptions);

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(COMMANDS);
  const inputRef = useRef(null);

  // Open palette on Ctrl+K
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  // Update fuzzy search results
  useEffect(() => {
    if (query.trim() === '') {
      setResults(COMMANDS);
    } else {
      const matches = fuse.search(query);
      setResults(matches.map((m) => m.item));
    }
  }, [query]);

  const executeCommand = async (cmd) => {
    try {
      const response = await fetch(cmd.endpoint, {
        method: cmd.method,
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        const err = await response.text();
        alert(`Error: ${err}`);
        return;
      }
      const data = await response.json();
      alert(`Success: ${JSON.stringify(data)}`);
    } catch (err) {
      alert(`Network error: ${err.message}`);
    } finally {
      setOpen(false);
      setQuery('');
    }
  };

  if (!open) return null;

  return (
    <div className="command-palette-overlay" onClick={() => setOpen(false)}>
      <div className="command-palette" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          type="text"
          placeholder="Type a command…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <ul className="command-list">
          {results.map((cmd) => (
            <li
              key={cmd.name}
              className="command-item"
              onClick={() => executeCommand(cmd)}
            >
              <strong>{cmd.name}</strong>
              <span className="cmd-desc">{cmd.description}</span>
            </li>
          ))}
          {results.length === 0 && <li className="no-results">No commands found</li>}
        </ul>
      </div>
    </div>
  );
}