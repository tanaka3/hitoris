import copy  # deepcopy を使うため
#import numpy as np

class Tetromino:
    # テトロミノの形状定義
    # 各テトロミノは4つの回転状態を持つ
    SHAPES = [
        # I (シアン)
        [
            [
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 0]
            ],
            [
                [0, 0, 0, 0],
                [0, 0, 0, 0],
                [1, 1, 1, 1],
                [0, 0, 0, 0]
            ],
            [
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 0, 0]
            ]
        ],
        # J (青)
        [
            [
                [1, 0, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 1, 1],
                [0, 1, 0],
                [0, 1, 0]
            ],
            [
                [0, 0, 0],
                [1, 1, 1],
                [0, 0, 1]
            ],
            [
                [0, 1, 0],
                [0, 1, 0],
                [1, 1, 0]
            ]
        ],
        # L (オレンジ)
        [
            [
                [0, 0, 1],
                [1, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 1, 0],
                [0, 1, 0],
                [0, 1, 1]
            ],
            [
                [0, 0, 0],
                [1, 1, 1],
                [1, 0, 0]
            ],
            [
                [1, 1, 0],
                [0, 1, 0],
                [0, 1, 0]
            ]
        ],
        # O (黄)
        [
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ],
            [
                [0, 1, 1, 0],
                [0, 1, 1, 0],
                [0, 0, 0, 0]
            ]
        ],
        # S (緑)
        [
            [
                [0, 1, 1],
                [1, 1, 0],
                [0, 0, 0]
            ],
            [
                [0, 1, 0],
                [0, 1, 1],
                [0, 0, 1]
            ],
            [
                [0, 0, 0],
                [0, 1, 1],
                [1, 1, 0]
            ],
            [
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0]
            ]
        ],
        # T (紫)
        [
            [
                [0, 1, 0],
                [1, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 1, 0],
                [0, 1, 1],
                [0, 1, 0]
            ],
            [
                [0, 0, 0],
                [1, 1, 1],
                [0, 1, 0]
            ],
            [
                [0, 1, 0],
                [1, 1, 0],
                [0, 1, 0]
            ]
        ],
        # Z (赤)
        [
            [
                [1, 1, 0],
                [0, 1, 1],
                [0, 0, 0]
            ],
            [
                [0, 0, 1],
                [0, 1, 1],
                [0, 1, 0]
            ],
            [
                [0, 0, 0],
                [1, 1, 0],
                [0, 1, 1]
            ],
            [
                [0, 1, 0],
                [1, 1, 0],
                [1, 0, 0]
            ]
        ]
    ]
    
    # 各テトロミノの色
    # COLORS = [
    #     11,  # I: シアン
    #     12,  # J: 青
    #     9,   # L: オレンジ
    #     10,  # O: 黄色
    #     3,   # S: 緑
    #     2,   # T: 紫
    #     8    # Z: 赤
    # ]
    
    def __init__(self, shape, type):
        self.type = type  # テトロミノの種類 (0-6)
        self.shape = shape
        self.rotation = 0  # 回転状態 (0-3)
        self.x = 0  # X座標
        self.y = 0  # Y座標
    
    @staticmethod
    def create(type):
        return Tetromino(Tetromino.SHAPES[type], type)

    def get_shape(self):
        """現在の回転状態でのテトロミノの形状を取得"""
        return self.shape[self.rotation]
    
    # def get_color(self):
    #     """テトロミノの色を取得"""
    #     return self.COLORS[self.type]
    
    def rotate_clockwise(self):
        """時計回りに回転"""
        self.rotation = (self.rotation + 1) % 4
    
    def rotate_counterclockwise(self):
        """反時計回りに回転"""
        self.rotation = (self.rotation - 1) % 4
    
    def get_width(self):
        """テトロミノの幅を取得"""
        return len(self.get_shape()[0])
    
    def get_height(self):
        """テトロミノの高さを取得"""
        return len(self.get_shape())
    
    def copy(self):
        """このテトロミノのディープコピーを作成して返す"""
        new_tetromino = Tetromino(copy.deepcopy(self.shape), self.type)
        new_tetromino.rotation = self.rotation
        new_tetromino.x = self.x
        new_tetromino.y = self.y
        return new_tetromino
    
    def equals_current_shape(self, other):
        """他のテトロミノと現在の形状が一致するか判定"""
        #return np.array_equal(np.array(self.get_shape()), np.array(other.get_shape()))
        
        my_shape = self.get_shape()
        other_shape = other.get_shape()
        
        # まず形状の行数が同じか確認
        if len(my_shape) != len(other_shape):
            return False
        
        # 各行ごとに比較
        for i in range(len(my_shape)):
            # 行の長さが異なる場合
            if len(my_shape[i]) != len(other_shape[i]):
                return False
            
            # 各要素の比較
            for j in range(len(my_shape[i])):
                if my_shape[i][j] != other_shape[i][j]:
                    return False
        
        # すべての要素が一致した場合
        return True