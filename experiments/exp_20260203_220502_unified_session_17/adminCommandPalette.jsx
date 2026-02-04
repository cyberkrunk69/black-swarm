import React, { useState, useEffect, useRef } from "react";
import Fuse from "fuse.js";
import "./adminCommandPalette.css";

const COMMANDS = [
  {
    name: "restart swarm",
    description: "Restart the entire swarm of workers",
    endpoint: "/api/admin/restart-swarm",
    method: "POST",
  },
  {
    name: "clear logs",
    description: "Clear all system logs",
    endpoint: "/api/admin/clear-logs",
    method: "POST",
  },
  {
    name: "export stats",
    description: "Export current statistics as JSON",
    endpoint: "/api/admin/export-stats",
    method: "GET",
  },
  {
    name: "pause workers",
    description: "Pause all active workers",
    endpoint: "/api/admin/pause-workers",
    method: "POST",
  },
];

// Initialize Fuse for fuzzy searching
const fuse = new Fuse(COMMANDS, {
  keys: ["name", "description"],
  threshold: 0.3,
});

export default function AdminCommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState(COMMANDS);
  const inputRef = useRef(null);

  // Open palette on Ctrl+K
  useEffect(() => {
    const handler = (e) => {
      if (e.ctrlKey && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    } else {
      setQuery("");
      setResults(COMMANDS);
    }
  }, [open]);

  // Update fuzzy search results
  useEffect(() => {
    if (!query) {
      setResults(COMMANDS);
    } else {
      const matches = fuse.search(query).map((res) => res.item);
      setResults(matches);
    }
  }, [query]);

  const executeCommand = async (cmd) => {
    try {
      const opts = {
        method: cmd.method,
        headers: { "Content-Type": "application/json" },
      };
      if (cmd.method !== "GET") {
        opts.body = JSON.stringify({ command: cmd.name });
      }
      const response = await fetch(cmd.endpoint, opts);
      if (!response.ok) {
        const err = await response.text();
        alert(`Command failed: ${err}`);
        return;
      }
      const data = await response.json();
      alert(`Command "${cmd.name}" executed successfully.`);
      console.log("Command response:", data);
    } catch (err) {
      console.error(err);
      alert(`Error executing command: ${err.message}`);
    } finally {
      setOpen(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && results.length === 1) {
      executeCommand(results[0]);
    }
  };

  if (!open) return null;

  return (
    <div className="admin-palette-overlay" onClick={() => setOpen(false)}>
      <div className="admin-palette-modal" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          type="text"
          placeholder="Type a command…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="admin-palette-input"
        />
        <ul className="admin-palette-list">
          {results.map((cmd) => (
            <li
              key={cmd.name}
              className="admin-palette-item"
              onClick={() => executeCommand(cmd)}
            >
              <strong>{cmd.name}</strong>
              <span className="admin-palette-desc">{cmd.description}</span>
            </li>
          ))}
          {results.length === 0 && (
            <li className="admin-palette-no-results">No commands found</li>
          )}
        </ul>
      </div>
    </div>
  );
}