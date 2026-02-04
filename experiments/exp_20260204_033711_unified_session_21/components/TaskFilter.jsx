import React, { useState, useEffect, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import PropTypes from 'prop-types';

/**
 * TaskFilter component
 *
 * Props:
 *  - tasks: Array of task objects { id, description, status, phase }
 *  - onFiltered: Callback receiving filtered task list
 *
 * Features:
 *  - Text input supports plain text or regular expressions.
 *  - Filters by id, description, status, or phase (case‑insensitive).
 *  - Highlights matching substrings in the rendered task list.
 *  - Persists the current filter string in the URL hash (`#filter=...`) for shareability.
 */
export default function TaskFilter({ tasks, onFiltered }) {
  const location = useLocation();
  const navigate = useNavigate();

  // Extract filter from URL hash on mount / hash change
  const getFilterFromHash = () => {
    const hash = location.hash.replace(/^#/, '');
    const params = new URLSearchParams(hash);
    return params.get('filter') || '';
  };

  const [filter, setFilter] = useState(getFilterFromHash());

  // Keep URL hash in sync with filter state
  useEffect(() => {
    const params = new URLSearchParams();
    if (filter) {
      params.set('filter', filter);
    }
    const newHash = params.toString();
    if (newHash !== location.hash.replace(/^#/, '')) {
      navigate({ hash: newHash }, { replace: true });
    }
  }, [filter, navigate, location.hash]);

  // Listen for external hash changes (e.g., user pastes a new URL)
  useEffect(() => {
    const unlisten = navigate((location) => {
      const newFilter = getFilterFromHash();
      if (newFilter !== filter) {
        setFilter(newFilter);
      }
    });
    return () => unlisten();
  }, [navigate, filter]);

  // Build RegExp safely – fall back to plain text search if regex is invalid
  const matcher = useMemo(() => {
    if (!filter) return null;
    try {
      return new RegExp(filter, 'i');
    } catch (e) {
      // Escape special characters for literal search
      const escaped = filter.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return new RegExp(escaped, 'i');
    }
  }, [filter]);

  // Filter tasks based on matcher
  const filteredTasks = useMemo(() => {
    if (!matcher) return tasks;
    return tasks.filter((t) => {
      const searchable = `${t.id} ${t.description} ${t.status} ${t.phase}`;
      return matcher.test(searchable);
    });
  }, [tasks, matcher]);

  // Notify parent about filtered list
  useEffect(() => {
    onFiltered(filteredTasks);
  }, [filteredTasks, onFiltered]);

  // Helper to wrap matches in <mark>
  const highlight = (text) => {
    if (!matcher) return text;
    const parts = [];
    let lastIndex = 0;
    let match;
    while ((match = matcher.exec(text)) !== null) {
      const start = match.index;
      const end = start + match[0].length;
      if (start > lastIndex) {
        parts.push(text.slice(lastIndex, start));
      }
      parts.push(
        <mark key={start}>{text.slice(start, end)}</mark>
      );
      lastIndex = end;
      // Prevent zero‑length infinite loops
      if (match[0].length === 0) {
        matcher.lastIndex += 1;
      }
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    return parts.length ? parts : text;
  };

  return (
    <div className="task-filter">
      <input
        type="text"
        placeholder="Search tasks (regex supported)…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        style={{ width: '100%', padding: '0.5rem', marginBottom: '1rem' }}
      />
      <ul className="task-list">
        {filteredTasks.map((task) => (
          <li key={task.id} className="task-item">
            <div>
              <strong>ID:</strong> {highlight(String(task.id))}
            </div>
            <div>
              <strong>Description:</strong> {highlight(task.description)}
            </div>
            <div>
              <strong>Status:</strong> {highlight(task.status)}
            </div>
            <div>
              <strong>Phase:</strong> {highlight(task.phase)}
            </div>
          </li>
        ))}
        {filteredTasks.length === 0 && (
          <li className="no-results">No tasks match the current filter.</li>
        )}
      </ul>
    </div>
  );
}

TaskFilter.propTypes = {
  tasks: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      description: PropTypes.string.isRequired,
      status: PropTypes.string.isRequired,
      phase: PropTypes.string.isRequired,
    })
  ).isRequired,
  onFiltered: PropTypes.func,
};

TaskFilter.defaultProps = {
  onFiltered: () => {},
};