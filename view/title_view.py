import pyxel
import math

class TitleView:
    def __init__(self):
        self.t = 0
        self.logo_y = 65
        self.particles = []
        
        # パーティクル生成
        for i in range(30):
            self.particles.append({
                'x': pyxel.rndf(0, pyxel.width),
                'y': pyxel.rndf(0, pyxel.height),
                'speed': pyxel.rndf(0.2, 1.0),
                'size': pyxel.rndi(1, 3),
                'color': pyxel.rndi(8, 14)
            })

 
        self.font_map = {
            'H': [
                "1 0 0 0 1",
                "1 0 0 0 1",
                "1 1 1 1 1",
                "1 0 0 0 1",
                "1 0 0 0 1",
            ],
            'I': [
                "1 1 1",
                "0 1 0",
                "0 1 0",
                "0 1 0",
                "1 1 1",
            ],
            'T': [
                "1 1 1",
                "0 1 0",
                "0 1 0",
                "0 1 0",
                "0 1 0",
            ],
            'O': [
                "1 1 1",
                "1 0 1",
                "1 0 1",
                "1 0 1",
                "1 1 1",
            ],
            'R': [
                "1 1 0",
                "1 0 1",
                "1 1 0",
                "1 0 1",
                "1 0 1",
            ],
            'S': [
                "0 1 1",
                "1 0 0",
                "1 1 0",
                "0 0 1",
                "1 1 0",
            ],
        }

        # より鮮やかな色使い
        self.block_colors = [8, 9, 10, 11, 12, 14]
        
        # テトロミノのサンプル形状
        self.tetrominos = [
            # I
            [(0,0), (1,0), (2,0), (3,0)],
            # O
            [(0,0), (1,0), (0,1), (1,1)],
            # T
            [(1,0), (0,1), (1,1), (2,1)],
            # L
            [(0,0), (0,1), (0,2), (1,2)],
            # J
            [(1,0), (1,1), (1,2), (0,2)],
            # S
            [(1,0), (2,0), (0,1), (1,1)],
            # Z
            [(0,0), (1,0), (1,1), (2,1)]
        ]
        
        # テトロミノのアニメーション用変数
        self.current_tetro = 0

    def update(self):
        self.t += 1
        
        # パーティクルのアップデート
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = pyxel.height
                p['x'] = pyxel.rndf(0, pyxel.width)
        

    def draw(self):
        pyxel.cls(0)

        # 背景グリッド (少し暗めに)
        for x in range(0, pyxel.width, 15):
            pyxel.line(x, 0, x, pyxel.height, 1)
        for y in range(0, pyxel.height, 15):
            pyxel.line(0, y, pyxel.width, y, 1)

        # パーティクルを描画
        for p in self.particles:
            pyxel.pset(p['x'], p['y'], p['color'])
    
        # タイトル背景効果
        wave_height = 25
        for x in range(0, pyxel.width, 2):
            wave = math.sin((self.t / 20) + (x / 30)) * wave_height
            pyxel.line(x, self.logo_y - 15 + wave, x, self.logo_y + 35 + wave, 1)


        # サブタイトル (点滅効果あり)
        subtitle_color = 7 if (self.t // 30) % 2 == 0 else 6
        sub_titie =  "HUMAN POSE CAPTURE BLOCK PUZZLE BY AI CAMERA"
        pyxel.text((pyxel.width - len(sub_titie) *4)//2, 50, sub_titie, subtitle_color)

        # タイトルを描画
        self.draw_block_text_centered(self.logo_y, "HITORIS", 7)



        # スタート指示（バウンドとカラーサイクル効果）
        prompt_text = "PRESS BUTTON TO START"
        prompt_x = (pyxel.width - len(prompt_text) *6)//2
        prompt_y = 170

        for i, char in enumerate(prompt_text):
            char_offset = math.sin((self.t + i * 4) / 10) * 2
            color = self.block_colors[(self.t // 5 + i) % len(self.block_colors)]
            pyxel.text(prompt_x + i * 6, prompt_y + char_offset, char, color)

        # 操作説明
        control_text = "ARROWS: MOVE/DROP   Z/X: ROTATE   C: HOLD"   
        pyxel.text((pyxel.width - len(control_text) *4)//2,  pyxel.height - 10, control_text, 6)


        # バージョン情報
        pyxel.text(pyxel.width - 30, pyxel.height - 10, "v0.0.1", 5)

    def draw_block_text_centered(self, y, text, block_size):
        total_width = 0
        for char in text:
            pattern = self.font_map.get(char)
            if pattern:
                total_width += (len(pattern[0].split()) + 1) * block_size
            else:
                total_width += 4 * block_size

        start_x = (pyxel.width - total_width) // 2

        # グローエフェクト（光る効果）
        # glow_size = 1 + math.sin(self.t / 10) * 0.5
        # for offset_x in [-1, 0, 1]:
        #     for offset_y in [-1, 0, 1]:
        #         if offset_x == 0 and offset_y == 0:
        #             continue
        #         self.draw_block_text(start_x + offset_x * glow_size, y + offset_y * glow_size, text, block_size, glow=True)

        # 影を描画
        self.draw_block_text(start_x + 2, y + 2, text, block_size, shadow=True)
        
        # 本体を描画
        self.draw_block_text(start_x, y, text, block_size, shadow=False)

    def draw_block_text(self, x, y, text, block_size, shadow=False, glow=False):
        cursor_x = x
        for char in text:
            pattern = self.font_map.get(char)
            if pattern:
                self.draw_block_char(cursor_x, y, pattern, block_size, shadow, glow)
                cursor_x += (len(pattern[0].split()) + 1) * block_size
            else:
                cursor_x += 4 * block_size

    def draw_block_char(self, x, y, pattern, block_size, shadow=False, glow=False):
        for row_idx, row in enumerate(pattern):
            for col_idx, val in enumerate(row.split()):
                if val == "1":
                    px = x + col_idx * block_size
                    py = y + row_idx * block_size
                    
                    if glow:
                        # グロー効果
                        pyxel.rect(px, py, block_size, block_size, 2)
                    elif shadow:
                        # 影効果
                        pyxel.rect(px, py, block_size, block_size, 0)
                    else:
                        # 3Dブロック風の効果
                        base_color = self.block_colors[(px + py + self.t) % len(self.block_colors)]
                        
                        # ブロックの本体
                        pyxel.rect(px, py, block_size, block_size, base_color)
                        
                        # ハイライト (上と左)
                        pyxel.rect(px, py, block_size-1, 1, 7)
                        pyxel.rect(px, py, 1, block_size-1, 7)
                        
                        # シャドウ (下と右)
                        pyxel.rect(px+1, py+block_size-1, block_size-1, 1, 0)
                        pyxel.rect(px+block_size-1, py+1, 1, block_size-2, 0)

    def draw_rotating_tetromino(self, x, y, tetro_idx, angle, scale):
        blocks = self.tetrominos[tetro_idx]
        
        # 回転の中心を計算
        center_x = sum(b[0] for b in blocks) / len(blocks)
        center_y = sum(b[1] for b in blocks) / len(blocks)
        
        # ブロックごとに描画
        for block in blocks:
            # 原点を中心に調整
            bx = block[0] - center_x
            by = block[1] - center_y
            
            # 回転
            rad = math.radians(angle)
            rot_x = bx * math.cos(rad) - by * math.sin(rad)
            rot_y = bx * math.sin(rad) + by * math.cos(rad)
            
            # 位置調整とスケール
            draw_x = x + rot_x * scale
            draw_y = y + rot_y * scale
            
            # 色はサイクル
            color = self.block_colors[(tetro_idx + self.t // 10) % len(self.block_colors)]
            
            # ブロック描画
            pyxel.rect(draw_x - scale/2, draw_y - scale/2, scale, scale, color)
            pyxel.rectb(draw_x - scale/2, draw_y - scale/2, scale, scale, 7)