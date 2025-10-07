# controller/auto_player.py
from copy import deepcopy
import math
import pyxel

from model.board import Board

class AutoPlayer:
    """
    デモ用の極シンプルAI。
    - 毎回、現在ピースに対して「回転0..3 × x位置」を総当り
    - Hold機能も考慮して最適な配置を選択
    - ベストへ向かう操作列（plan）を1フレーム1手ずつ実行
    """
    def __init__(self, game):
        self.game = game
        self.plan = []
        self._last_piece_obj = None  # 参照が変わった＝新ピース出現の検出用
        self.action_delay = 0  # 操作間のディレイ
        
        # Configから設定値を読み込む
        from config import Config
        self.move_delay = Config.AUTO_MOVE_DELAY  # 横移動・回転の遅延フレーム数
        self.drop_delay = Config.AUTO_DROP_DELAY  # ドロップ前の待機フレーム数
        self.spawn_delay = Config.AUTO_SPAWN_DELAY  # 新ピース出現時の待機フレーム数

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
            self.action_delay = self.spawn_delay  # 新しいピースが出現したら少し待つ

        # ディレイ中は何もしない
        if self.action_delay > 0:
            self.action_delay -= 1
            return

        # 計画が空なら、保険としてゆっくり落とす
        if not self.plan:
            # 4フレに1度だけ下げる（落下は game.update() でも進むので控えめ）
            if self.game.level < 3 and (self._frame() % 4 == 0):
                self.game.move_down()
            return

        # 次の操作を実行
        action = self.plan.pop(0)
        self._apply(action)
        
        # 操作後のディレイを設定
        if action in ["left", "right", "rotcw", "rotccw"]:
            self.action_delay = self.move_delay
        elif action == "hard":
            self.action_delay = self.drop_delay
        elif action == "hold":
            self.action_delay = self.spawn_delay  # Hold後は新ピース待機と同じ

    # === 計画作成 ===
    def _make_plan(self):
        piece = self.game.current_tetromino
        board = self.game.board
        if piece is None:
            return []

        # 現在のピースでの最良手を探索
        current_best_score, current_best_seq = self._find_best_placement(piece)
        
        # Hold機能が使用可能かチェック
        if not self.game.hold_used:
            # Holdした場合の最良手を探索
            hold_piece = self._get_hold_piece()
            if hold_piece is not None:
                hold_best_score, hold_best_seq = self._find_best_placement(hold_piece)
                
                # Holdした方が良いスコアなら、Holdを含めた計画にする
                if hold_best_score is not None and (current_best_score is None or hold_best_score > current_best_score + 100):
                    # +100はHoldのコストとして若干の閾値を設ける
                    return ["hold"] + hold_best_seq

        # 現在のピースでの最良手を返す
        return current_best_seq if current_best_score is not None else []

    def _get_hold_piece(self):
        """Hold後に出てくるピースを取得"""
        if self.game.hold_tetromino is not None:
            # すでにHoldがある場合は、それと交換
            return self.game.hold_tetromino.copy()
        elif len(self.game.next_tetrominos) > 0:
            # Holdが空の場合は、次のピースが来る
            return self.game.next_tetrominos[0].copy()
        return None

    def _find_best_placement(self, piece):
        """指定されたピースの最良配置を探索"""
        if piece is None:
            return None, []
            
        board = self.game.board
        best = None
        best_seq = []

        # 試したい回転回数（0..3）を列挙
        for rot in range(4):
            # xの探索範囲（左右に少し余裕を持たせて無効は弾く）
            for dst_x in range(-4, board.width + 4):
                score, seq = self._simulate_and_score(piece, rot, dst_x)
                if score is None:
                    continue
                if best is None or score > best:
                    best, best_seq = score, seq

        return best, best_seq

    # === 1手シミュレーション ===
    def _simulate_and_score(self, piece0, rot, dst_x):
        """指定されたピースでシミュレーション"""
        if piece0 is None:
            return None, []

        board = self.game.board
        
        # --- ピースのクローンを作成（盤面は直接使わない） ---
        p = piece0.copy()
        
        # 指定回転へ（単純に時計回りrot回）
        for _ in range(rot % 4):
            p.rotate_clockwise()
            if not self._is_valid_position_sim(p, board):
                return None, []

        # 指定xへ（衝突したら除外）
        cur_x = p.x
        dx = dst_x - cur_x
        step = 1 if dx > 0 else -1
        while dx != 0:
            p.x += step
            if not self._is_valid_position_sim(p, board):
                return None, []
            dx -= step

        # 下へ落とす
        while True:
            p.y += 1
            if not self._is_valid_position_sim(p, board):
                p.y -= 1
                break

        # --- ここからクローン盤面を作成してロック ---
        grid_clone = [row[:] for row in board.grid]
        
        # ピースを盤面にロック（クローン上で直接実行）
        shape = p.get_shape()  # Tetrominoの形状を取得
        tetromino_type = p.type + 1  # board.pyと同じロジック
        
        for block_y, row in enumerate(shape):
            for block_x, cell in enumerate(row):
                if cell:
                    board_x = p.x + block_x
                    board_y = p.y + block_y
                    if 0 <= board_y < board.height and 0 <= board_x < board.width:
                        grid_clone[board_y][board_x] = tetromino_type
        
        # 消去可能なライン数をカウント
        lines_cleared = self._count_clearable_lines_from_grid(grid_clone, board.width, board.height)

        # 盤面特徴量（クローンgridから計算）
        heights = self._column_heights_from_grid(grid_clone, board.width, board.height)
        agg_height = sum(heights)
        holes = self._holes_from_grid(grid_clone, heights, board.width, board.height)
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

        # 実行用の操作列を作る（piece0の座標からの相対操作）
        exec_seq = []
        # 回転
        exec_seq += ["rotcw"] * (rot % 4)
        # 横移動
        cur_x_real = piece0.x
        if dst_x < cur_x_real:
            exec_seq += ["left"] * (cur_x_real - dst_x)
        elif dst_x > cur_x_real:
            exec_seq += ["right"] * (dst_x - cur_x_real)
        # ドロップ
        exec_seq += ["hard"]

        return score, exec_seq
    
    def _is_valid_position_sim(self, piece, board):
        """シミュレーション用の衝突判定（Boardメソッドを呼ばない）"""
        shape = piece.get_shape()
        
        for block_y, row in enumerate(shape):
            for block_x, cell in enumerate(row):
                if cell == 0:
                    continue
                    
                x = piece.x + block_x
                y = piece.y + block_y
                
                # 範囲外チェック
                if x < 0 or x >= board.width or y < 0 or y >= board.height:
                    return False
                
                # 既存ブロックとの衝突チェック
                if y >= 0 and board.grid[y][x] != 0:
                    return False
        
        return True

    # === 低レベル評価関数 ===
    def _count_clearable_lines_from_grid(self, grid, width, height):
        """gridから直接消去可能なライン数をカウント"""
        count = 0
        for y in range(height):
            if all(grid[y][x] != 0 for x in range(width)):
                count += 1
        return count

    def _column_heights_from_grid(self, grid, width, height):
        """gridから直接各列の高さを計算"""
        heights = [0] * width
        for x in range(width):
            h = 0
            for y in range(height):
                if grid[y][x] != 0:
                    h = height - y
                    break
            heights[x] = h
        return heights

    def _holes_from_grid(self, grid, heights, width, height):
        """gridから直接穴の数をカウント"""
        holes = 0
        for x in range(width):
            top = height - heights[x]
            if top < 0:
                top = height
            for y in range(top + 1, height):
                if grid[y][x] == 0:
                    holes += 1
        return holes

    def _bumpiness(self, heights):
        return sum(abs(heights[i] - heights[i+1]) for i in range(len(heights)-1))

    def _frame(self):
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
        elif action == "hold":
            self.game.hold()