import random
import pyxel
import math
from config import Config
from model.tetromino import Tetromino
from model.board import Board

class Game:
    SHUTTER_COUNT = 30

    def __init__(self):
        # ゲームボード
        self.board = Board(10, 20)  # 10x20のボード
        
        # 現在操作中のテトロミノ
        self.current_tetromino = None
        
        # 次に出現するテトロミノ（2つ先まで）
        self.next_tetrominos = []
        
        # ホールドされているテトロミノ
        self.hold_tetromino = None
        
        # ホールドを使用したかどうかのフラグ
        self.hold_used = False
        
        # スコア
        self.score = 0
        
        # レベル
        self.level = 1
        
        # 消去したライン数
        self.lines_cleared = 0
        
        # ゲームオーバーフラグ
        self.is_game_over = False
        self.game_over_triggered = False  # ゲームオーバーエフェクト用のフラグ
        
        # T-Spin判定用変数
        self.last_move_was_rotation = False
        self.last_rotation_point_x = 0
        self.last_rotation_point_y = 0
        
        # エフェクト表示用
        self.effect_text = ""
        self.effect_timer = 0
        self.effect_color = 7
        
        # 連続消去カウンター (コンボ数)
        self.combo_count = -1
        
        # 背景グリッドの色
        self.grid_color = 1
        
        # カウントダウン関連
        self.countdown_active = False
        self.countdown_timer = 0
        
        # 非アクティブタイマー（操作がない時間を計測）
        self.inactivity_timer = 0
        self.inactivity_limit = 600  # 10秒 (60フレーム × 10)
        
        #
        self.camera = None
        self.shutter_count = 0

        # 自動プレイモードかどうか
        self.is_auto_play = False
        
        # ゲーム開始時の初期化
        self.reset()
        
    def set_camera(self, value):
        # セッター
        if not value == None:
            self.camera = value

    def reset(self):
        """ゲームをリセットする"""
        self.board.clear()
        self.current_tetromino = None
        self.next_tetrominos = []
        self.hold_tetromino = None
        self.hold_used = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.is_game_over = False
        self.game_over_triggered = False
        self.combo_count = -1
        self.effect_text = ""
        self.effect_timer = 0
        self.countdown_active = False
        self.countdown_timer = 0
        self.inactivity_timer = 0
        self.shutter_count = 0
        self.is_auto_play = False
        pyxel.stop()
        
    def start(self, is_auto_play = False):

        self.is_auto_play = is_auto_play

        """ゲームを開始する"""
        # 次のテトロミノを2つ用意
        for _ in range(3):  # 現在のテトロミノ + 次の2つで合計3つ
            self._generate_next_tetromino()
        
        # カウントダウンを開始
        self.countdown_active = True
        self.countdown_timer = 60
    
    def _generate_next_tetromino(self, origin_only = True):
        """次のテトロミノを生成する"""
        # テトロミノの種類をランダムに選択
        
        if len(self.next_tetrominos) >= 2 and not origin_only:
            return
        
        new_tetromino = None
        if Config.CAMERA and not self.camera == None and not origin_only:
            new_tetromino = self.camera.get_tetromino()


        if new_tetromino == None:
            new_tetromino = Tetromino.create(random.choice(list(range(7))))
        else:
            self.shutter_count = Game.SHUTTER_COUNT

    
        self.next_tetrominos.append(new_tetromino)
    
    def spawn_tetromino(self):
        """新しいテトロミノをボードに配置する"""
        # 最初のテトロミノを現在のテトロミノにし、新しいテトロミノを生成
        self.current_tetromino = self.next_tetrominos.pop(0)
        self._generate_next_tetromino(False)
        
        # テトロミノの初期位置を設定
        self.current_tetromino.x = self.board.width // 2 - 2
        self.current_tetromino.y = 0
        
        # ホールド使用フラグをリセット
        self.hold_used = False
        
        # 配置できない場合はゲームオーバー
        if not self.board.is_valid_position(self.current_tetromino) and not self.game_over_triggered:
            #self.is_game_over = True
            self.effect_timer = 0
            self.game_over_triggered = True  # エフェクト用のフラグを設定
            pyxel.stop()
            pyxel.play(0, 7)  # ゲームオーバー効果音

    
    def hold(self):
        """現在のテトロミノをホールドする"""
        if self.hold_used or self.countdown_active:
            return  # すでにホールドを使用している場合や、カウントダウン中は何もしない
        
        # 操作があったので非アクティブタイマーをリセット
        self.inactivity_timer = 0
        
        # 現在のテトロミノをホールドに保存
        if self.hold_tetromino is None:
            # ホールドが空の場合
            self.hold_tetromino = self.current_tetromino.copy() #Tetromino(self.current_tetromino.type)
            self.spawn_tetromino()
        else:
            # すでにホールドがある場合は交換
            temp = self.current_tetromino.copy()
            self.current_tetromino = self.hold_tetromino.copy() #Tetromino(self.hold_tetromino.type)
            self.current_tetromino.x = self.board.width // 2 - 2
            self.current_tetromino.y = 0
            self.hold_tetromino = temp
        
        # ホールド使用フラグとT-Spin判定フラグをリセット
        self.hold_used = True
        self.last_move_was_rotation = False
    
    def move_left(self):
        """テトロミノを左に移動する"""
        if self.countdown_active:
            return False  # カウントダウン中は移動しない
        
        # 操作があったので非アクティブタイマーをリセット
        self.inactivity_timer = 0
            
        self.current_tetromino.x -= 1
        if not self.board.is_valid_position(self.current_tetromino):
            self.current_tetromino.x += 1
            return False
        
        pyxel.play(0,0)
        # 移動したらT-Spin判定フラグをリセット
        self.last_move_was_rotation = False
        return True
    
    def move_right(self):
        """テトロミノを右に移動する"""
        if self.countdown_active:
            return False  # カウントダウン中は移動しない
        
        # 操作があったので非アクティブタイマーをリセット
        self.inactivity_timer = 0
            
        self.current_tetromino.x += 1
        if not self.board.is_valid_position(self.current_tetromino):
            self.current_tetromino.x -= 1
            return False
        
        pyxel.play(0,1)        
        # 移動したらT-Spin判定フラグをリセット
        self.last_move_was_rotation = False
        return True
    
    def move_down(self):
        """テトロミノを下に移動する"""
        if self.countdown_active:
            return False  # カウントダウン中は移動しない
        
        # 操作があったので非アクティブタイマーをリセット
        self.inactivity_timer = 0
            
        self.current_tetromino.y += 1
        if not self.board.is_valid_position(self.current_tetromino):
            self.current_tetromino.y -= 1
            self._lock_tetromino()
            return False
        # 移動したらT-Spin判定フラグをリセット
        self.last_move_was_rotation = False
        return True
    
    def hard_drop(self):
        """テトロミノをハードドロップする（一気に下まで落とす）"""
        if self.countdown_active:
            return  # カウントダウン中はハードドロップしない
        
        # 操作があったので非アクティブタイマーをリセット
        self.inactivity_timer = 0
            
        drop_distance = 0
        while self.move_down():
            drop_distance += 1
        
        # ハードドロップボーナス（落下距離×2点）
        self.score += drop_distance * 2
    
    def rotate(self, clockwise=True):
        """テトロミノを回転する（SRSを適用）"""
        if self.countdown_active:
            return False  # カウントダウン中は回転しない
        
        # 操作があったので非アクティブタイマーをリセット
        self.inactivity_timer = 0
            
        if self.current_tetromino.type == 3:  # Oテトロミノは回転しても変わらない
            return False
            
        original_rotation = self.current_tetromino.rotation
        original_x = self.current_tetromino.x
        original_y = self.current_tetromino.y
        
        # テトロミノを回転
        if clockwise:
            self.current_tetromino.rotate_clockwise()
        else:
            self.current_tetromino.rotate_counterclockwise()
        
        # SRSによる壁蹴り処理
        offsets = self._get_srs_offsets(original_rotation, self.current_tetromino.rotation, self.current_tetromino.type)
        
        for dx, dy in offsets:
            self.current_tetromino.x += dx
            self.current_tetromino.y += dy
            
            if self.board.is_valid_position(self.current_tetromino):
                # 回転成功
                self.last_move_was_rotation = True
                self.last_rotation_point_x = self.current_tetromino.x
                self.last_rotation_point_y = self.current_tetromino.y

                if clockwise:
                    pyxel.play(0,2)
                else:
                    pyxel.play(0,3)

                return True
            
            # 元の位置に戻す
            self.current_tetromino.x -= dx
            self.current_tetromino.y -= dy
        
        # 有効な位置が見つからなかった場合、回転をキャンセル
        self.current_tetromino.rotation = original_rotation
        self.current_tetromino.x = original_x
        self.current_tetromino.y = original_y
        return False
    
    def _get_srs_offsets(self, old_rotation, new_rotation, tetromino_type):
        """Super Rotation System（SRS）のオフセットを取得"""
        # Iテトロミノと他のテトロミノのSRSオフセットテーブル
        # 実際のテトリスのSRSと同じ動作をするようにオフセットを定義
        if tetromino_type == 0:  # Iテトロミノの場合
            srs_table = [
                [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],  # 0->1
                [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],  # 1->2
                [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],  # 2->3
                [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)]   # 3->0
            ]
        else:  # その他のテトロミノ
            srs_table = [
                [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],  # 0->1
                [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],    # 1->2
                [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],     # 2->3
                [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)]  # 3->0
            ]
        
        # 回転方向に応じてオフセットを取得
        table_index = old_rotation
        if (old_rotation + 1) % 4 != new_rotation:  # 反時計回りの場合
            table_index = (old_rotation - 1) % 4
        
        return srs_table[table_index]
    
    def _check_t_spin(self):
        """T-Spinが発生したかチェックする"""
        if self.current_tetromino.type != 5:  # Tテトロミノでない場合
            return False
            
        if not self.last_move_was_rotation:  # 最後の操作が回転でない場合
            return False
            
        # 角ブロックの数をカウント（3個以上で T-Spin と判定）
        corners_filled = 0
        t_x = self.last_rotation_point_x
        t_y = self.last_rotation_point_y
        
        # 四隅のブロックをチェック
        corners = [(t_x, t_y), (t_x + 2, t_y), (t_x, t_y + 2), (t_x + 2, t_y + 2)]
        
        for cx, cy in corners:
            if (cx < 0 or cx >= self.board.width or
                cy < 0 or cy >= self.board.height or
                self.board.grid[cy][cx] != 0):
                corners_filled += 1
                
        return corners_filled >= 3
    
    def _lock_tetromino(self):
        """テトロミノをボードに固定する"""

        pyxel.play(0,5)

        self.board.lock_tetromino(self.current_tetromino)
        
        # T-Spinチェック
        is_t_spin = self._check_t_spin()
        
        # ライン消去処理
        lines_cleared = self.board.clear_lines()
        
        # コンボ数更新
        if lines_cleared > 0:
            self.combo_count += 1
        else:
            self.combo_count = -1
            
        # スコア計算とエフェクト表示
        self._update_score(lines_cleared, is_t_spin)
        
        # 次のテトロミノを生成
        self.spawn_tetromino()
    
    def _update_score(self, lines_cleared, is_t_spin):
        """スコアを更新する"""
        # 基本点数（レベルに応じて増加）
        base_points = [0, 100, 300, 500, 800]  # 0, 1, 2, 3, 4ライン消去時のポイント
        
        # エフェクトとスコア計算
        if lines_cleared == 0:
            if is_t_spin:
                # T-Spin Zero
                self.score += 400 * self.level
                self.effect_text = "T-SPIN!"
                self.effect_color = 2  # 紫色
        else:
            # 通常のライン消去かT-Spinかで分岐
            if is_t_spin:
                if lines_cleared == 1:
                    # T-Spin Single
                    self.score += 800 * self.level
                    self.effect_text = "T-SPIN SINGLE!"
                    self.effect_color = 2  # 紫色
                elif lines_cleared == 2:
                    # T-Spin Double
                    self.score += 1200 * self.level
                    self.effect_text = "T-SPIN DOUBLE!"
                    self.effect_color = 2  # 紫色
                elif lines_cleared == 3:
                    # T-Spin Triple
                    self.score += 1600 * self.level
                    self.effect_text = "T-SPIN TRIPLE!"
                    self.effect_color = 2  # 紫色
                     
            else:
                # 通常のライン消去
                self.score += base_points[lines_cleared] * self.level
                
                if lines_cleared == 1:
                    self.effect_text = "SINGLE!"
                    self.effect_color = 7  # 白色
                elif lines_cleared == 2:
                    self.effect_text = "DOUBLE!"
                    self.effect_color = 10  # 黄色
                elif lines_cleared == 3:
                    self.effect_text = "TRIPLE!"
                    self.effect_color = 9  # オレンジ
                elif lines_cleared == 4:
                    self.effect_text = "TETRIS!"
                    self.effect_color = 8  # 赤色             
        
        # コンボボーナス（1コンボあたり50点×レベル）
        if self.combo_count > 0:
            combo_bonus = 50 * self.combo_count * self.level
            self.score += combo_bonus
            
            if self.combo_count > 1:
                self.effect_text += f" {self.combo_count} COMBO!"
            
        # Back-to-Back判定（テトリスやT-Spinの連続）
        # 実装略（必要に応じて追加可能）
            
        # 総消去ライン数を更新
        self.lines_cleared += lines_cleared
        
        # レベルアップ（10ラインごと）
        self.level = self.lines_cleared // 10 + 1
        
        # エフェクトタイマー設定
        if self.effect_text:
            self.effect_timer = 60  # 1秒間表示
    
    def update(self):
        """ゲームの状態を更新する（自動落下など）"""
        # カウントダウン中の更新
        if self.countdown_active:
            self.countdown_timer -= 1
            # カウントダウンが終了したらゲーム開始
            if self.countdown_timer <= 0:
                pyxel.play(0, 8)
                self.countdown_active = False
                pyxel.playm(0, loop=True)
                self.spawn_tetromino()  # カウントダウン終了後にテトロミノを配置
            return
            
        if self.is_game_over:
            return
        
        # 非アクティブタイマーの更新
        if self.game_over_triggered:
            self.inactivity_timer += 1
            if self.inactivity_timer >= self.inactivity_limit:
                # 10秒間操作がなければゲームオーバー
                self.is_game_over = True

            return
        
        # レベルに応じた落下速度で自動落下
        if pyxel.frame_count % max(60 - (self.level * 5), 5) == 0:
            self.move_down()
            
        # エフェクトタイマー更新
        if self.effect_timer > 0:
            self.effect_timer -= 1

        # 
        if self.shutter_count > 0:
            self.shutter_count -= 1