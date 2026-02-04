/**
 * Workspace state management for parallel task trees.
 *
 * This module introduces a `trees` map on the workspace state to keep track of
 * multiple independent task trees that can be rendered in the UI.  Each entry
 * records:
 *   - `nodeCount`: total number of nodes in the tree
 *   - `scale`: UI scaling factor for the tree visualisation
 *   - `collapsed`: whether the tree is currently collapsed in the UI
 *   - `miniElement`: a reference to the miniature UI element representing the tree
 *   - `rootId`: the identifier of the root node for quick lookup
 *
 * Two helper functions are provided:
 *   - `getTreeRoots()` – returns an array of root node identifiers for all
 *     registered trees.
 *   - `getTreeNodes(treeId)` – returns a list of node identifiers belonging to
 *     the specified tree.  For demonstration purposes this implementation assumes
 *     that node IDs are sequential integers starting at the root ID.
 *
 * The implementation is deliberately lightweight and framework‑agnostic so it
 * can be imported from any UI layer (React, Vue, plain JS, etc.).
 */

type TreeId = string;

/**
 * Information stored for each parallel task tree.
 */
export interface TreeInfo {
  /** Unique identifier of the root node for this tree */
  rootId: number;
  /** Total number of nodes contained in the tree */
  nodeCount: number;
  /** UI scaling factor (e.g., for zoom) */
  scale: number;
  /** Whether the tree UI is collapsed */
  collapsed: boolean;
  /** Reference to the miniature UI element (could be a DOM element, React ref, etc.) */
  miniElement: any;
}

/**
 * Workspace state singleton.
 *
 * The `trees` map is the central registry for all parallel task trees.
 */
export class WorkspaceState {
  /** Map from a tree identifier to its metadata */
  private static trees: Map<TreeId, TreeInfo> = new Map();

  /**
   * Register a new task tree or update an existing one.
   *
   * @param id        Unique identifier for the tree.
   * @param info      Metadata describing the tree.
   */
  static setTree(id: TreeId, info: TreeInfo): void {
    WorkspaceState.trees.set(id, info);
  }

  /**
   * Remove a tree from the registry.
   *
   * @param id  Identifier of the tree to remove.
   */
  static deleteTree(id: TreeId): void {
    WorkspaceState.trees.delete(id);
  }

  /**
   * Retrieve the stored information for a specific tree.
   *
   * @param id  Tree identifier.
   * @returns   TreeInfo if present, otherwise undefined.
   */
  static getTreeInfo(id: TreeId): TreeInfo | undefined {
    return WorkspaceState.trees.get(id);
  }

  /**
   * Get the root node identifiers for all registered trees.
   *
   * @returns An array of root node IDs.
   */
  static getTreeRoots(): number[] {
    const roots: number[] = [];
    for (const info of WorkspaceState.trees.values()) {
      roots.push(info.rootId);
    }
    return roots;
  }

  /**
   * Get the list of node identifiers belonging to a particular tree.
   *
   * This implementation assumes node IDs are sequential integers beginning
   * with the `rootId`.  If a more sophisticated graph structure is required,
   * replace this logic with a real traversal of the underlying data model.
   *
   * @param id  Tree identifier.
   * @returns   Array of node IDs, or an empty array if the tree does not exist.
   */
  static getTreeNodes(id: TreeId): number[] {
    const info = WorkspaceState.trees.get(id);
    if (!info) {
      return [];
    }

    const nodes: number[] = [];
    for (let i = 0; i < info.nodeCount; i++) {
      nodes.push(info.rootId + i);
    }
    return nodes;
  }

  /**
   * Retrieve the entire map of trees (read‑only).
   *
   * @returns A shallow copy of the internal Map.
   */
  static getAllTrees(): Map<TreeId, TreeInfo> {
    return new Map(WorkspaceState.trees);
  }
}

/* Export a default instance for convenience */
export default WorkspaceState;