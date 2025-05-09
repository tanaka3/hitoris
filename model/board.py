import pyxel
from view.game_view import GameView
        
class Board:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
    
    def clear(self):
        """ボードをクリアする"""
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
    
    def is_valid_position(self, tetromino):
        """テトロミノの位置が有効かどうかをチェック"""
        shape = tetromino.get_shape()
        
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x] == 0:
                    continue  # 空のセルはスキップ
                
                # テトロミノのグリッド上の位置
                board_x = tetromino.x + x
                board_y = tetromino.y + y
                
                # ボードの外側にはみ出していないかチェック
                if (board_x < 0 or board_x >= self.width or
                    board_y < 0 or board_y >= self.height):
                    return False
                
                # 他のブロックと重なっていないかチェック
                if board_y >= 0 and self.grid[board_y][board_x] != 0:
                    return False
        
        return True
    
    def lock_tetromino(self, tetromino):
        """テトロミノをボードに固定する"""
        shape = tetromino.get_shape()
        # tetromino.type + 1 をセルに格納（0は空白を表すため）
        tetromino_type = tetromino.type + 1
        
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x] == 0:
                    continue  # 空のセルはスキップ
                
                board_x = tetromino.x + x
                board_y = tetromino.y + y
                
                if 0 <= board_y < self.height and 0 <= board_x < self.width:
                    self.grid[board_y][board_x] = tetromino_type
        
    def is_line_full(self, y):
        """指定した行が埋まっているかチェック"""
        return all(self.grid[y][x] != 0 for x in range(self.width))
    
    def clear_line(self, y):
        """指定した行を消去し、上の行を下に移動"""
        for row in range(y, 0, -1):
            self.grid[row] = self.grid[row - 1][:]
        
        # 最上段を空にする
        self.grid[0] = [0 for _ in range(self.width)]
    
    def clear_lines(self):
        """埋まった行を消去し、消去した行数を返す"""
        lines_cleared = 0
        cleared_lines = []
        
        for y in range(self.height - 1, -1, -1):
            if self.is_line_full(y):
                cleared_lines.append(y)
                lines_cleared += 1
        
        # エフェクトのためにゲームビューに通知
        if hasattr(pyxel, 'APP') and hasattr(pyxel.APP, 'game_view'):
            pyxel.APP.game_view.add_line_clear_effect(cleared_lines)
            
        # 実際に行を消去
        for y in sorted(cleared_lines):
            self.clear_line(y)
            
        return lines_cleared
