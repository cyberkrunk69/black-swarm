/**
 * Smart layout algorithm for positioning tree visualisations on the dashboard.
 *
 * This function calculates a grid based on the number of trees and distributes
 * them evenly across the available dashboard area. It respects any user‑defined
 * positions (saved in `tree.position` with a `user` flag) and only auto‑positions
 * trees that do not already have a saved location.
 *
 * Grid calculation:
 *   cols = ceil(sqrt(treeCount))
 *   rows = ceil(treeCount / cols)
 *
 * Each cell receives an equal share of the dashboard width/height.
 *
 * The function is deliberately defensive – if the dashboard element cannot be
 * found it falls back to the full window dimensions.
 */
function smartLayoutTrees() {
    // Retrieve all tree objects that need layout.
    // The surrounding codebase exposes a global `dashboard` object with a
    // `trees` array; adjust as necessary for the actual data source.
    const trees = (window.dashboard && window.dashboard.trees) || [];

    const treeCount = trees.length;
    if (treeCount === 0) {
        return; // nothing to layout
    }

    // Determine grid dimensions.
    const cols = Math.ceil(Math.sqrt(treeCount));
    const rows = Math.ceil(treeCount / cols);

    // Determine the available drawing area.
    const dashboardEl = document.getElementById('dashboard');
    const totalWidth = dashboardEl ? dashboardEl.clientWidth : window.innerWidth;
    const totalHeight = dashboardEl ? dashboardEl.clientHeight : window.innerHeight;

    // Compute each cell size.
    const cellWidth = Math.floor(totalWidth / cols);
    const cellHeight = Math.floor(totalHeight / rows);

    // Position each tree.
    let placed = 0;
    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (placed >= treeCount) {
                break;
            }

            const tree = trees[placed];

            // Preserve user customisations.
            // If a tree already has a saved position that is marked as a user
            // placement, we skip auto‑positioning it.
            const hasUserPos = tree.position && tree.position.user === true;
            if (!hasUserPos) {
                // Auto‑position the tree.
                const x = c * cellWidth;
                const y = r * cellHeight;

                // Update tree geometry. The exact property names depend on the
                // rest of the codebase; we use a common convention.
                tree.x = x;
                tree.y = y;
                tree.width = cellWidth;
                tree.height = cellHeight;

                // Mark the position as automatically generated so subsequent
                // calls can recognise it.
                tree.position = Object.assign({}, tree.position, {
                    auto: true,
                    x,
                    y,
                    width: cellWidth,
                    height: cellHeight
                });
            }

            placed++;
        }
    }

    // Trigger a re‑render if the surrounding framework requires it.
    if (window.dashboard && typeof window.dashboard.render === 'function') {
        window.dashboard.render();
    }
}

// Export for environments that use modules.
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        smartLayoutTrees
    };
}