"""
Sfumato Radio - Global Configuration
プロジェクト全体で共有する物理定数・シミュレーション設定
"""

# --- サンプリングレート (Sampling Rates) ---

# 音声帯域 (Audio Baseband)
AUDIO_FS = 48_000

# RF帯域 (Radio Frequency)
# シミュレーション負荷を考慮し、オーディオの「50倍」に設定
# 48kHz * 50 = 2.4 MHz
RF_FS = 2_400_000


# --- FM放送規格 (FM Standards) ---

# 搬送波周波数 (Carrier Frequency)
# シミュレーション用に低く設定（本番では81.3MHzを受信する）
CARRIER_FREQ = 100_000  # 100 kHz

# 最大周波数偏移 (Maximum Frequency Deviation)
# 日本のFM放送規格に準拠 (+/- 75kHz)
# シミュレーション時はナローバンドで実行
MAX_DEVIATION = 7_500


# --- 派生定数 (Derived Constants) ---

# デシメーション係数 (Decimation Factor)
# RF信号を何分の一に間引けばオーディオになるか
# 2,400,000 / 48,000 = 50
DECIMATION_FACTOR = int(RF_FS // AUDIO_FS)

# ナイキスト周波数 (RF)
RF_NYQUIST = RF_FS / 2

# デフォルトのSN比 (シミュレーション用)
DEFAULT_SNR_DB = 30.0
