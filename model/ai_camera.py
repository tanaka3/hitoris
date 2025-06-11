import sys
sys.path.append("/usr/lib/python3/dist-packages")  

import pyxel
from config import Config
from picamera2 import Picamera2
from PIL import Image
import numpy as np
import threading
import random
from model.tetromino import Tetromino

from picamera2 import CompletedRequest, MappedArray, Picamera2
from picamera2.devices.imx500 import IMX500, NetworkIntrinsics
from picamera2.devices.imx500.postprocess_highernet import postprocess_higherhrnet

class AICamera:
    GRID_SIZE = 4  # 4x4のグリッド
    DETECTION_THRESHOLD = 0.3
    KEYPOINT_THRESHOLD = 0.4
    OBJECT_THRESHOLD = 0.51
    CAMERA_SIZE_H_W = (320, 240)

    MODEL_POSE_ESTIMATION = "/usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk"
    MODEL_OBJECT_DETECTION = "/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk"

    # 物体とテトロミノの対応関係
    OBJECT_TO_TETROMINO = {
        # I型（直線）：乗り物・交通関係 *
        1: 0, 2: 0, 3: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 12: 0, 13: 0,

        # J型（片側突出）：電子機器・家電 * 
        71: 1, 72: 1, 73: 1, 74: 1, 75: 1, 76: 1, 77: 1, 78: 1, 79: 1, 80: 1, 81: 1,

        # L型（逆向きのJ）：人・身に着ける物・遊具 0: 2, 
        26: 2, 27: 2, 30: 2, 31: 2, 32: 2, 33: 2, 34: 2, 35: 2, 36: 2,
        37: 2, 38: 2, 39: 2, 40: 2, 41: 2, 42: 2, 86: 2, 87: 2, 88: 2, 89: 2,

        # O型（正方形）：家具・静的オブジェクト *
        14: 3, 61: 3, 62: 3, 63: 3, 64: 3, 66: 3, 69: 3,

        # S型（曲線的）：動物・自然 * 
        15: 4, 16: 4, 17: 4, 18: 4, 19: 4, 20: 4, 21: 4, 22: 4, 23: 4, 24: 4,

        # T型（中心＋3方向）：小型オブジェクト・道具 *
        43: 5, 45: 5, 46: 5, 47: 5, 48: 5, 49: 5, 50: 5, 83: 5, 84: 5, 85: 5,

        # Z型（ジグザグ）：食べ物・日用品 *
        51: 6, 52: 6, 53: 6, 54: 6, 55: 6, 56: 6, 57: 6, 58: 6, 59: 6, 60: 6
    }

    OBJECT_TO_LABEL = {
        0: "person",1: "bicycle",2: "car",3: "motorcycle",4: "airplane",5: "bus",6: "train",7: "truck",8: "boat",9: "traffic light",
        10: "fire hydrant",11: "-",12: "stop sign",13: "parking meter",14: "bench",15: "bird",16: "cat",17: "dog",18: "horse",19: "sheep",
        20: "cow",21: "elephant",22: "bear",23: "zebra",24: "giraffe",25: "-",26: "backpack",27: "umbrella",28: "-",29: "-",
        30: "handbag",31: "tie",32: "suitcase",33: "frisbee",34: "skis",35: "snowboard",36: "sports ball",37: "kite",38: "baseball bat",39: "baseball glove",
        40: "skateboard",41: "surfboard",42: "tennis racket",43: "bottle",44: "-",45: "wine glass",46: "cup",47: "fork",48: "knife",49: "spoon",
        50: "bowl",51: "banana",52: "apple",53: "sandwich",54: "orange",55: "broccoli",56: "carrot",57: "hot dog",58: "pizza",59: "donut",
        60: "cake",61: "chair",62: "couch",63: "potted plant",64: "bed",65: "-",66: "dining table",67: "-",68: "-",69: "toilet",
        70: "-",71: "tv",72: "laptop",73: "mouse",74: "remote",75: "keyboard",76: "cell phone",77: "microwave",78: "oven",79: "toaster",
        80: "sink",81: "refrigerator",82: "-",83: "book",84: "clock",85: "vase",86: "scissors",87: "teddy bear",88: "hair drier",89: "toothbrush"
    }

    def __init__(self):
        self.pyxel_palette = self._get_pyxel_palette().reshape(1, 16, 3)
        self.color_lut = self._build_weighted_lut_6bit()

        # 状態変数
        self.shared_frame = None
        self.lock = threading.Lock()

        # 最後に検出された結果を保存する変数
        self.last_boxes = None
        self.last_scores = None
        self.last_keypoints = None

        self.shared_tetromino = None
        
        self.mode = "pose"  # デフォルトを物体検出に変更

        self.imx500 = None
        self.picam2 = None

        self._set_model(self.mode)

            # 高速化のための事前定義済み配置パターン
        self.two_piece_patterns = [
            # 横並び優先（高確率で成功）
            [(0, 0), (0, 2)], [(0, 0), (0, 3)], [(1, 0), (1, 2)],
            # 縦並び
            [(0, 0), (2, 0)], [(0, 0), (3, 0)], [(0, 1), (2, 1)],
            # L字型
            [(0, 0), (2, 2)], [(0, 0), (1, 2)], [(0, 2), (2, 0)]
        ]
        
        self.three_piece_patterns = [
            # 一列配置（最も効率的）
            [(0, 0), (0, 1), (0, 3)], [(0, 0), (1, 0), (3, 0)],
            # L字型
            [(0, 0), (0, 2), (2, 0)], [(0, 0), (2, 0), (2, 2)],
            # コンパクト三角
            [(0, 0), (1, 1), (0, 2)], [(0, 1), (1, 0), (1, 2)],
            # 分散配置
            [(0, 0), (1, 2), (2, 1)], [(0, 0), (0, 3), (3, 0)]
        ]
        self.GRID_SIZE = 4

    def set_model(self, mode_name):
        if self.mode == mode_name:
            return False

        if mode_name == "obj" or mode_name == "pose": 
            self._set_model(mode_name)
            return True

        return False
    
    def _set_model(self, mode):
        
        if self.picam2:
            self.picam2.stop()
            self.picam2.close()
            del self.picam2
        
        if self.imx500:
            del self.imx500

        self.mode = mode

        model = AICamera.MODEL_POSE_ESTIMATION if self.mode == "pose" else AICamera.MODEL_OBJECT_DETECTION

        self.imx500 = IMX500(model)
        intrinsics = self.imx500.network_intrinsics or NetworkIntrinsics()
        if intrinsics.inference_rate is None:
            intrinsics.inference_rate = 10
        if intrinsics.labels is None:
            with open("assets/coco_labels.txt", "r") as f:
                intrinsics.labels = f.read().splitlines()
        intrinsics.update_with_defaults()
        self.imx500.set_auto_aspect_ratio()

        self.picam2 = Picamera2(self.imx500.camera_num)
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": AICamera.CAMERA_SIZE_H_W},
            controls={'FrameRate': 30}, 
            buffer_count=12)
        #self.imx500.show_network_fw_progress_bar()
        self.picam2.start(config, show_preview=False)
 
        self.picam2.pre_callback = self._camera_callback
        
    def is_model_loaded(self):
        current, total = self.imx500.get_fw_upload_progress(2)
        if current > 0.95 * total:
            return True
        return False

    # Pyxelパレット取得
    def _get_pyxel_palette(self):
        palette = []
        for i in range(16):
            color = pyxel.colors[i]
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            palette.append([r, g, b])
        return np.array(palette, dtype=np.int16)
    
    # R成分に重みをつけた LUT を構築
    def _build_weighted_lut_6bit(self, rgb_weights=(1.4, 1.0, 0.6)):
        lut = np.zeros((64, 64, 64), dtype=np.uint8)
        w = np.array(rgb_weights).reshape(1, 1, 3)

        for r in range(64):
            for g in range(64):
                for b in range(64):
                    rgb = np.array([r << 2, g << 2, b << 2])
                    diffs = self.pyxel_palette.astype(np.int16) - rgb.astype(np.int16)
                    distances = np.sum((diffs * w) ** 2, axis=2)
                    lut[r, g, b] = np.argmin(distances)
        return lut
    
    # カメラ画像取得 → リサイズ
    def _camera_callback(self, request):
        if self.mode == "pose":
            boxes, scores, keypoints = self._ai_output_tensor_parse_pose(request.get_metadata())
            with MappedArray(request, stream='main') as m:
                # キーポイントからブロックを生成して描画
                if keypoints is not None and len(keypoints) > 0:
                    img_height, img_width = m.array.shape[:2]
                    self.shared_tetromino = self._create_occupancy_grid(keypoints, img_width, img_height)
        else:
            # 物体検出の場合
            detected_objects = self._ai_output_tensor_parse_objects(request.get_metadata())
            if detected_objects is not None and len(detected_objects) > 0:
                with MappedArray(request, stream='main') as m:
                    img_height, img_width = m.array.shape[:2]
                    self.shared_tetromino = self._create_tetromino_from_objects(detected_objects, img_width, img_height)
            pass

        # pyxel画像化
        frame = request.make_array("main")
        h, w, _ = frame.shape
        min_side = min(h, w)
        top = (h - min_side) // 2
        left = (w - min_side) // 2
        cropped = frame[top:top + min_side, left:left + min_side]
        resized = np.array(Image.fromarray(cropped).resize((Config.CAMERA_WIDTH, Config.CAMERA_HEIGHT), Image.BILINEAR))

        with self.lock:
            self.shared_frame = resized

    def _ai_output_tensor_parse_pose(self, metadata: dict):
        """ポーズ推定用のパース処理"""
        np_outputs = self.imx500.get_outputs(metadata=metadata, add_batch=True)
        if np_outputs is not None:
            keypoints, scores, boxes = postprocess_higherhrnet(outputs=np_outputs,
                                                            img_size=AICamera.CAMERA_SIZE_H_W,
                                                            img_w_pad=(0, 0),
                                                            img_h_pad=(0, 0),
                                                            detection_threshold=AICamera.DETECTION_THRESHOLD,
                                                            network_postprocess=True)

            if scores is not None and len(scores) > 0:
                self.last_keypoints = np.reshape(np.stack(keypoints, axis=0), (len(scores), 17, 3))
                self.last_boxes = [np.array(b) for b in boxes]
                self.last_scores = np.array(scores)

        return self.last_boxes, self.last_scores, self.last_keypoints

    def _ai_output_tensor_parse_objects(self, metadata: dict):
        """物体検出用のパース処理"""
        np_outputs = self.imx500.get_outputs(metadata=metadata, add_batch=True)
        if np_outputs is not None:
            # SSD MobileNet用の後処理
            # 実際の実装では、使用しているモデルに応じた後処理を行う
            # ここでは簡略化して、検出結果の構造を想定
            
            # 通常、SSDの出力は [boxes, scores, classes, num_detections] の形式
            if len(np_outputs) >= 3:
                boxes = np_outputs[0]
                scores = np_outputs[1] 
                classes = np_outputs[2]
                
                detected_objects = []
                
                # 閾値以上のスコアを持つ検出結果のみを処理
                for i in range(len(scores[0])):
                    if scores[0][i] >= AICamera.OBJECT_THRESHOLD:
                        class_id = int(classes[0][i])

                        if not class_id in AICamera.OBJECT_TO_TETROMINO:
                            continue

                        score = scores[0][i]
                        box = boxes[0][i]  # [y1, x1, y2, x2] の順序（正規化済み）

                        if score < AICamera.OBJECT_THRESHOLD:
                            continue
                        
                        detected_objects.append({
                            'class_id': class_id,
                            'score': score,
                            'box': box
                        })
                
                # スコア順でソート、上位2つまで
                detected_objects.sort(key=lambda x: x['score'], reverse=True)
                self.last_detected_objects = detected_objects[:2]
                
                return self.last_detected_objects
        
        return None


    def _create_tetromino_from_objects(self, detected_objects, img_width, img_height):
        """検出された物体からテトロミノを生成"""
        if not detected_objects:
            return None
        
        # 最大2つまでの物体を処理
        objects_to_process = detected_objects[:2]
        
        # 検出された物体に対応するテトロミノを取得
        tetrominoes = []
        for obj in objects_to_process:
            class_id = obj['class_id']
            if class_id in AICamera.OBJECT_TO_TETROMINO:
                print(f"{class_id} - {AICamera.OBJECT_TO_LABEL[class_id]} {obj['score']:.2f}")
                    
                tetromino_type = AICamera.OBJECT_TO_TETROMINO[class_id]
                tetromino = Tetromino.create(tetromino_type)
                tetrominoes.append(tetromino)
        
        if not tetrominoes:
            # 対応するテトロミノがない場合はランダム
            return Tetromino.create(random.randint(0, 6))
        
        # 1つのテトロミノの場合はそのまま返す
        if len(tetrominoes) == 1:
            return tetrominoes[0]
        
        # 複数のテトロミノがある場合は合体させる
        combined_grid = self._merge_tetrominoes(tetrominoes)
        
        # 合体したグリッドからテトロミノを作成
        rotations = self._create_rotations(combined_grid)
        
        # テトロミノタイプは最初の物体のものを使用
        first_type = tetrominoes[0].type
        tetromino = Tetromino(rotations, first_type)
        
        # 現状と同じ場合は既存のテトロミノタイプを保持
        if self.shared_tetromino is not None and self.shared_tetromino.equals_current_shape(tetromino):
            tetromino.type = self.shared_tetromino.type
        
        return tetromino
        
    def _merge_tetrominoes(self, tetrominoes):
            """高速なテトロミノ合体処理"""
            if len(tetrominoes) == 0:
                return np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int32)
            elif len(tetrominoes) == 1:
                return self._place_single_tetromino_fast(tetrominoes[0])
            elif len(tetrominoes) == 2:
                return self._merge_two_tetrominoes_fast(tetrominoes[0], tetrominoes[1])
            elif len(tetrominoes) == 3:
                return self._merge_three_tetrominoes_fast(tetrominoes[0], tetrominoes[1], tetrominoes[2])
            else:
                # 3つ以上は最初の3つのみ使用
                return self._merge_three_tetrominoes_fast(tetrominoes[0], tetrominoes[1], tetrominoes[2])
    
    def _place_single_tetromino_fast(self, tetromino):
        """単一テトロミノの高速配置"""
        combined_grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int32)
        shape = np.array(tetromino.get_shape())
        h, w = shape.shape
        
        # 左上優先で配置（中央寄せ計算を省略）
        end_y = min(h, self.GRID_SIZE)
        end_x = min(w, self.GRID_SIZE)
        
        for y in range(end_y):
            for x in range(end_x):
                if shape[y, x] == 1:
                    combined_grid[y, x] = 1
        
        return combined_grid
    
    def _merge_two_tetrominoes_fast(self, tetromino1, tetromino2):
        """2つのテトロミノの高速合体"""
        shape1 = np.array(tetromino1.get_shape())
        shape2 = np.array(tetromino2.get_shape())
        h1, w1 = shape1.shape
        h2, w2 = shape2.shape
        
        # 事前定義パターンを高速テスト（最大5パターンのみ）
        for i, (pos1, pos2) in enumerate(self.two_piece_patterns[:5]):
            if self._can_place_fast(shape1, pos1, h1, w1) and self._can_place_fast(shape2, pos2, h2, w2):
                grid = self._place_two_shapes_fast(shape1, shape2, pos1, pos2)
                overlap_count = self._count_overlaps_fast(shape1, shape2, pos1, pos2)
                
                # 重なりが2個以下なら即座に採用（高速化）
                if overlap_count <= 2:
                    return grid
        
        # パターンマッチしない場合は単純配置
        return self._simple_placement([shape1, shape2])
    
    def _merge_three_tetrominoes_fast(self, tetromino1, tetromino2, tetromino3):
        """3つのテトロミノの高速合体"""
        shapes = [np.array(t.get_shape()) for t in [tetromino1, tetromino2, tetromino3]]
        
        # 事前定義パターンを高速テスト（最大3パターンのみ）
        for pattern in self.three_piece_patterns[:3]:
            if self._test_three_pattern_fast(shapes, pattern):
                return self._place_three_shapes_fast(shapes, pattern)
        
        # パターンマッチしない場合は単純配置
        return self._simple_placement(shapes)
    
    def _can_place_fast(self, shape, pos, h, w):
        """高速境界チェック"""
        pos_y, pos_x = pos
        return pos_y + h <= self.GRID_SIZE and pos_x + w <= self.GRID_SIZE
    
    def _count_overlaps_fast(self, shape1, shape2, pos1, pos2):
        """高速重なりカウント（完全チェックを省略）"""
        pos1_y, pos1_x = pos1
        pos2_y, pos2_x = pos2
        
        # 大まかな重なり推定（詳細計算を省略）
        h1, w1 = shape1.shape
        h2, w2 = shape2.shape
        
        # 境界ボックスの重なりチェック
        if (pos1_y + h1 <= pos2_y or pos2_y + h2 <= pos1_y or 
            pos1_x + w1 <= pos2_x or pos2_x + w2 <= pos1_x):
            return 0  # 重なりなし
        
        # 重なりありの場合は概算値を返す
        overlap_area = min(pos1_y + h1, pos2_y + h2) - max(pos1_y, pos2_y)
        overlap_area *= min(pos1_x + w1, pos2_x + w2) - max(pos1_x, pos2_x)
        return max(0, overlap_area // 2)  # 概算重なりセル数
    
    def _place_two_shapes_fast(self, shape1, shape2, pos1, pos2):
        """2つの形状の高速配置"""
        grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int32)
        
        # 形状1を配置
        self._place_shape_on_grid(grid, shape1, pos1)
        # 形状2を配置（重なりを許可）
        self._place_shape_on_grid(grid, shape2, pos2)
        
        return grid
    
    def _place_three_shapes_fast(self, shapes, pattern):
        """3つの形状の高速配置"""
        grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int32)
        
        for shape, pos in zip(shapes, pattern):
            self._place_shape_on_grid(grid, shape, pos)
        
        return grid
    
    def _place_shape_on_grid(self, grid, shape, pos):
        """グリッドに形状を配置（高速版）"""
        pos_y, pos_x = pos
        h, w = shape.shape
        
        end_y = min(pos_y + h, self.GRID_SIZE)
        end_x = min(pos_x + w, self.GRID_SIZE)
        
        for y in range(max(0, pos_y), end_y):
            for x in range(max(0, pos_x), end_x):
                shape_y, shape_x = y - pos_y, x - pos_x
                if shape_y < h and shape_x < w and shape[shape_y, shape_x] == 1:
                    grid[y, x] = 1
    
    def _test_three_pattern_fast(self, shapes, pattern):
        """3つのパターンの高速テスト"""
        for shape, pos in zip(shapes, pattern):
            h, w = shape.shape
            if not self._can_place_fast(shape, pos, h, w):
                return False
        return True
    
    def _simple_placement(self, shapes):
        """単純配置（フォールバック）"""
        grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE), dtype=np.int32)
        
        # 左上から順次配置（最も高速）
        positions = [(0, 0), (0, 2), (2, 0), (2, 2)]
        
        for i, shape in enumerate(shapes):
            if i < len(positions):
                pos = positions[i]
            else:
                pos = (0, 0)  # デフォルト位置
            
            self._place_shape_on_grid(grid, shape, pos)
        
        return grid
    
    def _create_occupancy_grid(self, keypoints, img_width, img_height):
        """複数の人物のキーポイントからグリッドの占有状態を作成"""
        # 4x4のグリッドを初期化（すべて0）
        grid = np.zeros((AICamera.GRID_SIZE, AICamera.GRID_SIZE), dtype=np.int32)
        
        valid_keypoints_found = False
        
        # すべての人物のキーポイントを処理
        for person_kp in keypoints:
            for i, kp in enumerate(person_kp):
                # 信頼度が閾値以上のキーポイントのみ処理
                if kp[2] >= AICamera.KEYPOINT_THRESHOLD:
                    # 顔のキーポイント（0-4）の場合は鼻（0）のみ使用
                    if i <= 4:
                        if i == 0:  # 鼻のみ処理
                            grid_x, grid_y = self._get_grid_position(kp, img_width, img_height)
                            grid[grid_y, grid_x] = 1
                            valid_keypoints_found = True
                    else:  # 体のキーポイント
                        grid_x, grid_y = self._get_grid_position(kp, img_width, img_height)
                        grid[grid_y, grid_x] = 1
                        valid_keypoints_found = True

        # 有効なキーポイントが見つからなかった場合はNoneを返す
        if not valid_keypoints_found or np.sum(grid) == 0:
            return None  

        rotations = self._create_rotations(grid)
        tetromino = Tetromino(rotations, 7 + random.choice(list(range(7))))
    
        # 現状と同じ場合
        if self.shared_tetromino is not None and self.shared_tetromino.equals_current_shape(tetromino):
            tetromino.type = self.shared_tetromino.type
        
        return tetromino
    
    def _create_rotations(self, grid):
        """グリッドとその90度、180度、270度回転を含む配列を作成"""
        rotations = [grid.copy()]
        
        for i in range(3):  # 90度、180度、270度の回転を作成
            rotations.append(self._rotate_grid_90(rotations[-1]))
        
        return rotations
    
    def _rotate_grid_90(self, grid):
        """グリッドを90度時計回りに回転"""
        return np.rot90(grid, k=1, axes=(1, 0))

    # Pyxel描画
    def get_frame(self):
        with self.lock:
            frame = self.shared_frame.copy() if self.shared_frame is not None else None
        return frame

    def get_tetromino(self):
        if self.shared_tetromino is None:
            return None

        tetromino = self.shared_tetromino.copy()
        return tetromino