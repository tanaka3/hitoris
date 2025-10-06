import pyxel
from model.game import Game
from controller.input_handler import InputHandler
from view.game_view import GameView
from view.title_view import TitleView
from view.loading_view import LoadingView
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
        
        # モデル
        self.game = Game()
        
        # ビュー
        self.title_view = TitleView()
        self.game_view = GameView()
    
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
        
        # グローバルアクセス用（エフェクト登録用）
        pyxel.APP = self
        
        # Pyxelのコールバックを設定
        pyxel.run(self.update, self.draw)
    
    def update(self):
        # ESCキーでゲーム終了
        #if InputHandler.is_key_pressed(KeyConfig.EXIT):
        #    pyxel.quit()
        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        # タイトル画面の処理
        if self.is_loading:
            self.loading_view.update() 

            if self.camera.is_model_loaded():
                self.is_loading = False
                self.is_title_screen = True
        

        elif self.is_title_screen:
            if InputHandler.is_key_pressed(KeyConfig.START):    
                pyxel.play(0, 1)
                self.is_title_screen = False
                self.game.start(True)

            if Config.CAMERA and InputHandler.is_key_pressed(KeyConfig.SELECT):
                self.mode = "obj" if self.mode == "pose" else "pose"

                if self.camera.set_model(self.mode):

                    self.title_view.mode = self.mode
                    self.is_title_screen = False
                    self.is_loading = True
                
            self.title_view.update()
        # ゲーム画面の処理
        else:
            if self.game.is_auto_play:
                if self.controller.any_pressed():
                    self.is_title_screen = True
                    self.game.reset()
                    return

            self.controller.handle_input()
            self.game.update()
                
            # ゲームオーバー時はタイトル画面に戻る
            if self.game.is_game_over:
                self.is_title_screen = True
                self.game.reset()
    
    def draw(self):
        pyxel.cls(0)
        
        if self.is_loading:
            self.loading_view.draw()
        elif self.is_title_screen:
            self.title_view.draw()
        else:
            self.game_view.draw(self.game, self.camera)       

if __name__ == "__main__":
    TetrisApp()
