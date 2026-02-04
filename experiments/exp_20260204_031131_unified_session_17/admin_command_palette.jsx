import React, { useState, useEffect, useRef } from "react";
import Fuse from "fuse.js";
import "./admin_command_palette.css";

/**
 * AdminCommandPalette
 *
 * Press Ctrl+K to open the palette.
 * Type to fuzzy‑search a list of admin commands.
 * Selecting a command triggers an API call to /api/admin/execute.
 *
 * Commands supported:
 *   - restart swarm
 *   - clear logs
 *   - export stats
 *   - pause workers
 *
 * The component is deliberately self‑contained so it can be dropped
 * into any page of the application.
 */
const COMMANDS = [
  {
    name: "restart swarm",
    description: "Restart the entire swarm of workers",
    endpoint: "/api/admin/restart_swarm",
    method: "POST",
  },
  {
    name: "clear logs",
    description: "Delete all log files on the server",
    endpoint: "/api/admin/clear_logs",
    method: "POST",
  },
  {
    name: "export stats",
    description: "Export current statistics as a JSON file",
    endpoint: "/api/admin/export_stats",
    method: "GET",
  },
  {
    name: "pause workers",
    description: "Pause all workers temporarily",
    endpoint: "/api/admin/pause_workers",
    method: "POST",
  },
];

// Fuse.js options for fuzzy searching
const fuseOptions = {
  keys: ["name", "description"],
  includeScore: true,
  threshold: 0.4,
};

export default function AdminCommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(COMMANDS);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef(null);
  const fuse = useRef(new Fuse(COMMANDS, fuseOptions));

  // Global key listener for Ctrl+K
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Focus the input when palette opens
  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    } else {
      setQuery("");
      setResults(COMMANDS);
      setSelectedIdx(0);
    }
  }, [open]);

  // Update fuzzy results when query changes
  useEffect(() => {
    if (!query) {
      setResults(COMMANDS);
      setSelectedIdx(0);
      return;
    }
    const matches = fuse.current.search(query);
    setResults(matches.map((m) => m.item));
    setSelectedIdx(0);
  }, [query]);

  const executeCommand = async (cmd) => {
    try {
      const response = await fetch(cmd.endpoint, {
        method: cmd.method,
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        const err = await response.text();
        alert(`Command failed: ${err}`);
        return;
      }
      const data = await response.json();
      alert(`Command "${cmd.name}" executed successfully.\nResponse: ${JSON.stringify(data)}`);
    } catch (e) {
      console.error(e);
      alert(`Error executing command: ${e.message}`);
    } finally {
      setOpen(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIdx((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIdx((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[selectedIdx]) {
        executeCommand(results[selectedIdx]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  if (!open) return null;

  return (
    <div className="admin-palette-backdrop" onClick={() => setOpen(false)}>
      <div className="admin-palette-modal" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          type="text"
          placeholder="Type a command..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="admin-palette-input"
        />
        <ul className="admin-palette-list">
          {results.map((cmd, idx) => (
            <li
              key={cmd.name}
              className={`admin-palette-item ${idx === selectedIdx ? "selected" : ""}`}
              onMouseEnter={() => setSelectedIdx(idx)}
              onClick={() => executeCommand(cmd)}
            >
              <span className="cmd-name">{cmd.name}</span>
              <span className="cmd-desc">{cmd.description}</span>
            </li>
          ))}
          {results.length === 0 && <li className="admin-palette-no-results">No commands found</li>}
        </ul>
      </div>
    </div>
  );
}