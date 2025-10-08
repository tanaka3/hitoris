import pyxel
from model.game import Game
from model.ranking import Ranking
from controller.input_handler import InputHandler
from controller.auto_player import AutoPlayer
from view.game_view import GameView
from view.title_view import TitleView
from view.loading_view import LoadingView
from view.ranking_view import RankingView, NameEntryView
from controller.game_controller import GameController
from config import Config
from key import KeyConfig

if Config.CAMERA:
    from model.ai_camera import AICamera


class TetrisApp:
    def __init__(self):
        # 画面の解像度を設定
        pyxel.init(Config.SCREEN_CAMERA_WIDTH if Config.CAMERA else Config.SCREEN_WIDTH, 
                    Config.SCREEN_WIDTH, title="HITORIS", fps=60)
        pyxel.load("hitoris.pyxres")  # リソースファイルをロード
        #pyxel.fullscreen(True) 
        
        # ゲームの状態
        self.is_title_screen = True
        self.is_loading = False
        self.is_name_entry = False
        self.is_ranking = False
        
        # アトラクトモードの状態管理
        self.attract_phase = 0  # 0: 初回タイトル→ランキング, 1: ランキング後タイトル→デモ
        
        # モデル
        self.game = Game()
        self.ranking = Ranking()
        
        # ビュー
        self.title_view = TitleView()
        self.game_view = GameView()
        self.ranking_view = RankingView()
        self.name_entry_view = NameEntryView()
    
        self.camera = None
        self.loading_view = None

        if Config.CAMERA:
            self.loading_view = LoadingView()
            self.is_loading = True
            self.camera = AICamera()
            self.mode = "pose"

            self.game.set_camera(self.camera)
        
        # コントローラー
        self.controller = GameController(self.game)
        self.auto_player = AutoPlayer(self.game)
        
        # グローバルアクセス用（エフェクト登録用）
        pyxel.APP = self

        self.idle_timer = 0
        self.new_rank = None
        
        # Pyxelのコールバックを設定
        pyxel.run(self.update, self.draw)
    
    def update(self):
        # ESCキーでゲーム終了
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        # ローディング画面の処理
        if self.is_loading:
            self.loading_view.update() 

            if self.camera.is_model_loaded():
                self.is_loading = False
                self.is_title_screen = True
                self.idle_timer = 0

        # 名前入力画面の処理
        elif self.is_name_entry:
            self.name_entry_view.update()
            
            # タイムアウトチェック
            if self.name_entry_view.is_timeout():
                # タイムアウト時は現在の名前で自動決定
                name = self.name_entry_view.get_name()
                self.ranking.add_entry(name, self.game.score, self.game.lines_cleared)
                self.is_name_entry = False
                self.is_ranking = True
                self.ranking_view.reset_timer()
                self.idle_timer = 0
            elif self.name_entry_view.handle_input():
                # 手動で決定
                name = self.name_entry_view.get_name()
                self.ranking.add_entry(name, self.game.score, self.game.lines_cleared)
                self.is_name_entry = False
                self.is_ranking = True
                self.ranking_view.reset_timer()
                self.idle_timer = 0

        # ランキング画面の処理
        elif self.is_ranking:
            self.ranking_view.update()
            
            # タイムアウトまたはボタン押下でタイトルへ
            if self.ranking_view.is_timeout() or self.controller.any_pressed():
                self.is_ranking = False
                self.is_title_screen = True
                self.new_rank = None
                self.game.reset()  # ゲームをリセット
                self.idle_timer = 0
                
                # ボタン押下の場合はフェーズをリセット
                if self.controller.any_pressed():
                    self.attract_phase = 0
                else:
                    # タイムアウトの場合は次のフェーズへ
                    self.attract_phase = 1

        # タイトル画面の処理
        elif self.is_title_screen:
            # 何か入力があったらタイマーとフェーズをリセット
            if self.controller.any_pressed():
                self.idle_timer = 0
                self.attract_phase = 0
            else:
                # 入力がない場合はタイマーを進める
                self.idle_timer += 1
                
                # フェーズ0: タイトル→ランキング（60秒後）
                if self.attract_phase == 0 and self.idle_timer >= Config.TITLE_TO_RANKING_SEC * 60:
                    self.is_title_screen = False
                    self.is_ranking = True
                    self.new_rank = None
                    self.ranking_view.reset_timer()
                    self.idle_timer = 0
                    return
                
                # フェーズ1: タイトル→デモモード（60秒後）
                if self.attract_phase == 1 and self.idle_timer >= Config.TITLE_TO_DEMO_SEC * 60:
                    pyxel.play(0, 1)
                    self.is_title_screen = False
                    self.game.start(True)  # オートプレイモードで開始
                    self.idle_timer = 0
                    self.attract_phase = 0  # 次回はまたランキングから
                    return

            if InputHandler.is_key_pressed(KeyConfig.START):    
                pyxel.play(0, 1)
                self.is_title_screen = False
                self.game.start(False)  # 手動プレイモードで開始
                self.idle_timer = 0
                self.attract_phase = 0

            if Config.CAMERA and InputHandler.is_key_pressed(KeyConfig.SELECT):
                self.mode = "obj" if self.mode == "pose" else "pose"

                if self.camera.set_model(self.mode):
                    self.title_view.mode = self.mode
                    self.is_title_screen = False
                    self.is_loading = True
                    self.idle_timer = 0
                    self.attract_phase = 0
                
            self.title_view.update()
            
        # ゲーム画面の処理
        else:
            # オートプレイモード中
            if self.game.is_auto_play:
                if self.controller.any_pressed():
                    self.is_title_screen = True
                    self.game.reset()
                    self.idle_timer = 0
                    self.attract_phase = 0
                    return
                
                # オートプレイヤーを更新
                self.auto_player.update()
            # 手動プレイモード中
            else:
                self.controller.handle_input()
            
            # ゲーム本体を更新
            self.game.update()
                
            # ゲームオーバー時の処理
            if self.game.is_game_over:
                # オートプレイモードではランキングに登録せずタイトルへ
                if self.game.is_auto_play:
                    self.is_title_screen = True
                    self.game.reset()
                    self.idle_timer = 0
                    self.attract_phase = 0  # デモ後はまたランキングから開始
                # 手動プレイモードではランキング処理
                else:
                    # ランクインチェック
                    if self.ranking.check_ranking(self.game.score):
                        # ランクイン！名前入力へ
                        self.new_rank = self.ranking.get_rank(self.game.score)
                        self.is_name_entry = True
                        self.name_entry_view.reset()
                        self.attract_phase = 0  # 手動プレイ後はリセット
                    else:
                        # ランキング表示（ランクインなし）
                        self.is_ranking = True
                        self.new_rank = None
                        self.ranking_view.reset_timer()
                        self.attract_phase = 0  # 手動プレイ後はリセット
                    
                    self.idle_timer = 0
                return
    
    def draw(self):
        pyxel.cls(0)
        
        if self.is_loading:
            self.loading_view.draw()
        elif self.is_name_entry:
            self.name_entry_view.draw(self.game.score, self.game.lines_cleared, self.new_rank)
        elif self.is_ranking:
            self.ranking_view.draw(self.ranking, self.new_rank)
        elif self.is_title_screen:
            self.title_view.draw()
        else:
            self.game_view.draw(self.game, self.camera)       

if __name__ == "__main__":
    TetrisApp()