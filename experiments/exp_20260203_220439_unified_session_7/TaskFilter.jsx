import React, { useState, useEffect, useMemo } from "react";

/**
 * TaskFilter component
 *
 * Props:
 *  - tasks: Array<{ id: string|number, description: string, status: string, phase: string }>
 *  - onFiltered?: (filteredTasks) => void   // optional callback when filter changes
 *
 * Features:
 *  - Text input that accepts plain text or regex (if wrapped in /.../).
 *  - Filters tasks by id, description, status, or phase.
 *  - Highlights matching substrings using <mark>.
 *  - Persists the current filter string in the URL hash (e.g., #filter=abc)
 *  - Restores filter from URL hash on mount for shareable links.
 */
const TaskFilter = ({ tasks, onFiltered }) => {
  const [filter, setFilter] = useState("");

  // Load filter from URL hash on mount
  useEffect(() => {
    const hash = window.location.hash;
    const match = hash.match(/filter=([^&]*)/);
    if (match && match[1]) {
      try {
        const decoded = decodeURIComponent(match[1]);
        setFilter(decoded);
      } catch (_) {
        // ignore malformed hash
      }
    }
  }, []);

  // Update URL hash whenever filter changes
  useEffect(() => {
    const encoded = encodeURIComponent(filter);
    const newHash = `filter=${encoded}`;
    if (window.location.hash !== `#${newHash}`) {
      window.location.replace(`#${newHash}`);
    }
  }, [filter]);

  // Build regex from filter string (supports /.../ flags)
  const filterRegex = useMemo(() => {
    if (!filter) return null;
    try {
      // If filter looks like a regex literal /pattern/flags
      const regexLiteral = filter.match(/^\/(.+)\/([gimsuy]*)$/);
      if (regexLiteral) {
        return new RegExp(regexLiteral[1], regexLiteral[2] || "i");
      }
      // Otherwise, escape special chars for a simple contains search (case‑insensitive)
      const escaped = filter.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return new RegExp(escaped, "i");
    } catch (e) {
      // Invalid regex – treat as no match
      return null;
    }
  }, [filter]);

  // Filter and highlight tasks
  const filteredTasks = useMemo(() => {
    if (!filterRegex) return tasks;
    return tasks.filter((t) => {
      const searchable = `${t.id} ${t.description} ${t.status} ${t.phase}`;
      return filterRegex.test(searchable);
    });
  }, [tasks, filterRegex]);

  // Optional external callback
  useEffect(() => {
    if (onFiltered) onFiltered(filteredTasks);
  }, [filteredTasks, onFiltered]);

  // Helper to wrap matches in <mark>
  const highlight = (text) => {
    if (!filterRegex) return text;
    const parts = [];
    let lastIndex = 0;
    let match;
    while ((match = filterRegex.exec(text)) !== null) {
      const start = match.index;
      const end = start + match[0].length;
      if (start > lastIndex) {
        parts.push(text.slice(lastIndex, start));
      }
      parts.push(<mark key={start}>{text.slice(start, end)}</mark>);
      lastIndex = end;
      // Prevent infinite loops with zero‑length matches
      if (match[0].length === 0) {
        filterRegex.lastIndex++;
      }
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    // Reset lastIndex for next call
    filterRegex.lastIndex = 0;
    return parts.length ? parts : text;
  };

  return (
    <div className="task-filter">
      <input
        type="text"
        placeholder="Search tasks (id, description, status, phase). Use /regex/ for regex."
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="task-filter-input"
        style={{ width: "100%", padding: "0.5rem", marginBottom: "1rem" }}
      />
      <ul className="task-list">
        {filteredTasks.map((task) => (
          <li key={task.id} className="task-item">
            <strong>{highlight(String(task.id))}:</strong>{" "}
            {highlight(task.description)} –{" "}
            <em>{highlight(task.status)}</em> –{" "}
            <span>{highlight(task.phase)}</span>
          </li>
        ))}
        {filteredTasks.length === 0 && (
          <li className="no-results">No tasks match the current filter.</li>
        )}
      </ul>
    </div>
  );
};

export default TaskFilter;