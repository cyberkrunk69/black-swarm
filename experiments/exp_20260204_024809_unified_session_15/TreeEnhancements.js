/**
 * TreeEnhancements.js
 *
 * This module provides a higher‑order component (HOC) that wraps the existing
 * Tree component to ensure that all interactive operations (scale, collapse,
 * drag) affect only the tree instance they belong to. It also introduces a
 * simple z‑index manager so that a tree being dragged is brought to the front
 * of the UI stack.
 *
 * Usage:
 *   import withTreeIsolation from './TreeEnhancements';
 *   const IsolatedTree = withTreeIsolation(Tree);
 *
 *   // In JSX
 *   <IsolatedTree {...props} />
 */

import React, { useRef, useState, useEffect, useCallback } from 'react';

// Simple z-index manager – a module‑level counter.
let globalZIndex = 1;

/**
 * withTreeIsolation – HOC
 *
 * @param {React.ComponentType<any>} WrappedTree The original Tree component.
 * @returns {React.FC<any>} A new component with isolated interactions.
 */
export default function withTreeIsolation(WrappedTree) {
  // Return a functional component that forwards all props.
  const IsolatedTree = (props) => {
    // Local state for scale and collapsed nodes – isolated per instance.
    const [scale, setScale] = useState(1);
    const [collapsedNodes, setCollapsedNodes] = useState(new Set());

    // Ref to the root DOM element of this tree.
    const treeRef = useRef(null);

    // -------------------------------------------------------------------------
    // Z‑INDEX handling for drag operations
    // -------------------------------------------------------------------------
    const bringToFront = useCallback(() => {
      // Increment the global counter and assign it to this tree.
      const newZ = ++globalZIndex;
      if (treeRef.current) {
        treeRef.current.style.zIndex = newZ;
      }
    }, []);

    // Drag event handlers – they only affect this tree.
    const handleDragStart = useCallback(
      (e) => {
        bringToFront();
        // Preserve any original dragStart handler the wrapped tree might use.
        if (props.onDragStart) {
          props.onDragStart(e);
        }
      },
      [bringToFront, props]
    );

    const handleDragEnd = useCallback(
      (e) => {
        if (props.onDragEnd) {
          props.onDragEnd(e);
        }
      },
      [props]
    );

    // -------------------------------------------------------------------------
    // Scale handling – isolated per tree
    // -------------------------------------------------------------------------
    const handleWheel = useCallback(
      (e) => {
        // Only react to ctrl+wheel or pinch gestures if needed.
        // Here we simply use vertical wheel delta to adjust scale.
        const delta = e.deltaY;
        const factor = delta > 0 ? 0.9 : 1.1;
        setScale((prev) => {
          const newScale = Math.min(Math.max(prev * factor, 0.5), 3);
          return newScale;
        });
        e.preventDefault();
      },
      []
    );

    // -------------------------------------------------------------------------
    // Collapse handling – isolated per tree
    // -------------------------------------------------------------------------
    const toggleNode = useCallback(
      (nodeId) => {
        setCollapsedNodes((prev) => {
          const newSet = new Set(prev);
          if (newSet.has(nodeId)) {
            newSet.delete(nodeId);
          } else {
            newSet.add(nodeId);
          }
          return newSet;
        });
      },
      []
    );

    // -------------------------------------------------------------------------
    // Effect: attach wheel listener to the tree container.
    // -------------------------------------------------------------------------
    useEffect(() => {
      const el = treeRef.current;
      if (el) {
        el.addEventListener('wheel', handleWheel, { passive: false });
        return () => {
          el.removeEventListener('wheel', handleWheel);
        };
      }
    }, [handleWheel]);

    // -------------------------------------------------------------------------
    // Render
    // -------------------------------------------------------------------------
    return (
      <div
        ref={treeRef}
        style={{
          transform: `scale(${scale})`,
          transformOrigin: '0 0',
          position: 'relative', // required for z-index
          // Initial z-index is low; it will be raised on drag.
          zIndex: 1,
          userSelect: 'none',
        }}
        draggable
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
      >
        {/* Pass down the isolated state and helpers to the wrapped tree. */}
        <WrappedTree
          {...props}
          collapsedNodes={collapsedNodes}
          onToggleNode={toggleNode}
          // The wrapped component can still receive its own callbacks.
          // We expose scale only for visual consistency; the component itself
          // does not need to know about it.
        />
      </div>
    );
  };

  // Preserve display name for easier debugging.
  const wrappedName = WrappedTree.displayName || WrappedTree.name || 'Component';
  IsolatedTree.displayName = `withTreeIsolation(${wrappedName})`;

  return IsolatedTree;
}