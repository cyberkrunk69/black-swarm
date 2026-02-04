"""
tree_placement.py
-----------------

Utility module for spawning tree nodes on a 2‑D grid without overlap.
It provides:

* ``Grid`` – a simple occupancy grid that tracks placed nodes.
* ``find_open_cell`` – returns a random free cell or ``None`` when the grid is full.
* ``spawn_tree`` – high‑level helper that creates a tree data‑structure at an
  available location, guaranteeing no collisions.
* ``handle_window_resize`` – recomputes the grid dimensions when the browser
  window (or canvas) size changes, preserving already‑placed trees whenever
  possible.

The implementation is deliberately framework‑agnostic – it works with any UI
layer (e.g. vanilla JS canvas, React, PyQt, etc.) that can call the exposed
functions and pass the required size information.
"""

from __future__ import annotations

import random
from typing import List, Optional, Tuple, Dict

# Type alias for a coordinate on the grid
Coord = Tuple[int, int]

class Grid:
    """
    Represents a rectangular occupancy grid.

    Parameters
    ----------
    width_px : int
        Width of the drawing area in pixels.
    height_px : int
        Height of the drawing area in pixels.
    cell_size_px : int
        Desired size of a single grid cell (both width and height).  The grid
        will be automatically sized to the nearest whole number of cells that
        fit inside the supplied dimensions.
    """

    def __init__(self, width_px: int, height_px: int, cell_size_px: int = 64):
        if cell_size_px <= 0:
            raise ValueError("cell_size_px must be > 0")
        self.cell_size = cell_size_px
        self.update_dimensions(width_px, height_px)

    # --------------------------------------------------------------------- #
    # Public API
    # --------------------------------------------------------------------- #
    def update_dimensions(self, width_px: int, height_px: int) -> None:
        """
        Re‑calculate the number of rows/columns based on a new window size.
        Existing occupied cells are retained if they still fit; otherwise
        they are discarded (the caller can decide how to handle loss).

        Parameters
        ----------
        width_px, height_px : int
            New pixel dimensions of the container.
        """
        self.cols = max(1, width_px // self.cell_size)
        self.rows = max(1, height_px // self.cell_size)

        # Create a fresh occupancy matrix; preserve cells that are still valid
        new_occupied: List[List[bool]] = [
            [False for _ in range(self.cols)] for _ in range(self.rows)
        ]

        # Copy over any previously occupied cells that still lie within bounds
        for r in range(min(self.rows, len(self._occupied))):
            for c in range(min(self.cols, len(self._occupied[0]))):
                new_occupied[r][c] = self._occupied[r][c]

        self._occupied = new_occupied

    def is_occupied(self, coord: Coord) -> bool:
        """Return True if the given cell is already taken."""
        r, c = coord
        return self._occupied[r][c]

    def occupy(self, coord: Coord) -> None:
        """Mark a cell as taken."""
        r, c = coord
        self._occupied[r][c] = True

    def free(self, coord: Coord) -> None:
        """Mark a cell as free."""
        r, c = coord
        self._occupied[r][c] = False

    def all_free_cells(self) -> List[Coord]:
        """Return a list of every free cell coordinate."""
        free_cells: List[Coord] = []
        for r in range(self.rows):
            for c in range(self.cols):
                if not self._occupied[r][c]:
                    free_cells.append((r, c))
        return free_cells

    # --------------------------------------------------------------------- #
    # Helper utilities
    # --------------------------------------------------------------------- #
    def cell_to_pixel(self, coord: Coord) -> Tuple[int, int]:
        """Convert a grid coordinate to the top‑left pixel of that cell."""
        r, c = coord
        return (c * self.cell_size, r * self.cell_size)

    def pixel_to_cell(self, x: int, y: int) -> Coord:
        """Convert a pixel position to the containing grid cell."""
        return (y // self.cell_size, x // self.cell_size)

# ------------------------------------------------------------------------- #
# High‑level spawning helpers
# ------------------------------------------------------------------------- #

def find_open_cell(grid: Grid) -> Optional[Coord]:
    """
    Return a random free cell from ``grid``.  If the grid is full, ``None`` is
    returned.
    """
    free_cells = grid.all_free_cells()
    if not free_cells:
        return None
    return random.choice(free_cells)


def spawn_tree(grid: Grid, tree_factory) -> Optional[Dict]:
    """
    Attempt to place a new tree on the grid.

    Parameters
    ----------
    grid : Grid
        The occupancy grid that tracks current nodes.
    tree_factory : Callable[[int, int], Any]
        A callable that receives the pixel ``(x, y)`` of the top‑left corner of
        the chosen cell and returns a tree representation (e.g. a dict, a UI
        component, etc.).

    Returns
    -------
    dict or None
        The newly created tree object, or ``None`` if no free space exists.
    """
    cell = find_open_cell(grid)
    if cell is None:
        # No room left on the grid
        return None

    # Mark the cell as occupied *before* creating the tree to guarantee atomicity
    grid.occupy(cell)

    # Convert to pixel coordinates for the factory
    x, y = grid.cell_to_pixel(cell)
    tree = tree_factory(x, y)

    # Attach metadata useful for later removal / repositioning
    if isinstance(tree, dict):
        tree['_grid_coord'] = cell
    else:
        # Fallback: try to set an attribute if the object permits it
        try:
            setattr(tree, '_grid_coord', cell)
        except Exception:
            pass

    return tree


def handle_window_resize(grid: Grid, new_width_px: int, new_height_px: int) -> None:
    """
    Public helper to be called from UI code when the container size changes.
    It updates the internal grid dimensions while preserving already‑occupied
    cells that still fit.

    Parameters
    ----------
    grid : Grid
        The grid instance used for tree placement.
    new_width_px, new_height_px : int
        New pixel dimensions of the container.
    """
    grid.update_dimensions(new_width_px, new_height_px)

# ------------------------------------------------------------------------- #
# Example factory (for documentation / quick‑testing purposes)
# ------------------------------------------------------------------------- #

def example_tree_factory(x: int, y: int) -> Dict:
    """
    Simple factory that creates a dictionary representing a tree.
    In a real application this would likely instantiate a UI widget or a
    data‑model object.
    """
    return {
        "type": "tree",
        "position_px": (x, y),
        "size_px": (grid.cell_size, grid.cell_size)  # placeholder, assumes square cells
    }

# ------------------------------------------------------------------------- #
# Example usage (not executed on import)
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    # Simulate a 800x600 canvas with 64‑px cells
    grid = Grid(width_px=800, height_px=600, cell_size_px=64)

    # Spawn 10 trees
    for i in range(10):
        tree = spawn_tree(grid, lambda x, y: {"id": i, "pos": (x, y)})
        if tree is None:
            print("No more free cells!")
            break
        print(f"Spawned tree {tree}")

    # Resize the window
    handle_window_resize(grid, new_width_px=1024, new_height_px=768)
    print(f"Grid after resize: {grid.rows} rows × {grid.cols} cols")