import React from 'react';
import PropTypes from 'prop-types';

/**
 * Compact tree summary element.
 *
 * Props:
 *  - title: string – task title
 *  - completed: number – number of completed items
 *  - total: number – total items
 *  - nodeType: string – one of 'default', 'error', 'warning', 'success' (determines border color)
 *  - onExpand: func – callback when expand button is clicked
 */
const NODE_COLORS = {
  default: '#bbb',
  error: '#e74c3c',
  warning: '#f1c40f',
  success: '#2ecc71',
};

const TreeMiniSummary = ({
  title,
  completed,
  total,
  nodeType = 'default',
  onExpand,
}) => {
  const borderColor = NODE_COLORS[nodeType] || NODE_COLORS.default;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        padding: '4px 8px',
        border: `1px solid ${borderColor}`,
        borderRadius: '4px',
        backgroundColor: '#fafafa',
        fontFamily: 'sans-serif',
        fontSize: '0.85rem',
        cursor: 'pointer',
        userSelect: 'none',
        maxWidth: '250px',
      }}
      onClick={onExpand}
      title="Click to expand full tree"
    >
      {/* Tree icon (simple caret) */}
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill={borderColor}
        style={{ marginRight: '6px' }}
      >
        <path d="M8 5v14l11-7z" />
      </svg>

      {/* Title */}
      <span style={{ flexGrow: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {title}
      </span>

      {/* Completed/Total */}
      <span style={{ margin: '0 6px', color: '#555' }}>
        {completed}/{total}
      </span>

      {/* Expand button (plus icon) */}
      <button
        type="button"
        onClick={e => {
          e.stopPropagation();
          onExpand?.();
        }}
        style={{
          background: 'none',
          border: 'none',
          padding: 0,
          margin: 0,
          cursor: 'pointer',
          color: borderColor,
        }}
        aria-label="Expand tree"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill={borderColor}>
          <path d="M19 13H13v6h-2v-6H5v-2h6V5h2v6h6v2z" />
        </svg>
      </button>
    </div>
  );
};

TreeMiniSummary.propTypes = {
  title: PropTypes.string.isRequired,
  completed: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
  nodeType: PropTypes.oneOf(['default', 'error', 'warning', 'success']),
  onExpand: PropTypes.func,
};

export default TreeMiniSummary;