"""Classes da grade e das células usadas pelo Tetris."""
from abc import ABC, abstractmethod
import pygame


class obj(ABC):
    def __init__(self, x, y, sprites=None):
        self.x, self.y = x, y
        self.sprites = sprites or []

    @abstractmethod
    def draw(self, screen): pass

    @abstractmethod
    def update(self, dt): pass


class Cell(obj):
    """Uma célula da matriz; sua cor representa o estado livre/ocupado."""
    def __init__(self, x, y, size):
        super().__init__(x, y)
        self.size, self.color = size, None

    def draw(self, screen, color=None, ghost=False, flash=False):
        color = color or self.color
        rect = pygame.Rect(self.x+1, self.y+1, self.size-2, self.size-2)
        if color is None:
            pygame.draw.rect(screen, (26,28,52), rect)
            pygame.draw.rect(screen, (47,51,82), rect, 1)
        elif ghost:
            pygame.draw.rect(screen, color, rect, 2, border_radius=3)
        else:
            if flash: color = tuple(min(255, c+100) for c in color)
            pygame.draw.rect(screen, color, rect, border_radius=3)
            pygame.draw.line(screen, (255,255,255), (rect.left+3,rect.top+3), (rect.right-3,rect.top+3), 2)
            shade = tuple(max(0,c-60) for c in color)
            pygame.draw.line(screen, shade, (rect.right-2,rect.top+3), (rect.right-2,rect.bottom-2), 3)

    def update(self, dt): pass


class Grid(obj):
    """Matriz 10x20 que controla colisões, fixação e linhas completas."""
    def __init__(self, x, y, grid_size=(10,20), cell_size=25):
        super().__init__(x, y)
        self.columns, self.rows = grid_size
        self.cell_size = cell_size
        self.cells = [[Cell(x+col*cell_size, y+row*cell_size, cell_size)
                       for col in range(self.columns)] for row in range(self.rows)]

    def reset(self):
        for row in self.cells:
            for cell in row: cell.color = None

    def positions(self, piece, shape=None, dx=0, dy=0):
        shape = shape or piece.shape
        return [(piece.x+col+dx, piece.y+row+dy) for row,line in enumerate(shape)
                for col,value in enumerate(line) if value]

    def valid(self, piece, shape=None, dx=0, dy=0):
        for col,row in self.positions(piece,shape,dx,dy):
            if col<0 or col>=self.columns or row>=self.rows: return False
            if row>=0 and self.cells[row][col].color is not None: return False
        return True

    def lock(self, piece):
        above = False
        for col,row in self.positions(piece):
            if row<0: above=True
            else: self.cells[row][col].color=piece.color
        return above

    def full_lines(self):
        return [row for row,cells in enumerate(self.cells) if all(cell.color for cell in cells)]

    def clear_lines(self, lines):
        colors=[[cell.color for cell in row] for row in self.cells]
        for row in reversed(lines): colors.pop(row)
        colors=[[None]*self.columns for _ in lines]+colors
        for row,values in enumerate(colors):
            for col,color in enumerate(values): self.cells[row][col].color=color

    def draw(self, screen, piece=None, flashing=(), flash=False):
        border=pygame.Rect(self.x-8,self.y-8,self.columns*self.cell_size+16,self.rows*self.cell_size+16)
        pygame.draw.rect(screen,(18,20,39),border,border_radius=6)
        for row in self.cells:
            for cell in row:
                cell.draw(screen,flash=flash and (cell.y-self.y)//self.cell_size in flashing)
        if piece is None: return
        drop=0
        while self.valid(piece,dy=drop+1): drop+=1
        for col,row in self.positions(piece,dy=drop):
            if row>=0: self.cells[row][col].draw(screen,piece.color,ghost=True)
        for col,row in self.positions(piece):
            if row>=0: self.cells[row][col].draw(screen,piece.color)

    def update(self, dt):
        for row in self.cells:
            for cell in row: cell.update(dt)
