class Config:
    CAMERA = False  # カメラ機能を有効にするか
    GHOST = False   # ゴースト機能を有効にするか
    CLEAR_PARTICLES = True  # パーティクルエフェクトを有効にするかどうか
    CLEAR_EFFECT = True  # ライン消去エフェクトを有効にするかどうか

    # ゲームのスクリーンサイズ
    SCREEN_WIDTH = 240
    SCREEN_HEIGHT = 240
    SCREEN_CAMERA_WIDTH = 480

    # カメラ映像表示のサイズ
    CAMERA_VIEW_WIDTH = 200
    CAMERA_VIEW_HEIGHT = 200

    # カメラのサイズ
    CAMERA_WIDTH = 320
    CAMERA_HEIGHT = 240

    # デモ（自動プレイ）開始までの待機時間（秒）
    DEMO_IDLE_SEC = 120

    # オートプレイの速度設定（フレーム数）
    AUTO_MOVE_DELAY = 10   # 横移動・回転の遅延（推奨: 2-5）
    AUTO_DROP_DELAY = 10   # ドロップ前の待機時間（推奨: 5-15）
    AUTO_SPAWN_DELAY = 10  # 新ピース出現時の待機時間（推奨: 5-15）