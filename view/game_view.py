import pyxel
import math
import random
from config import Config
from view.renderer import Renderer

class GameView:
    
    ENABLE_PARTICLES = True  # パーティクルエフェクトを有効にするかどうか

    def __init__(self):
        # ライン消去エフェクト用の変数
        self.line_clear_effect = []
        self.particles = []
        
    def draw(self, game, camera = None):
        """ゲーム画面を描画する"""
        # 背景
        pyxel.cls(0)
        
        # 背景グリッド
        self._draw_background_grid()
        
        # ボードを描画
        Renderer.draw_board(game.board)

        # ライン消去エフェクトを描画
        self._draw_line_clear_effect()
        
        # パーティクルエフェクトを描画
        self._draw_particles()
        
        # ホールドテトロミノを描画
        Renderer.draw_hold(game.hold_tetromino)
        
        # ネクストテトロミノを描画
        Renderer.draw_next(game.next_tetrominos)

        if Config.CAMERA and not camera == None:
            Renderer.draw_camera(camera, game.shutter_count)

        # スコア情報を描画
        Renderer.draw_score(game.score, game.level, game.lines_cleared)
        
        # カウントダウンが有効な場合はカウントダウンを表示
        if game.countdown_active:
            self._draw_countdown(game.countdown_timer)
        else:
            # ゴーストテトロミノを描画
            if Config.GHOST:
                if game.current_tetromino is not None and not game.is_game_over:
                    Renderer.draw_ghost_tetromino(game.current_tetromino, game.board)
            
            # 現在のテトロミノを描画
            if game.current_tetromino is not None and not game.is_game_over:
                Renderer.draw_current_tetromino(game.current_tetromino, game.board)
        
        # ゲームオーバー時の表示
        if game.game_over_triggered:
            Renderer.draw_game_over(game.score, game.level, game.lines_cleared)
            
        # コンボや消去エフェクトのテキストを表示
        if game.effect_timer > 0:
            text_x = (240 - len(game.effect_text) * 4)//2
            text_y = 120
            # テキストを少し揺らす
            if game.effect_timer > 45:
                shake = random.randint(-1, 1)
                text_x += shake
                text_y += shake
                
            # テキストの影を描画
            pyxel.text(text_x + 1, text_y + 1, game.effect_text, 0)
            # テキストを描画
            pyxel.text(text_x, text_y, game.effect_text, game.effect_color)
        else:
            game.effect_text = ""
            
    
    def _draw_background_grid(self):
        """背景のグリッドを描画"""
        # 背景グリッド (少し暗めに)
        for x in range(0, pyxel.width, 15):
            pyxel.line(x, 0, x, pyxel.height, 1)
        for y in range(0, pyxel.height, 15):
            pyxel.line(0, y, pyxel.width, y, 1)

    def _draw_countdown(self, timer):
        """開始エフェクトを描画"""

        b = math.log(8) / 60  # ln(4) / 60
        scale =  (math.exp(b * (60 - timer % 60)) - 1)
        
        # 画面中央の座標
        center_x = pyxel.width // 2
        center_y = pyxel.height //2
        
        # スプライト画像の情報
        sprite_bank = 0      # 使用するスプライトバンク
        sprite_u = 48        # スプライト画像のX座標
        sprite_v = 32        # スプライト画像のY座標
        sprite_w = 48        # GO!画像の幅 (修正: 48px)
        sprite_h = 16        # GO!画像の高さ (修正: 16px)
        colorkey = 1        # 透明色（黒を想定）

        # 背景を描画（単色の長方形）
        pyxel.rect(0, 95, pyxel.width, 50, 1) 

        pyxel.blt(center_x - sprite_w//2, center_y - sprite_h//2, 
                    sprite_bank, sprite_u, sprite_v, 
                    sprite_w, sprite_h,colorkey, scale=scale)
        
    def add_line_clear_effect(self, y_positions):
        """ライン消去エフェクトを追加"""
        for y in y_positions:
            self.line_clear_effect.append({
                "y": Renderer.BOARD_Y + y * Renderer.BLOCK_SIZE,
                "width": 0,
                "timer": 15
            })
            
            # パーティクルも追加
            if GameView.ENABLE_PARTICLES:
                for _ in range(20):
                    self.particles.append({
                        "x": Renderer.BOARD_X + random.randint(0, 10) * Renderer.BLOCK_SIZE,
                        "y": Renderer.BOARD_Y + y * Renderer.BLOCK_SIZE,
                        "dx": random.uniform(-2, 2),
                        "dy": random.uniform(-3, 0),
                        "color": random.choice([7, 8, 9, 10, 11]),
                        "life": random.randint(20, 40)
                    })
    
    def _draw_line_clear_effect(self):
        """ライン消去エフェクトを描画"""
        new_effects = []
        
        for effect in self.line_clear_effect:
            # エフェクトの表示時間が残っている場合
            if effect["timer"] > 0:
                # 横に広がる白い線
                board_width = 10 * Renderer.BLOCK_SIZE
                center_x = Renderer.BOARD_X + board_width // 2
                half_width = min(effect["width"], board_width // 2)
                
                pyxel.rect(center_x - half_width, effect["y"], half_width * 2, Renderer.BLOCK_SIZE, 7)
                
                # エフェクトを更新
                effect["width"] += 2
                effect["timer"] -= 1
                new_effects.append(effect)
        
        self.line_clear_effect = new_effects

    def _draw_particles(self):
        """パーティクルエフェクトを描画"""
        if not GameView.ENABLE_PARTICLES:
            return
        
        new_particles = []
        
        for p in self.particles:
            # パーティクルの寿命が残っている場合
            if p["life"] > 0:
                # パーティクルを描画
                pyxel.pset(p["x"], p["y"], p["color"])
                
                # パーティクルを移動
                p["x"] += p["dx"]
                p["y"] += p["dy"]
                p["dy"] += 0.1  # 重力
                p["life"] -= 1
                
                new_particles.append(p)
        
        self.particles = new_particles