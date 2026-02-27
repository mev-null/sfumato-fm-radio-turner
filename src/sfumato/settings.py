"""
Sfumato Radio - Global Configuration
プロジェクト全体で共有する物理定数・シミュレーション設定
"""

# --- オーディオ・MPX帯域 (Audio & Multiplex) ---

# 音声帯域 (Audio Baseband)
AUDIO_FS = 48_000

# MPX信号を作るための中間レート
# ステレオ信号は最大53kHzまであるため、最低で106kHz必要
MPX_FS = 192_000  # 192 kHz = 48k * 4 (b'100)

# ステレオ規格
PILOT_FREQ = 19_000  # 19 kHz
SUB_FREQ = 38_000  # 38 kHz (19k * 2)


# --- RF帯域 (Radio Frequency) ---
RF_FS = 2_304_000  # 2.3MHz = MPX(192k) * 12


# --- FM放送規格 (FM Standards) ---

# 搬送波周波数 (Carrier Frequency)
# シミュレーション用に低く設定（本番では81.3MHzを受信する）
CARRIER_FREQ = 250_000  # 250 kHz

# 最大周波数偏移 (Maximum Frequency Deviation)
# 日本のFM放送規格に準拠 (+/- 75kHz Wide FM)
MAX_DEVIATION = 75_000

# 時定数
# 日本のFM放送規格に準拠 (50 \mu s)
TIME_CONSTANT = 50e-6


# --- 派生定数 (Derived Constants) ---

# デシメーション係数 (Decimation Factor)
# RF -> MPX (受信機で最初に落とすレート)
RF_TO_MPX_FACTOR = int(RF_FS // MPX_FS)  # 2304000 / 192000 = 12

# MPX -> Audio (最後に落とすレート)
MPX_TO_AUDIO_FACTOR = int(MPX_FS // AUDIO_FS)  # 192000 / 48000 = 4

# ナイキスト周波数 (RF)
RF_NYQUIST = RF_FS / 2

# デフォルトのSN比 (シミュレーション用)
DEFAULT_SNR_DB = 40.0

# シミュレーション入力音源
INPUT_FILE = "first_ancem92.wav"
