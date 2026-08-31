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


# --- 音声再生フィルタ (Audio Reconstruction / 192k→48k 間引き FIR) ---
# 復調後の音声を帯域制限しつつ 48kHz へ間引く FIR の設計仕様(roadmap 1.7 H1)。
# 阻止端を PILOT_FREQ(19k)未満に置き、パイロット漏れ込みを 60dB 以上削る。
# 高次 IIR を避け FIR を採る(線形位相・固定小数点に強く、ポリフェーズ間引きは将来 HW に移植しやすい)。
AUDIO_BAND_HZ = 15_000  # 通過端 [Hz]: 音声上限
AUDIO_LPF_STOP_HZ = 18_000  # 阻止端 [Hz]: PILOT_FREQ 未満に置く
AUDIO_LPF_STOP_ATTEN_DB = 60.0  # 阻止量 [dB]


# --- ステレオ復調(線形位相 FIR・遅延整合)roadmap 1.5.3 ---
# 副搬送波(L-R を載せた DSB-SC)の帯域と、main/sub を遅延整合させるための線形位相 FIR。
# IIR の非線形位相が「副搬送波=2×パイロット」関係と main/sub の打ち消しを壊すため、
# ここだけ位相重視で FIR にする(音質系の IIR は据え置き=適材適所)。
SUB_BAND_LOW_HZ = 23_000  # 副搬送波帯の下端 [Hz]
SUB_BAND_HIGH_HZ = 53_000  # 上端 [Hz]
STEREO_FIR_TAPS = (
    255  # main LPF / sub BPF の FIR タップ数(奇数=線形位相、同長で群遅延一致)
)
# 38kHz 再生搬送波の位相補正 [rad]。経路の群遅延ぶん副搬送波が位相回転するのを補う。
# 値は実測で確定(240deg。フィルタ群遅延で決まり PLL 帯域には依存しない)。
# フィルタ構成(STEREO_FIR_TAPS 等)を変えたら取り直す。±10deg で約 6dB 落ちる。
STEREO_CARRIER_PHASE_RAD = 4.1888


# --- RF帯域 (Radio Frequency) ---
RF_FS = 2_304_000  # 2.3MHz = MPX(192k) * 12


# --- FM放送規格 (FM Standards) ---

# 搬送波周波数 (Carrier Frequency)
# シミュレーション用に低く設定(実放送帯 76–95 MHz の受信は将来 HW に移植する場合の課題)
CARRIER_FREQ = 250_000  # 250 kHz

# 最大周波数偏移 (Maximum Frequency Deviation)
# 日本のFM放送規格に準拠 (+/- 75kHz Wide FM)
MAX_DEVIATION = 75_000

# 時定数
# 日本のFM放送規格に準拠 (50 \mu s)
TIME_CONSTANT = 50e-6


# --- 受信フロントエンド (Channel Select / イメージ除去) ---
# 複素ミキシング後・判別器前に置くチャネル選択 LPF。実信号を複素 LO で混ぜると
# 2*CARRIER_FREQ(=500kHz)に像が出るので、これを除去してから位相を取る。
# 側波帯(Carson ≈ 2*(MAX_DEVIATION + 53k) ≈ 256kHz、片側 ≈ 128kHz)は残し、
# 500kHz の像は落とす位置に置く(将来 HW に移植する場合は DDC のチャネル選択フィルタに相当)。
IF_LPF_CUTOFF_HZ = 250_000  # チャネル選択 LPF カットオフ [Hz]
IF_LPF_ORDER = 6  # Butterworth 次数(2.3M 段なので低次。将来の HW 移植にも軽い)


# --- 制御ループ定数 (PLL Settings) ---

# PLL (Phase Locked Loop) 用の設定
# ノイズ除去と追従性のバランスを決める
# ループ帯域幅 (Hz): 狭いほどノイズに強いが、追従が鈍り NCO の定常位相誤差 ε が残る。
# ステレオ検波では ε が 38kHz で 2ε に拡大し分離を律速するため、高 SNR では広めが有利
# (実測: 50Hz→38dB / 120Hz→42dB / 200Hz→45dB)。低 SNR でのノイズ耐性とのトレードオフ。
PLL_BANDWIDTH = 200.0
PLL_DAMPING = 1.2  # ダンピング係数 (zeta): 0.707が最も応答が良い


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

# シミュレーション入力音源(プロジェクトルート基準の相対パス。main.py で root に解決)
INPUT_FILE = "inputs/first_ancem92.wav"


# --- 品質評価・ゲート (roadmap 1.7) ---
# 方針・しきい値の根拠は docs/adr/adr-005-demod-quality-gate.md が正本。

# characterize の測定条件(変えると baseline は無効)
EVAL_TONE_FREQ = 1_000.0  # 評価トーン [Hz]: コヒーレント (48000/1000=48 周期)
EVAL_DURATION_S = 1.0  # 測定長 [秒]
EVAL_SNR_DB = DEFAULT_SNR_DB  # 評価時の SN比 [dB]
EVAL_SEED = 12_345  # AWGN シード(再現性)

# 絶対しきい値ゲート(目標 = 市販製品スペック。None はスキップ)
THD_MAX = 0.003  # THD 上限 [線形比]
SEPARATION_MIN_DB = 42.0  # L-R セパレーション下限 [dB]
SINAD_MIN_DB = 75.0  # SINAD 下限 [dB]
PLL_LOCK_MAX_S = None  # PLL ロック時間上限 [秒](観測値から確定)

# PLL ロック時間メトリクスのパラメータ(None ならロック計測をスキップ)
PLL_LOCK_TOL = None  # ロック判定の |error| 上限
PLL_LOCK_HOLD_SAMPLES = None  # ロック継続とみなす連続サンプル数

# 回帰ゲートの許容幅(ハードゲート。環境差ドリフトの吸収分)
REGRESSION_TOL = 0.02  # 許容幅 [割合]: 2%
