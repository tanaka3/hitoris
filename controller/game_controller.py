import pyxel
from key import KeyConfig
from controller.input_handler import InputHandler

class GameController:
    def __init__(self, game):
        self.game = game
        
        # 自動落下の速度制御用カウンター
        self.auto_drop_counter = 0
        
        # キー入力のディレイカウンター
        self.move_delay = 0
        self.rotate_delay = 0
        self.hold_delay = 0
        
        # DASとARR（Delayed Auto Shift、Auto Repeat Rate）の設定
        self.das = 10  # 最初の入力が効くまでの遅延
        self.arr = 2   # リピート時の間隔
    
    def handle_input(self):
        """ユーザー入力を処理する"""
        if self.game.is_game_over:
            return

        if self.game.game_over_triggered:
            if InputHandler.is_key_pressed(KeyConfig.START):
                self.game.is_game_over = True
            return

        # ホールド
        if ((InputHandler.is_key_pressed(KeyConfig.HOLD)) 
            and self.hold_delay == 0):
            pyxel.play(0, 7)
            self.game.hold()
            self.hold_delay = 10  # ホールド操作後の遅延
        
        # 左移動
        if InputHandler.is_key_down(KeyConfig.LEFT):
            if self.move_delay == 0 or self.move_delay > self.das and self.move_delay % self.arr == 0:
                self.game.move_left()
            self.move_delay += 1
        # 右移動
        elif InputHandler.is_key_down(KeyConfig.RIGHT):
            if self.move_delay == 0 or self.move_delay > self.das and self.move_delay % self.arr == 0:
          
                self.game.move_right()
            self.move_delay += 1
        else:
            self.move_delay = 0
        
        # ソフトドロップ（下キーで加速落下）
        if InputHandler.is_key_down(KeyConfig.DOWN):
            if pyxel.frame_count % 4 == 0:  # ソフトドロップの速度
                self.game.move_down()
        
        # ハードドロップ（上キーで即時落下）
        if InputHandler.is_key_pressed(KeyConfig.UP):
            self.game.hard_drop()
        
        # 回転（ZキーとXキー）
        # 反時計回り回転
        if InputHandler.is_key_pressed(KeyConfig.LEFT_ROTAITION) and self.rotate_delay == 0:

            self.game.rotate(clockwise=False)
            self.rotate_delay = 10  # 回転操作後の遅延
        # 時計回り回転
        elif InputHandler.is_key_pressed(KeyConfig.RIGHT_ROTAITION) and self.rotate_delay == 0:

            self.game.rotate(clockwise=True)
            self.rotate_delay = 10  # 回転操作後の遅延
        
        # ディレイカウンターを減少
        if self.rotate_delay > 0:
            self.rotate_delay -= 1
        if self.hold_delay > 0:
            self.hold_delay -= 1
