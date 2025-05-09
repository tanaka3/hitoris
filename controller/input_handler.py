import pyxel
from key import KeyConfig

class InputHandler:
    """入力処理を管理するクラス"""
    
    @staticmethod
    def is_key_pressed(key: KeyConfig):
        """キーが押されたかどうかを判定（1回だけ反応）"""
        return pyxel.btnp(key.key) or pyxel.btnp(key.btn)
    
    @staticmethod
    def is_key_pressed_repeat(key: KeyConfig, repeat_interval=10):
        """キーが押されたかどうかを判定（リピート付き）"""
        return pyxel.btnp(key.key, repeat_interval, repeat_interval) or pyxel.btnp(key.btn, repeat_interval, repeat_interval)
    
    @staticmethod
    def is_key_down(key: KeyConfig):
        """キーが押下されているかどうかを判定（連続反応）"""
        return pyxel.btn(key.key) or pyxel.btn(key.btn)
