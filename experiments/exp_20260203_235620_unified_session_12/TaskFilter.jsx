import React, { useState, useEffect, useMemo } from "react";

/**
 * Utility: escape RegExp special characters in a plain string.
 */
function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Highlights all matches of the regex within the text.
 * Returns an array of React nodes.
 */
function highlightMatches(text, regex) {
  if (!regex) return text;
  const parts = [];
  let lastIndex = 0;
  let match;

  // Using while loop to capture all matches
  while ((match = regex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;
    if (start > lastIndex) {
      parts.push(text.slice(lastIndex, start));
    }
    parts.push(
      <mark key={start}>{text.slice(start, end)}</mark>
    );
    lastIndex = end;

    // Avoid zero-length matches causing infinite loops
    if (match[0].length === 0) {
      regex.lastIndex++;
    }
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts;
}

/**
 * Parses the URL hash to retrieve a persisted filter string.
 * Expected format: #filter=encodedString
 */
function getPersistedFilter() {
  const hash = window.location.hash.substring(1); // remove '#'
  const params = new URLSearchParams(hash);
  const encoded = params.get("filter");
  return encoded ? decodeURIComponent(encoded) : "";
}

/**
 * Persists the current filter string into the URL hash.
 */
function setPersistedFilter(filter) {
  const params = new URLSearchParams();
  if (filter) {
    params.set("filter", encodeURIComponent(filter));
  }
  const newHash = params.toString();
  window.location.replace(`#${newHash}`);
}

/**
 * Main component.
 *
 * Props:
 *   tasks: Array<{ id: string|number, description: string, status: string, phase: string }>
 */
export default function TaskFilter({ tasks }) {
  const [filter, setFilter] = useState(() => getPersistedFilter());

  // Sync filter with URL hash on mount / hash change
  useEffect(() => {
    const onHashChange = () => setFilter(getPersistedFilter());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  // Update URL hash whenever filter changes
  useEffect(() => {
    setPersistedFilter(filter);
  }, [filter]);

  // Build a RegExp from the filter string.
  // If the user input is an invalid regex, fallback to escaped plain text.
  const regex = useMemo(() => {
    if (!filter) return null;
    try {
      return new RegExp(filter, "gi");
    } catch (e) {
      // Treat as plain text search
      return new RegExp(escapeRegExp(filter), "gi");
    }
  }, [filter]);

  // Filtered tasks based on id, description, status, phase
  const filteredTasks = useMemo(() => {
    if (!regex) return tasks;
    return tasks.filter((task) => {
      const searchable = [
        String(task.id),
        task.description,
        task.status,
        task.phase,
      ].join(" ");
      return regex.test(searchable);
    });
  }, [tasks, regex]);

  // Render a row with highlighted fields
  const renderTaskRow = (task) => (
    <tr key={task.id}>
      <td>{regex ? highlightMatches(String(task.id), regex) : task.id}</td>
      <td>{regex ? highlightMatches(task.description, regex) : task.description}</td>
      <td>{regex ? highlightMatches(task.status, regex) : task.status}</td>
      <td>{regex ? highlightMatches(task.phase, regex) : task.phase}</td>
    </tr>
  );

  return (
    <div className="task-filter-container">
      <input
        type="text"
        placeholder="Search (regex supported)…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        style={{ width: "100%", padding: "8px", marginBottom: "12px", fontSize: "1rem" }}
      />
      <table className="task-table" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>ID</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Description</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Status</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ccc" }}>Phase</th>
          </tr>
        </thead>
        <tbody>
          {filteredTasks.length > 0 ? (
            filteredTasks.map(renderTaskRow)
          ) : (
            <tr>
              <td colSpan={4} style={{ textAlign: "center", padding: "12px" }}>
                No tasks match the filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}