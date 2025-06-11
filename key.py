from enum import Enum
import pyxel

class KeyConfig(Enum):
    UP = {"key": pyxel.KEY_UP, "btn": pyxel.GAMEPAD1_BUTTON_DPAD_UP}
    DOWN = {"key": pyxel.KEY_DOWN, "btn": pyxel.GAMEPAD1_BUTTON_DPAD_DOWN}
    LEFT = {"key": pyxel.KEY_LEFT, "btn": pyxel.GAMEPAD1_BUTTON_DPAD_LEFT}
    RIGHT = {"key": pyxel.KEY_RIGHT, "btn": pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT}

    HOLD = {"key": pyxel.KEY_C, "btn": pyxel.GAMEPAD1_BUTTON_X}
    LEFT_ROTAITION  = {"key":pyxel.KEY_Z, "btn": pyxel.GAMEPAD1_BUTTON_A}
    RIGHT_ROTAITION  = {"key":pyxel.KEY_X, "btn": pyxel.GAMEPAD1_BUTTON_B}
    START = {"key": pyxel.KEY_SPACE, "btn": pyxel.GAMEPAD1_BUTTON_START}
    EXIT = {"key": pyxel.KEY_ESCAPE, "btn": pyxel.GAMEPAD1_BUTTON_BACK}
    SELECT = {"key": pyxel.KEY_TAB, "btn": pyxel.GAMEPAD1_BUTTON_BACK}

    @property
    def key(self):
        return self.value["key"]

    @property
    def btn(self):
        return self.value["btn"]