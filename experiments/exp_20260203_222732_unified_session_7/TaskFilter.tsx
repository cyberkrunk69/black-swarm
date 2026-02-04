import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

/**
 * Types for a task. Adjust if your actual task shape differs.
 */
export interface Task {
  id: string;
  description: string;
  status: string;
  phase: string;
}

/**
 * Props for the TaskFilter component.
 */
interface TaskFilterProps {
  /** Full list of tasks to filter/display */
  tasks: Task[];
}

/**
 * Helper: escape special regex characters if the user wants a literal search.
 * If the input starts and ends with `/` we treat it as a raw RegExp, otherwise we
 * escape it.
 */
function buildRegExp(input: string): RegExp | null {
  if (!input) return null;
  try {
    // If user entered something like /pattern/flags, use it directly
    if (input.startsWith("/") && input.lastIndexOf("/") > 0) {
      const lastSlash = input.lastIndexOf("/");
      const pattern = input.slice(1, lastSlash);
      const flags = input.slice(lastSlash + 1);
      return new RegExp(pattern, flags);
    }
    // Otherwise escape special characters for a literal search (case‑insensitive)
    const escaped = input.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return new RegExp(escaped, "i");
  } catch {
    // Invalid RegExp – ignore filter
    return null;
  }
}

/**
 * Highlight all RegExp matches inside a string by wrapping them in <mark>.
 */
function highlightMatches(text: string, regex: RegExp | null): React.ReactNode {
  if (!regex) return text;
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  // Reset lastIndex in case the regex has the global flag
  regex.lastIndex = 0;
  while ((match = regex.exec(text)) !== null) {
    const start = match.index;
    const end = start + match[0].length;
    if (start > lastIndex) {
      parts.push(text.slice(lastIndex, start));
    }
    parts.push(
      <mark key={start} style={{ backgroundColor: "#fffd38" }}>
        {text.slice(start, end)}
      </mark>
    );
    lastIndex = end;
    // Prevent infinite loops for zero‑length matches
    if (match[0].length === 0) regex.lastIndex++;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

/**
 * Main component – renders a search box and a filtered task list.
 */
export const TaskFilter: React.FC<TaskFilterProps> = ({ tasks }) => {
  const location = useLocation();
  const navigate = useNavigate();

  // Initialise filter from URL hash (without the leading #)
  const initialFilter = decodeURIComponent(location.hash.replace(/^#/, "")) || "";
  const [filterText, setFilterText] = useState<string>(initialFilter);
  const filterRegex = useMemo(() => buildRegExp(filterText), [filterText]);

  // Persist filter in URL hash whenever it changes
  useEffect(() => {
    const encoded = encodeURIComponent(filterText);
    navigate(`#${encoded}`, { replace: true });
  }, [filterText, navigate]);

  // Filter tasks based on the regex matching any of the searchable fields
  const filteredTasks = useMemo(() => {
    if (!filterRegex) return tasks;
    return tasks.filter((t) => {
      return (
        filterRegex.test(t.id) ||
        filterRegex.test(t.description) ||
        filterRegex.test(t.status) ||
        filterRegex.test(t.phase)
      );
    });
  }, [tasks, filterRegex]);

  return (
    <div style={{ padding: "1rem" }}>
      <input
        type="text"
        placeholder="Search tasks (id, description, status, phase). Regex supported."
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
        style={{
          width: "100%",
          padding: "0.5rem",
          marginBottom: "1rem",
          fontSize: "1rem",
        }}
      />
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>ID</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Description</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Status</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Phase</th>
          </tr>
        </thead>
        <tbody>
          {filteredTasks.map((t) => (
            <tr key={t.id} style={{ borderBottom: "1px solid #f0f0f0" }}>
              <td>{highlightMatches(t.id, filterRegex)}</td>
              <td>{highlightMatches(t.description, filterRegex)}</td>
              <td>{highlightMatches(t.status, filterRegex)}</td>
              <td>{highlightMatches(t.phase, filterRegex)}</td>
            </tr>
          ))}
          {filteredTasks.length === 0 && (
            <tr>
              <td colSpan={4} style={{ textAlign: "center", padding: "1rem" }}>
                No tasks match the current filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default TaskFilter;