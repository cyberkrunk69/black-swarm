/**
 * Workspace state management for handling multiple parallel task trees.
 *
 * Each tree is identified by a unique string key and tracks:
 *  - nodeCount: total number of nodes in the tree
 *  - scale: UI scaling factor for the tree view
 *  - collapsed: UI collapsed/expanded status of the tree
 *  - miniElement: a reference (e.g., DOM element or component) representing the tree’s mini‑map
 *
 * The module also provides helper functions required by the UI/UX specification:
 *    - getTreeRoots(): returns the identifiers (keys) of all registered trees.
 *    - getTreeNodes(): returns an array containing the metadata of every tree entry.
 *
 * This file is added under the experiment folder so it does not modify any core‑system files.
 */

type TreeMeta = {
    /** Number of nodes contained in the tree */
    nodeCount: number;
    /** UI scaling factor (e.g., zoom level) */
    scale: number;
    /** Whether the tree is currently collapsed in the UI */
    collapsed: boolean;
    /** Reference to a mini‑map element (could be a DOM node, React ref, etc.) */
    miniElement: any;
};

/**
 * Central registry for all parallel task trees in the current workspace.
 *
 * The map key is a unique identifier for the tree (e.g., a UUID or a user‑provided name).
 */
export const trees: Map<string, TreeMeta> = new Map();

/**
 * Register a new tree or update an existing one.
 *
 * @param id - Unique identifier for the tree.
 * @param meta - Metadata describing the tree.
 */
export function setTree(id: string, meta: TreeMeta): void {
    trees.set(id, meta);
}

/**
 * Remove a tree from the registry.
 *
 * @param id - Identifier of the tree to remove.
 */
export function deleteTree(id: string): void {
    trees.delete(id);
}

/**
 * Retrieve the identifiers of all registered tree roots.
 *
 * According to UIUX_INTERACTION_SPEC.md §5, a "tree root" is the entry point
 * for each parallel task tree. In this implementation the root is represented
 * by the map key.
 *
 * @returns An array of tree identifiers (root IDs).
 */
export function getTreeRoots(): string[] {
    return Array.from(trees.keys());
}

/**
 * Retrieve the metadata for every registered tree.
 *
 * This function is used by the UI layer to render mini‑maps,
 * compute aggregate statistics, etc.
 *
 * @returns An array of TreeMeta objects, one for each registered tree.
 */
export function getTreeNodes(): TreeMeta[] {
    return Array.from(trees.values());
}

/**
 * Convenience accessor to fetch a specific tree’s metadata.
 *
 * @param id - Identifier of the tree.
 * @returns The TreeMeta object if the tree exists; otherwise `undefined`.
 */
export function getTree(id: string): TreeMeta | undefined {
    return trees.get(id);
}