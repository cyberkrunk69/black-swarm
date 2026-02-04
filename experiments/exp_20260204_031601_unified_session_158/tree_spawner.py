"""
tree_spawner.py

Utility for spawning tree objects on a 2D grid while avoiding collisions.
Also provides a simple responsive layout helper that adapts the grid to
window resize events (compatible with pygame).

The module is deliberately self‑contained so it can be imported by the
experiment’s main script without touching any read‑only core files.
"""

from __future__ import annotations

import random
from typing import List, Tuple, Set

import pygame


# --------------------------------------------------------------------------- #
# Grid management
# --------------------------------------------------------------------------- #
class GridManager:
    """
    Manages a rectangular grid of cells. Each cell can hold at most one tree.
    The grid automatically rescales when the window size changes.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        rows: int = 20,
        cols: int = 20,
        margin: int = 10,
    ) -> None:
        """
        Parameters
        ----------
        screen: pygame.Surface
            The display surface – used to derive the current window size.
        rows, cols: int
            Desired number of rows and columns in the logical grid.
        margin: int
            Pixels between cells (both horizontal and vertical).
        """
        self.screen = screen
        self.rows = rows
        self.cols = cols
        self.margin = margin

        # Set of occupied cell coordinates (row, col)
        self.occupied: Set[Tuple[int, int]] = set()

        # Compute cell size based on the current window dimensions
        self._recalc_cell_size()

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #
    def is_occupied(self, row: int, col: int) -> bool:
        """Return True if the given cell already contains a tree."""
        return (row, col) in self.occupied

    def occupy(self, row: int, col: int) -> None:
        """Mark a cell as occupied. No safety checks – caller must ensure it's free."""
        self.occupied.add((row, col))

    def free(self, row: int, col: int) -> None:
        """Mark a cell as free (e.g., when a tree is removed)."""
        self.occupied.discard((row, col))

    def find_open_position(self, attempts: int = 100) -> Tuple[int, int] | None:
        """
        Randomly search for a free cell.

        Returns
        -------
        (row, col) tuple if a free cell is found, otherwise None.
        """
        free_cells = [
            (r, c)
            for r in range(self.rows)
            for c in range(self.cols)
            if not self.is_occupied(r, c)
        ]
        if not free_cells:
            return None

        # Randomly pick one of the free cells – optionally limit attempts
        # (the attempts argument is kept for compatibility with older code)
        return random.choice(free_cells)

    def spawn_tree(self, tree_group: pygame.sprite.Group) -> bool:
        """
        Create a new Tree sprite at a random free location and add it to the
        supplied sprite group.

        Returns
        -------
        True if the tree was spawned, False if the grid is full.
        """
        pos = self.find_open_position()
        if pos is None:
            return False

        row, col = pos
        tree = Tree(self, row, col)
        tree_group.add(tree)
        self.occupy(row, col)
        return True

    def handle_resize(self, new_width: int, new_height: int) -> None:
        """
        Called by the main loop when the pygame window is resized.
        Recalculates cell dimensions while preserving the logical grid size.
        """
        self._recalc_cell_size(new_width, new_height)

    # ------------------------------------------------------------------- #
    # Internal helpers
    # ------------------------------------------------------------------- #
    def _recalc_cell_size(self, width: int | None = None, height: int | None = None) -> None:
        """
        Compute the pixel size of each grid cell based on the current window size.
        """
        if width is None or height is None:
            width, height = self.screen.get_size()

        # Subtract margins that appear on both sides of the grid
        usable_w = max(0, width - (self.margin * (self.cols + 1)))
        usable_h = max(0, height - (self.margin * (self.rows + 1)))

        self.cell_w = usable_w // self.cols
        self.cell_h = usable_h // self.rows

    def cell_rect(self, row: int, col: int) -> pygame.Rect:
        """
        Return a pygame.Rect representing the pixel area for the given cell.
        """
        x = self.margin + col * (self.cell_w + self.margin)
        y = self.margin + row * (self.cell_h + self.margin)
        return pygame.Rect(x, y, self.cell_w, self.cell_h)


# --------------------------------------------------------------------------- #
# Tree sprite
# --------------------------------------------------------------------------- #
class Tree(pygame.sprite.Sprite):
    """
    Simple visual representation of a tree that occupies a single grid cell.
    """

    COLOR = (34, 139, 34)  # ForestGreen

    def __init__(self, grid: GridManager, row: int, col: int) -> None:
        super().__init__()
        self.grid = grid
        self.row = row
        self.col = col

        # Create a surface sized to the current cell dimensions
        self.image = pygame.Surface((grid.cell_w, grid.cell_h), pygame.SRCALPHA)
        self._draw_tree()

        # Position the sprite
        self.rect = self.grid.cell_rect(row, col)

    def _draw_tree(self) -> None:
        """Render a simple tree shape onto self.image."""
        w, h = self.image.get_size()
        # Draw a simple trunk
        trunk_w = max(2, w // 6)
        trunk_h = h // 3
        trunk_rect = pygame.Rect(
            (w - trunk_w) // 2,
            h - trunk_h,
            trunk_w,
            trunk_h,
        )
        pygame.draw.rect(self.image, (101, 67, 33), trunk_rect)

        # Draw foliage (circle)
        foliage_radius = min(w, h) // 3
        foliage_center = (w // 2, h - trunk_h)
        pygame.draw.circle(self.image, self.COLOR, foliage_center, foliage_radius)

    def update(self, *args, **kwargs) -> None:
        """
        Called each frame. If the window has been resized, the cell dimensions
        may have changed – we need to rebuild the image and rect.
        """
        # Detect size change
        expected_w, expected_h = self.grid.cell_w, self.grid.cell_h
        if self.image.get_size() != (expected_w, expected_h):
            self.image = pygame.Surface((expected_w, expected_h), pygame.SRCALPHA)
            self._draw_tree()
            self.rect = self.grid.cell_rect(self.row, self.col)


# --------------------------------------------------------------------------- #
# Example usage (can be imported and called from the experiment's main script)
# --------------------------------------------------------------------------- #
def run_demo():
    """
    Minimal demo that opens a resizable pygame window,
    spawns trees on click, and demonstrates collision‑free placement.
    """
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("Tree Spawner Demo – Collision‑Free Grid")

    clock = pygame.time.Clock()
    grid = GridManager(screen, rows=15, cols=20, margin=8)
    trees = pygame.sprite.Group()

    # Pre‑populate a few trees
    for _ in range(30):
        grid.spawn_tree(trees)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                # Resize the display surface
                screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                grid.handle_resize(*event.size)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left‑click tries to add a new tree
                grid.spawn_tree(trees)

        # Update sprites (handle possible cell‑size changes)
        trees.update()

        # Draw
        screen.fill((135, 206, 235))  # Light sky blue background
        trees.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run_demo()