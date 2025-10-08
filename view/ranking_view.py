import pyxel
import math
from key import KeyConfig
from controller.input_handler import InputHandler
from config import Config

class RankingView:
    """ランキング表示画面"""
    
    def __init__(self):
        self.t = 0
        self.scroll_y = 0
        self.timeout_timer = 0
        
    def reset_timer(self):
        """タイムアウトタイマーをリセット"""
        self.timeout_timer = 0
        
    def update(self):
        """アニメーション更新"""
        self.t += 1
        self.timeout_timer += 1
    
    def is_timeout(self):
        """タイムアウトしたかチェック"""
        return self.timeout_timer >= Config.RANKING_VIEW_TIMEOUT_SEC * 60
    
    def draw(self, ranking, new_rank=None):
        """
        ランキングを描画
        ranking: Rankingオブジェクト
        new_rank: 新しくランクインした順位（1-based、なければNone）
        """
        pyxel.cls(0)
        
        # 背景グリッド
        for x in range(0, pyxel.width, 15):
            pyxel.line(x, 0, x, pyxel.height, 1)
        for y in range(0, pyxel.height, 15):
            pyxel.line(0, y, pyxel.width, y, 1)
        
        # タイトル
        title = "RANKING"
        title_x = (pyxel.width - len(title) * 4) // 2
        pyxel.text(title_x, 15, title, 10)
        
        # ランキング一覧
        rankings = ranking.get_rankings()
        start_y = 35
        
        for i, entry in enumerate(rankings):
            y = start_y + i * 18
            rank = i + 1
            
            # 新しくランクインした行は強調
            is_new = (new_rank is not None and rank == new_rank)
            
            # 点滅効果（新規ランクイン時）
            if is_new and (self.t // 15) % 2 == 0:
                # 背景を点滅
                pyxel.rect(10, y - 5, pyxel.width - 20, 16, 2)
            
            # 順位の色分け
            if rank == 1:
                rank_color = 10  # 金色
            elif rank == 2:
                rank_color = 12  # 銀色
            elif rank == 3:
                rank_color = 9   # 銅色
            else:
                rank_color = 7   # 白色
            
            # 順位
            rank_text = f"{rank:2d}."
            pyxel.text(20, y, rank_text, rank_color)
            
            # 名前
            name = entry['name']
            name_color = 11 if is_new else 7
            pyxel.text(45, y, name, name_color)
            
            # スコア
            score_text = f"{entry['score']:6d}"
            pyxel.text(90, y, score_text, 7)
            
            # ライン数
            lines_text = f"{entry['lines']:3d}L"
            pyxel.text(160, y, lines_text, 6)
        
        # 操作説明
        prompt = "PRESS ANY BUTTON TO CONTINUE"
        prompt_x = (pyxel.width - len(prompt) * 4) // 2
        prompt_y = pyxel.height - 20
        
        # 点滅効果
        if (self.t // 30) % 2 == 0:
            pyxel.text(prompt_x, prompt_y, prompt, 7)


class NameEntryView:
    """名前入力画面"""
    
    ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    def __init__(self):
        self.t = 0
        self.name = ['A', 'A', 'A']  # 3文字の名前
        self.cursor_pos = 0  # 0-2の位置
        self.timeout_timer = 0
        
    def reset(self):
        """リセット"""
        self.name = ['A', 'A', 'A']
        self.cursor_pos = 0
        self.t = 0
        self.timeout_timer = 0
    
    def update(self):
        """アニメーション更新"""
        self.t += 1
        self.timeout_timer += 1
    
    def is_timeout(self):
        """タイムアウトしたかチェック"""
        return self.timeout_timer >= Config.NAME_ENTRY_TIMEOUT_SEC * 60
    
    def handle_input(self):
        """
        入力処理
        戻り値: 入力完了したらTrue
        """
        # 入力があったらタイマーをリセット
        input_detected = False
        
        # 上キーで文字を進める
        if InputHandler.is_key_pressed(KeyConfig.UP):
            idx = self.ALPHABET.index(self.name[self.cursor_pos])
            idx = (idx + 1) % len(self.ALPHABET)
            self.name[self.cursor_pos] = self.ALPHABET[idx]
            pyxel.play(0, 0)
            input_detected = True
            
        # 下キーで文字を戻す
        elif InputHandler.is_key_pressed(KeyConfig.DOWN):
            idx = self.ALPHABET.index(self.name[self.cursor_pos])
            idx = (idx - 1) % len(self.ALPHABET)
            self.name[self.cursor_pos] = self.ALPHABET[idx]
            pyxel.play(0, 0)
            input_detected = True
        
        # 左キーでカーソルを左に移動
        elif InputHandler.is_key_pressed(KeyConfig.LEFT):
            self.cursor_pos = (self.cursor_pos - 1) % 3
            pyxel.play(0, 1)
            input_detected = True
            
        # 右キーでカーソルを右に移動
        elif InputHandler.is_key_pressed(KeyConfig.RIGHT):
            self.cursor_pos = (self.cursor_pos + 1) % 3
            pyxel.play(0, 1)
            input_detected = True
        
        # STARTキー、Zキー、Xキーで決定
        elif (InputHandler.is_key_pressed(KeyConfig.START) or 
              InputHandler.is_key_pressed(KeyConfig.LEFT_ROTAITION) or
              InputHandler.is_key_pressed(KeyConfig.RIGHT_ROTAITION)):
            pyxel.play(0, 2)
            return True
        
        # 入力があったらタイマーをリセット
        if input_detected:
            self.timeout_timer = 0
        
        return False
    
    def get_name(self):
        """入力された名前を取得"""
        return ''.join(self.name)
    
    def draw(self, score, lines, rank):
        """
        名前入力画面を描画
        score: 獲得スコア
        lines: 消去ライン数
        rank: ランクイン順位
        """
        pyxel.cls(0)
        
        # 背景グリッド
        for x in range(0, pyxel.width, 15):
            pyxel.line(x, 0, x, pyxel.height, 1)
        for y in range(0, pyxel.height, 15):
            pyxel.line(0, y, pyxel.width, y, 1)
        
        # タイトル
        title = "NEW RECORD!"
        title_x = (pyxel.width - len(title) * 4) // 2
        
        # 虹色効果
        for i, char in enumerate(title):
            color = [8, 9, 10, 11, 12, 14][(self.t // 5 + i) % 6]
            pyxel.text(title_x + i * 4, 20, char, color)
        
        # ランクイン順位
        rank_text = f"{rank}TH PLACE!"
        rank_x = (pyxel.width - len(rank_text) * 4) // 2
        
        rank_color = 10 if rank == 1 else (12 if rank == 2 else (9 if rank == 3 else 11))
        pyxel.text(rank_x, 40, rank_text, rank_color)
        
        # スコア表示
        score_text = f"SCORE: {score}"
        score_x = (pyxel.width - len(score_text) * 4) // 2
        pyxel.text(score_x, 60, score_text, 7)
        
        # ライン数表示
        lines_text = f"LINES: {lines}"
        lines_x = (pyxel.width - len(lines_text) * 4) // 2
        pyxel.text(lines_x, 75, lines_text, 6)
        
        # 名前入力プロンプト
        prompt = "ENTER YOUR NAME"
        prompt_x = (pyxel.width - len(prompt) * 4) // 2
        pyxel.text(prompt_x, 100, prompt, 7)
        
        # 名前入力エリア（大きく表示）
        name_y = 120
        char_spacing = 30
        total_width = char_spacing * 3
        start_x = (pyxel.width - total_width) // 2
        
        for i, char in enumerate(self.name):
            x = start_x + i * char_spacing + 14
            
            # カーソル位置は強調
            if i == self.cursor_pos:
                # 点滅する下線
                if (self.t // 15) % 2 == 0:
                    pyxel.rect(x - 5, name_y + 12, 12, 2, 11)
                
                # 文字を描画
                self._draw_large_char(x, name_y, char, 11)
            else:
                self._draw_large_char(x, name_y, char, 7)
        
        # 操作説明
        controls = [
            "UP/DOWN: CHANGE LETTER",
            "LEFT/RIGHT: MOVE CURSOR",
            "Z/X or SPACE: CONFIRM"
        ]
        
        for i, text in enumerate(controls):
            text_x = (pyxel.width - len(text) * 4) // 2
            pyxel.text(text_x, 160 + i * 10, text, 6)
    
    def _draw_large_char(self, x, y, char, color):
        """文字を描画"""
        pyxel.text(x, y, char, color)