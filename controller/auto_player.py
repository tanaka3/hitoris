# controller/auto_player.py
from copy import deepcopy
import math
import pyxel

from model.board import Board

class AutoPlayer:
    """
    デモ用の極シンプルAI。
    - 毎回、現在ピースに対して「回転0..3 × x位置」を総当り
    - クローン盤面で着地をシミュレーションし、簡易評価でベストを選ぶ
    - ベストへ向かう操作列（plan）を1フレーム1手ずつ実行
    """
    def __init__(self, game):
        self.game = game
        self.plan = []
        self._last_piece_obj = None  # 参照が変わった＝新ピース出現の検出用

    # === 外部から毎フレーム呼ぶ ===
    def update(self):
        # カウントダウン中やゲームオーバーでは何もしない
        if self.game.countdown_active or self.game.is_game_over or self.game.game_over_triggered:
            self.plan.clear()
            self._last_piece_obj = self.game.current_tetromino
            return

        # ピースが変わったら計画作り直し
        if self._last_piece_obj is not self.game.current_tetromino:
            self.plan = self._make_plan()
            self._last_piece_obj = self.game.current_tetromino

        # 計画が空なら、保険としてゆっくり落とす
        if not self.plan:
            # 4フレに1度だけ下げる（落下は game.update() でも進むので控えめ）
            if self.game.level < 3 and (self._frame() % 4 == 0):
                self.game.move_down()
            return

        # 1フレームに1手ずつ実行
        action = self.plan.pop(0)
        self._apply(action)

    # === 計画作成 ===
    def _make_plan(self):
        piece = self.game.current_tetromino
        board = self.game.board
        if piece is None:
            return []

        best = None
        best_seq = []

        # 試したい回転回数（0..3）を列挙
        for rot in range(4):
            # xの探索範囲（左右に少し余裕を持たせて無効は弾く）
            for dst_x in range(-4, board.width + 4):
                score, seq = self._simulate_and_score(rot, dst_x)
                if score is None:
                    continue
                if best is None or score > best:
                    best, best_seq = score, seq

        return best_seq

    # === 1手シミュレーション ===
    def _simulate_and_score(self, rot, dst_x):
        # 必要オブジェクト
        piece0 = self.game.current_tetromino
        if piece0 is None:
            return None, []

        # --- 盤面/ピースのクローンを作成 ---
        b = Board(self.game.board.width, self.game.board.height)
        b.grid = [row[:] for row in self.game.board.grid]

        p = piece0.copy()  # Tetromino.copy() は既存コードで使用されている
        # 指定回転へ（単純に時計回りrot回）
        for _ in range(rot % 4):
            p.rotate_clockwise()
            if not b.is_valid_position(p):
                # SRSキックは省略（壁に当たるものは除外）
                return None, []

        # 指定xへ（衝突したら除外）
        cur_x = p.x
        dx = dst_x - cur_x
        step = 1 if dx > 0 else -1
        while dx != 0:
            p.x += step
            if not b.is_valid_position(p):
                return None, []
            dx -= step

        # 下へ落とす
        while True:
            p.y += 1
            if not b.is_valid_position(p):
                p.y -= 1
                break

        # ロック → 行消去をクローン盤面上で実行
        b.lock_tetromino(p)
        lines_before = self._count_full_lines(b)
        cleared = b.clear_lines()
        # 一部実装では clear_lines() が内部で消し、戻り値で本数を返す
        # 念のためどちらでも動くよう fallback
        lines_cleared = cleared if isinstance(cleared, int) else lines_before

        # 盤面特徴量
        heights = self._column_heights(b)
        agg_height = sum(heights)
        holes = self._holes(b, heights)
        bumpiness = self._bumpiness(heights)
        max_height = max(heights) if heights else 0

        # スコア（調整しやすいようシンプルに線形）
        score = (
            1000 * lines_cleared
            - 8   * holes
            - 1.5 * agg_height
            - 2.0 * bumpiness
            - 0.5 * max_height
        )

        # 実行用の操作列を作る（現在の実ゲーム座標からの相対操作）
        exec_seq = []
        # 回転
        exec_seq += ["rotcw"] * (rot % 4)
        # 横移動
        cur_x_real = piece0.x
        if dst_x < cur_x_real:
            exec_seq += ["left"] * (cur_x_real - dst_x)
        elif dst_x > cur_x_real:
            exec_seq += ["right"] * (dst_x - cur_x_real)
        # ドロップ（見栄え重視でハード）
        exec_seq += ["hard"]

        return score, exec_seq

    # === 低レベル評価関数 ===
    def _count_full_lines(self, b):
        return sum(1 for y in range(b.height) if all(b.grid[y][x] != 0 for x in range(b.width)))

    def _column_heights(self, b):
        heights = [0] * b.width
        for x in range(b.width):
            h = 0
            for y in range(b.height):
                if b.grid[y][x] != 0:
                    h = b.height - y
                    break
            heights[x] = h
        return heights

    def _holes(self, b, heights):
        holes = 0
        for x in range(b.width):
            top = b.height - heights[x]
            if top < 0:  # 何もない列
                top = b.height
            for y in range(top + 1, b.height):
                if b.grid[y][x] == 0:
                    holes += 1
        return holes

    def _bumpiness(self, heights):
        return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))

    def _frame(self):
        # pyxel.frame_count に依存しない実装でも良いが、ここでは簡易にゲーム側を参照
        return pyxel.frame_count

    # === 実行（1フレ1手） ===
    def _apply(self, action):
        if action == "left":
            self.game.move_left()
        elif action == "right":
            self.game.move_right()
        elif action == "rotcw":
            self.game.rotate(clockwise=True)
        elif action == "rotccw":
            self.game.rotate(clockwise=False)
        elif action == "soft":
            self.game.move_down()
        elif action == "hard":
            self.game.hard_drop()
