import pyxel
import math
import random


class LoadingView:
    def __init__(self):
        self.t = 0
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

        # より鮮やかな色使い
        self.block_colors = [8, 9, 10, 11, 12, 14]

    def update(self):
        self.t += 1
        # パーティクルのアップデート
        for p in self.particles:
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = pyxel.height
                p['x'] = pyxel.rndf(0, pyxel.width)
    def draw(self):
        """ゲーム画面を描画する"""
        # 背景
        pyxel.cls(0)
        
        # 背景グリッド (少し暗めに)
        for x in range(0, pyxel.width, 15):
            pyxel.line(x, 0, x, pyxel.height, 1)
        for y in range(0, pyxel.height, 15):
            pyxel.line(0, y, pyxel.width, y, 1)

        # パーティクルを描画
        for p in self.particles:
            pyxel.pset(p['x'], p['y'], p['color'])
        
        prompt_text = "NOW LOADING"
        prompt_x = (pyxel.width - len(prompt_text) *6)//2
        prompt_y = 116

        for i, char in enumerate(prompt_text):
            char_offset = math.sin((self.t + i * 4) / 10) * 2
            color = self.block_colors[(self.t // 5 + i) % len(self.block_colors)]
            pyxel.text(prompt_x + i * 6, prompt_y + char_offset, char, color)

 