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
    CAMERA_SIZE_H_W = (320, 240)

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

        # model = "/usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk"
        # self.imx500 = IMX500(model)
        # self.intrinsics = self.imx500.network_intrinsics or NetworkIntrinsics()        
        # if self.intrinsics.inference_rate is None:
        #      self.intrinsics.inference_rate = 10
        # if self.intrinsics.labels is None:
        #      with open("assets/coco_labels.txt", "r") as f:
        #          self.intrinsics.labels = f.read().splitlines()
        # self.intrinsics.update_with_defaults()
        
        # self.imx500.show_network_fw_progress_bar()
        
        # self.picam2 = Picamera2()
        # config = self.picam2.create_preview_configuration(
        #     main={"format": "RGB888", "size": (320, 240)},
        #     controls={"FrameDurationLimits": (33333, 33333)},
        #     buffer_count=6
        # )
        # self.picam2.configure(config)
        # self.picam2.post_callback = self.camera_callback

        self.imx500 = IMX500("/usr/share/imx500-models/imx500_network_higherhrnet_coco.rpk")
        intrinsics = self.imx500.network_intrinsics or NetworkIntrinsics()
        if intrinsics.inference_rate is None:
            intrinsics.inference_rate = 10
        if intrinsics.labels is None:
            with open("assets/coco_labels.txt", "r") as f:
                intrinsics.labels = f.read().splitlines()
        intrinsics.update_with_defaults()

        self.picam2 = Picamera2(self.imx500.camera_num)
        config = self.picam2.create_preview_configuration(
            main={"format": "RGB888", "size": AICamera.CAMERA_SIZE_H_W},
            controls={'FrameRate': 30}, 
            buffer_count=12)
        #self.imx500.show_network_fw_progress_bar()
        self.picam2.start(config, show_preview=False)
        self.imx500.set_auto_aspect_ratio()
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

        boxes, scores, keypoints = self._ai_output_tensor_parse(request.get_metadata())
        with MappedArray(request, stream='main') as m:
            # キーポイントからブロックを生成して描画
            if keypoints is not None and len(keypoints) > 0:
                img_height, img_width = m.array.shape[:2]
                self.shared_tetromino = self._create_occupancy_grid(keypoints, img_width, img_height)

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

    def _ai_output_tensor_parse(self, metadata: dict):
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
    
    def _get_grid_position(self, keypoint, img_width, img_height):
        """
        キーポイントの位置をグリッド上の座標に変換する
        キーポイントは正規化して離散化することで、同じポーズなら同じグリッド位置になるようにする
        """
        # COCOの17キーポイント：
        # 0: 鼻, 1-4: 目と耳(左右), 5: 左肩, 6: 右肩, 7: 左肘, 8: 右肘, 
        # 9: 左手首, 10: 右手首, 11: 左腰, 12: 右腰, 13: 左膝, 14: 右膝,
        # 15: 左足首, 16: 右足首
        
        x, y, confidence = keypoint
        
        # 画像サイズに対して相対的な位置を計算（0〜1の範囲）
        norm_x = min(max(x / img_width, 0), 1)
        norm_y = min(max(y / img_height, 0), 1)
        
        # グリッド座標に変換（0〜GRID_SIZE-1の範囲）
        grid_x = min(int(norm_x * AICamera.GRID_SIZE), AICamera.GRID_SIZE - 1)
        grid_y = min(int(norm_y * AICamera.GRID_SIZE), AICamera.GRID_SIZE - 1)
        
        return grid_x, grid_y
    
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
    
        # # 現状と同じ場合
        if not self.shared_tetromino == None and self.shared_tetromino.equals_current_shape(tetromino):
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

        if self.shared_tetromino == None:
            return None

        tetromino = self.shared_tetromino.copy()
        return tetromino