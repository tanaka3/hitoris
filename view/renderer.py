import pyxel
import math
from config import Config

class Renderer:
    """ゲーム要素の描画を担当するクラス"""
    
    # ブロックのサイズ
    BLOCK_SIZE = 10
    
    # テトロミノ画像のサイズ
    TETROMINO_IMG_SIZE = 16
    
    # ボードの描画位置
    BOARD_X = 70  # 画面中央にボードがくるように配置
    BOARD_Y = 20
    
    # ボードのサイズ計算
    BOARD_WIDTH = 10 * BLOCK_SIZE  # 10ブロック分の幅
    BOARD_HEIGHT = 20 * BLOCK_SIZE  # 20ブロック分の高さ
    
    # ホールド領域の描画位置とサイズ
    HOLD_WIDTH = 5 * BLOCK_SIZE
    HOLD_HEIGHT = 5 * BLOCK_SIZE
    HOLD_X = 10  # 画面左側に配置
    HOLD_Y = 50
    
    # ネクスト領域の描画位置とサイズ
    NEXT_WIDTH = 5 * BLOCK_SIZE
    NEXT_HEIGHT = 10 * BLOCK_SIZE  # 2つのテトロミノ分の高さ
    NEXT_X = Config.SCREEN_WIDTH - 10 - NEXT_WIDTH  # 画面右側に配置
    NEXT_Y = 50

    CAMERA_TETROMINO_X = 405
    CAMERA_TETROMINO_Y = 25
    
    @staticmethod
    def initialize():
        """リソースを初期化する"""
        # pyxresファイルがまだロードされていない場合はロード
        # 注: メインのinitで既にロードされている場合は不要
        try:
            # 既にロードされているか確認
            if not hasattr(pyxel, 'image'):
                pyxel.load("hitoris.pyxres")
        except:
            print("Warning: Could not load hitoris.pyxres")
    
    @staticmethod
    def draw_block(x, y, color):
        """ブロックを描画する（カラーのみ使用する場合のフォールバック）"""
        size = Renderer.BLOCK_SIZE
        pyxel.rect(x, y, size, size, color)
        pyxel.rect(x + 1, y + 1, size - 2, size - 2, color)
    
    @staticmethod
    def draw_block_from_image(x, y, tetromino_type, is_ghost=False):
        """画像からブロックを描画する"""
        # テトロミノ画像の位置を計算
        img_x = 0 if is_ghost else 16 + tetromino_type * 16  # 各テトロミノは16pxごとに配置
        img_y = 16 if is_ghost else 0     # ゴースト画像は y=16 の位置

        # 画像からブロックを描画
        pyxel.blt(
            x, y,                          # 描画位置 
            0,                             # イメージバンク
            img_x + 3, img_y + 3,          # 画像内の位置
            Renderer.BLOCK_SIZE,           # 横幅
            Renderer.BLOCK_SIZE,           # 高さ
            1                              # 透明色 (カラー1)
        )
    
    @staticmethod
    def draw_tetromino(tetromino, offset_x, offset_y, scale=1.0, is_ghost=False):
        """テトロミノを描画する"""
        if tetromino is None:
            return

        shape = tetromino.get_shape()
        size = Renderer.BLOCK_SIZE * scale

        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x] != 0:
                    block_x = offset_x + x * size
                    block_y = offset_y + y * size
                    
                    # 画像からブロックを描画
                    Renderer.draw_block_from_image(
                        block_x, block_y, 
                        tetromino.type, 
                        is_ghost
                    )

    @staticmethod
    def draw_board(board):
        """ゲームボードを描画する"""
        # ボードの背景
        board_width = board.width * Renderer.BLOCK_SIZE
        board_height = board.height * Renderer.BLOCK_SIZE
        pyxel.rectb(Renderer.BOARD_X - 1, Renderer.BOARD_Y - 1, 
                   board_width + 2, board_height + 2, 7)
        
        pyxel.rect(Renderer.BOARD_X, Renderer.BOARD_Y, 
                   board_width, board_height, 0)
        
        # ボードのグリッドを描画
        for y in range(board.height):
            for x in range(board.width):
                block_value = board.grid[y][x]
                if block_value != 0:
                    block_x = Renderer.BOARD_X + x * Renderer.BLOCK_SIZE
                    block_y = Renderer.BOARD_Y + y * Renderer.BLOCK_SIZE
                    
                    # block_value - 1をテトロミノタイプとして使用
                    # 0はボードの空白のため、実際のタイプは1始まり
                    tetromino_type = block_value - 1
                    Renderer.draw_block_from_image(block_x, block_y, tetromino_type)
                    
    @staticmethod
    def draw_current_tetromino(tetromino, board):
        """現在操作中のテトロミノを描画する"""
        if tetromino is None:
            return
            
        shape = tetromino.get_shape()
        
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x] != 0:
                    block_x = Renderer.BOARD_X + (tetromino.x + x) * Renderer.BLOCK_SIZE
                    block_y = Renderer.BOARD_Y + (tetromino.y + y) * Renderer.BLOCK_SIZE
                    Renderer.draw_block_from_image(block_x, block_y, tetromino.type)
                    
    @staticmethod
    def draw_ghost_tetromino(tetromino, board):
        """ゴーストテトロミノ（着地位置のプレビュー）を描画する"""
        if tetromino is None:
            return
            
        # 現在のテトロミノの位置を保存
        original_y = tetromino.y
        ghost_y = original_y
        
        # ゴーストテトロミノを一番下まで落とす
        while True:
            ghost_y += 1
            
            # テトロミノの仮の位置を設定
            tetromino.y = ghost_y
            
            # 位置が無効なら一つ上に戻す
            if not board.is_valid_position(tetromino):
                ghost_y -= 1
                break
                
        # 元の位置に戻す
        tetromino.y = original_y
        
        # ゴーストテトロミノを描画
        shape = tetromino.get_shape()
        
        for y in range(len(shape)):
            for x in range(len(shape[y])):
                if shape[y][x] != 0:
                    block_x = Renderer.BOARD_X + (tetromino.x + x) * Renderer.BLOCK_SIZE
                    block_y = Renderer.BOARD_Y + (ghost_y + y) * Renderer.BLOCK_SIZE
                    
                    # ゴーストテトロミノを画像から描画
                    Renderer.draw_block_from_image(block_x, block_y, tetromino.type, is_ghost=True)
                    
    @staticmethod
    def draw_hold(hold_tetromino):
        """ホールドテトロミノを描画する"""
        # ホールド領域の背景
        pyxel.rectb(Renderer.HOLD_X - 1, Renderer.HOLD_Y - 1, 
                   Renderer.HOLD_WIDTH + 2, Renderer.HOLD_HEIGHT + 2, 7)
        pyxel.rect(Renderer.HOLD_X, Renderer.HOLD_Y, 
                   Renderer.HOLD_WIDTH, Renderer.HOLD_HEIGHT, 0)  # 背景を黒に設定
        
        text = "HOLD"
        pyxel.text(Renderer.HOLD_X +  +  (Renderer.HOLD_WIDTH + 2 - len(text) * 4) /2, Renderer.HOLD_Y - 10, text, 7)
        
        if hold_tetromino is not None:
            # テトロミノを中央に配置するためのオフセット計算
            tetromino_width = hold_tetromino.get_width()
            tetromino_height = hold_tetromino.get_height()
            
            # 枠の中心を計算
            center_x = Renderer.HOLD_X + Renderer.HOLD_WIDTH / 2
            center_y = Renderer.HOLD_Y + Renderer.HOLD_HEIGHT / 2
            
            # テトロミノの左上座標を計算（中心から半分のサイズを引く）
            offset_x = center_x - (tetromino_width * Renderer.BLOCK_SIZE) / 2
            offset_y = center_y - (tetromino_height * Renderer.BLOCK_SIZE) / 2
            
            # ホールドテトロミノを描画
            Renderer.draw_tetromino(hold_tetromino, offset_x, offset_y, 1.0)
                    
    @staticmethod
    def draw_next(next_tetrominos):
        """次のテトロミノを描画する"""
        # ネクスト領域の背景
        pyxel.rectb(Renderer.NEXT_X - 1, Renderer.NEXT_Y - 1, 
                   Renderer.NEXT_WIDTH + 2, Renderer.NEXT_HEIGHT + 2, 7)
        pyxel.rect(Renderer.NEXT_X, Renderer.NEXT_Y, 
                   Renderer.NEXT_WIDTH, Renderer.NEXT_HEIGHT, 0)  # 背景を黒に設定
        text = "NEXT"
        pyxel.text(Renderer.NEXT_X +  (Renderer.NEXT_WIDTH + 2 - len(text) * 4) /2, Renderer.NEXT_Y - 10, text, 7)
        
        # 次の2つのテトロミノを描画
        for i, tetromino in enumerate(next_tetrominos[:2]):
            if tetromino is None:
                continue
                
            # テトロミノを中央に配置するためのオフセット計算
            tetromino_width = tetromino.get_width()
            tetromino_height = tetromino.get_height()
            
            # 各ネクスト枠の中心を計算（5ブロック×5ブロックの領域の中心）
            center_x = Renderer.NEXT_X + Renderer.NEXT_WIDTH / 2
            center_y = Renderer.NEXT_Y + (i * 5 + 2.5) * Renderer.BLOCK_SIZE
            
            # テトロミノの左上座標を計算（中心から半分のサイズを引く）
            offset_x = center_x - (tetromino_width * Renderer.BLOCK_SIZE) / 2
            offset_y = center_y - (tetromino_height * Renderer.BLOCK_SIZE) / 2
            
            # ネクストテトロミノを描画
            Renderer.draw_tetromino(tetromino, offset_x, offset_y, 1.0)
    
    @staticmethod
    def draw_score(score, level, lines):
        """スコア情報を描画する"""
        pyxel.text(10, 150, f"SCORE: {score}", 7)
        pyxel.text(10, 160, f"LEVEL: {level}", 7)
        pyxel.text(10, 170, f"LINES: {lines}", 7)
    
    
    @staticmethod
    def draw_game_over(score, level, lines):
        """ゲームオーバー表示を描画する"""
        # 背景を描画（単色の長方形）
        pyxel.rect(0, 95, pyxel.width, 50, 1) 

        text = "GAME OVER"
        pyxel.text((pyxel.width - len(text) * 4)/2, 103, text, 8)

        text = f"SCORE: {score}"
        pyxel.text((pyxel.width - len(text) * 4)/2, 118, text, 7)

        text = "PRESS ANY BUTTON TO CONTINUE"
        pyxel.text((pyxel.width - len(text) * 4)/2, 133, text, 7)


    @staticmethod
    def draw_autoplay():
        # 背景を描画（単色の長方形）
        pyxel.rect(0, 0, pyxel.width, 10, 8)

        text = "DEMO MODE"
        pyxel.text((pyxel.width - len(text) * 4)/2, 3, text, 7)

        pyxel.rect(0,  pyxel.height - 10, pyxel.width, 10, 8)

        text = "AUTO PLAY"        
        pyxel.text((pyxel.width - len(text) * 4)/2, pyxel.height -7, text, 7)     

    @staticmethod
    def draw_camera(camera=None, shutter = 0):
        if camera == None:
            return
        
        offset_x = 260
        offset_y = 20
        frame = camera.get_frame()

        if frame is not None:
            reduced = frame >> 2
            r = reduced[:, :, 0]
            g = reduced[:, :, 1]
            b = reduced[:, :, 2]
            indexed = camera.color_lut[r, g, b]

            for y in range(200):
                for x in range(200):
                    pyxel.pset(offset_x + x, offset_y + y, int(indexed[y, x]))

        pyxel.rectb(offset_x - 2, offset_y - 2, 202, 202, 7)

        # 認識しているテトロミノを表示
        tetromino = camera.get_tetromino()
    
        pyxel.rectb(Renderer.CAMERA_TETROMINO_X - 1, Renderer.CAMERA_TETROMINO_Y - 1, 
                    Renderer.HOLD_WIDTH + 2, Renderer.HOLD_HEIGHT + 2, 7)
        pyxel.dither(0.5)
        pyxel.rect(Renderer.CAMERA_TETROMINO_X, Renderer.CAMERA_TETROMINO_Y, 
                    Renderer.HOLD_WIDTH, Renderer.HOLD_HEIGHT, 0)  # 背景を黒に設定
        pyxel.dither(1.0)

        if tetromino is not None:

            # テトロミノを中央に配置するためのオフセット計算
            tetromino_width = tetromino.get_width()
            tetromino_height = tetromino.get_height()
            
            # 枠の中心を計算
            center_x = Renderer.CAMERA_TETROMINO_X + Renderer.HOLD_WIDTH / 2
            center_y = Renderer.CAMERA_TETROMINO_Y + Renderer.HOLD_HEIGHT / 2
            
            # テトロミノの左上座標を計算（中心から半分のサイズを引く）
            offset_x = center_x - (tetromino_width * Renderer.BLOCK_SIZE) / 2
            offset_y = center_y - (tetromino_height * Renderer.BLOCK_SIZE) / 2
            
            # ホールドテトロミノを描画
            Renderer.draw_tetromino(tetromino, offset_x, offset_y, 1.0)

            if shutter > 0:
                alpha = 1 - math.sin(math.pi * shutter / 60)
                pyxel.dither(alpha)
                pyxel.rect(259, 19, Config.CAMERA_VIEW_WIDTH, Config.CAMERA_VIEW_HEIGHT, 7)  # 背景を黒に設定
                pyxel.dither(1.0)

        # 認識しているボックスを表示
        boxs = camera.get_boxes()
        if boxs is not None:
            offset_x = (Config.CAMERA_WIDTH - Config.CAMERA_VIEW_WIDTH ) / 2
            offset_y = (Config.CAMERA_HEIGHT - Config.CAMERA_VIEW_HEIGHT ) /2
            for box in boxs:
                x, y, w, h = box
                x  = x  - offset_x
                if x < 0:
                    x = 0
                y = y  - offset_y
                if y < 0:
                    y = 0
                w = w 
                h = h 
                if x + w > Config.CAMERA_VIEW_WIDTH:
                    w = w - (x + w -Config.CAMERA_VIEW_WIDTH)
                if y + h > Config.CAMERA_VIEW_HEIGHT:
                    h = h - (y + h -Config.CAMERA_VIEW_HEIGHT)

                pyxel.rectb(260 + x, 20 + y, w, h, 3)

        # ラベルの描画
        label = camera.get_labels()
        if label is not None:

            pyxel.dither(0.5)
            pyxel.rect(260, Config.CAMERA_VIEW_HEIGHT -4, Config.CAMERA_VIEW_WIDTH, 12, 0)  # 背景を黒に設定
            pyxel.dither(1.0)

            pyxel.text(259 + (Config.CAMERA_VIEW_WIDTH -len(label) * 4) / 2 , Config.CAMERA_VIEW_HEIGHT , label, 7)
