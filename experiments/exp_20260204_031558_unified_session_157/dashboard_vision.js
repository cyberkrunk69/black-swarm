/**
 * dashboard_vision.js
 *
 * This module contains utilities for arranging and visualising "trees" on the
 * dashboard.  The `smartLayoutTrees` function is responsible for automatically
 * positioning trees that do not already have a saved position while preserving
 * any user‑defined customisations.
 *
 * The layout algorithm:
 *   1. Determine the total number of trees.
 *   2. Compute the number of columns as `ceil(sqrt(treeCount))`.
 *   3. Compute the number of rows needed to accommodate all trees.
 *   4. Divide the available dashboard space evenly into a grid.
 *   5. Iterate over the trees:
 *        • If a tree already has a saved position (`tree.position`), leave it
 *          untouched (this respects user customisation).
 *        • Otherwise, assign it the centre of the next free grid cell.
 *
 * The function returns a new array of tree objects with updated `position`
 * properties.  It does **not** mutate the original objects unless they are
 * already being repositioned.
 */

const DASHBOARD_WIDTH = 1200;   // Default width of the dashboard canvas (px)
const DASHBOARD_HEIGHT = 800;   // Default height of the dashboard canvas (px)

/**
 * Automatically layout trees on the dashboard.
 *
 * @param {Array<Object>} trees - Array of tree objects. Each tree may contain:
 *   - `id` (string|number): Unique identifier.
 *   - `position` (Object|null): Existing saved position `{x: Number, y: Number}`.
 *   - `customPosition` (boolean): If true, the position was set by the user and
 *                                 must not be overridden.
 *
 * @returns {Array<Object>} A new array where trees lacking a saved position are
 *                          assigned coordinates that evenly fill the dashboard.
 *
 * The algorithm respects the following rules:
 *   • `cols = Math.ceil(Math.sqrt(treeCount))`.
 *   • Grid cells are sized to fill the whole dashboard width/height.
 *   • Trees are placed at the centre of their allocated cell.
 *   • Existing positions (including user‑customised ones) are preserved.
 */
function smartLayoutTrees(trees) {
    if (!Array.isArray(trees) || trees.length === 0) {
        return [];
    }

    const totalCount = trees.length;
    const cols = Math.ceil(Math.sqrt(totalCount));
    const rows = Math.ceil(totalCount / cols);

    // Size of each grid cell
    const cellWidth = DASHBOARD_WIDTH / cols;
    const cellHeight = DASHBOARD_HEIGHT / rows;

    // Helper to clone a tree (shallow copy is enough for our use‑case)
    const cloneTree = (tree) => Object.assign({}, tree);

    // Keep a running index for cells that will receive auto‑generated positions.
    let autoIndex = 0;

    // Produce a new array with updated positions.
    const positionedTrees = trees.map((originalTree) => {
        // Preserve any existing position (including user customisations).
        if (originalTree.position && typeof originalTree.position.x === 'number' && typeof originalTree.position.y === 'number') {
            // If the tree explicitly signals a custom position, we never touch it.
            if (originalTree.customPosition) {
                return cloneTree(originalTree);
            }
            // Position exists but is not marked as custom – we still keep it
            // because the user or a previous layout already decided where it belongs.
            return cloneTree(originalTree);
        }

        // No saved position – compute one based on the next free grid cell.
        const colIdx = autoIndex % cols;
        const rowIdx = Math.floor(autoIndex / cols);

        const x = colIdx * cellWidth + cellWidth / 2;
        const y = rowIdx * cellHeight + cellHeight / 2;

        const updatedTree = cloneTree(originalTree);
        updatedTree.position = { x, y };
        // Mark that this position was automatically generated.
        updatedTree.autoPositioned = true;

        autoIndex += 1;
        return updatedTree;
    });

    return positionedTrees;
}

// Export for use in other modules (CommonJS & ESModule compatibility)
if (typeof module !== 'undefined' && typeof module.exports !== 'undefined') {
    module.exports = {
        smartLayoutTrees,
        DASHBOARD_WIDTH,
        DASHBOARD_HEIGHT
    };
}
export { smartLayoutTrees, DASHBOARD_WIDTH, DASHBOARD_HEIGHT };