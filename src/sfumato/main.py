import numpy as np
import os
import sys
import time
import matplotlib.pyplot as plt

from sfumato import settings
from sfumato.transmitter import FmTransmitter
from sfumato.receiver import FmReceiver
from sfumato.channnel import add_awgn
from sfumato.component.radio_ui import RadioUI
from sfumato.utils.load_and_preprocess_wav import load_and_preprocess_wav
from sfumato.utils.output_audio import save_audio
from sfumato.utils.audio_source import AudioSource


def main():
    # --- UI起動 ---
    RadioUI.header()

    # --- 設定 ---
    INPUT_FILE = settings.INPUT_FILE
    base_name = os.path.splitext(os.path.basename(INPUT_FILE))[0]
    OUTPUT_FILE = f"outputs/{base_name}_restored.wav"
    TARGET_SNR = settings.DEFAULT_SNR_DB

    # テスト音源生成
    if not os.path.exists(INPUT_FILE):
        RadioUI.log(
            "SYSTEM",
            "Input file missing. Generating Stereo Time Signal...",
            RadioUI.YELLOW,
        )
        source = AudioSource()
        # ステレオ時報の生成 (L=Low, R=High)
        melody = source.stereo_time_tone()
        save_audio(melody, fs=48000, filename=INPUT_FILE)

    # --- 1. 送信機 (Transmitter) ---
    print(f"\n{RadioUI.BOLD}--- [1] Transmitter Station ---{RadioUI.RESET}")
    RadioUI.log(
        "PREPROCESS", f"Loading '{os.path.basename(INPUT_FILE)}'...", RadioUI.BLUE
    )

    # ステレオWAVの読み込み (N, 2)
    audio_data = load_and_preprocess_wav(INPUT_FILE, settings.AUDIO_FS)

    RadioUI.log("MODULATION", "FM Stereo Modulation in progress...", RadioUI.BLUE)
    tx = FmTransmitter()
    rf_signal = tx.modulate(audio_data)

    RadioUI.on_air_animation(duration=2)

    # --- 2. 通信路 (Channel) ---
    print(f"{RadioUI.BOLD}--- [2] Wireless Channel ---{RadioUI.RESET}")
    RadioUI.log("CHANNEL", f"Applying AWGN (SNR={TARGET_SNR}dB)...", RadioUI.YELLOW)

    # ノイズ付加
    noisy_rf_signal = add_awgn(rf_signal, TARGET_SNR)
    time.sleep(1)

    # --- 3. 受信機 (Receiver) ---
    print(f"\n{RadioUI.BOLD}--- [3] Receiver Device ---{RadioUI.RESET}")
    RadioUI.tuning_animation()

    rx = FmReceiver()

    # A. RF信号 -> MPX信号 (192kHz)
    RadioUI.log("DEMODULATION", "Quadrature Demodulation to MPX...", RadioUI.CYAN)
    mpx_signal = rx.process(noisy_rf_signal)

    # B. パイロット抽出 & キャリア再生
    RadioUI.log("STEREO", "Recovering 38kHz Sub-carrier...", RadioUI.CYAN)
    carrier_38k = rx._recover_carrier(mpx_signal)

    # C. ステレオ分離 (Matrix Decoding)
    RadioUI.log("STEREO", "Decoding L/R Channels...", RadioUI.CYAN)
    demodulated_audio = rx._stereo_decode(mpx_signal, carrier_38k)

    # --- 4. 保存 ---
    print(f"\n{RadioUI.BOLD}--- [4] Output ---{RadioUI.RESET}")
    RadioUI.log("IO", f"Saving audio to {OUTPUT_FILE}", RadioUI.GREEN)

    # normalize=Falseにして、入力と音量レベルを比較しやすくする
    save_audio(demodulated_audio, rx.audio_fs, OUTPUT_FILE, normalize=True, gain=0.9)
    RadioUI.reception_success(OUTPUT_FILE)

    # --- 5. グラフ表示 (ステレオ対応版) ---
    try:
        RadioUI.log("VISUALIZER", "Generating Stereo Analysis Graph...", RadioUI.DIM)

        # ヘルパー関数: 確実に (N, 2) に整形して L, R を返す
        def split_channels(data):
            # 1次元 (N,) -> モノラル (L=R)
            if data.ndim == 1:
                return data, data
            # 2次元 (N, 2) -> ステレオ
            elif data.ndim == 2 and data.shape[1] == 2:
                return data[:, 0], data[:, 1]
            # 2次元 (N, 1) -> モノラル
            elif data.ndim == 2 and data.shape[1] == 1:
                flat = data.flatten()
                return flat, flat
            else:
                raise ValueError(f"Unexpected data shape: {data.shape}")

        # 入力と出力を安全に分離
        in_l, in_r = split_channels(audio_data)
        out_l, out_r = split_channels(demodulated_audio)

        # プロット開始
        plt.figure(figsize=(14, 10))
        limit = 1000  # 拡大表示するサンプル数 (先頭1000サンプル)

        # 時間軸 (ms)
        t_axis = np.arange(limit) / settings.AUDIO_FS * 1000

        # --- [左上] Left Ch 時間波形 ---
        plt.subplot(2, 2, 1)
        plt.plot(t_axis, in_l[:limit], label="In (L)", color="blue", alpha=0.5)
        plt.plot(
            t_axis,
            out_l[:limit],
            label="Out (L)",
            color="cyan",
            alpha=0.8,
            linestyle="--",
        )
        plt.title("Left Channel (Time Domain)")
        plt.xlabel("Time [ms]")
        plt.ylabel("Amplitude")
        plt.legend(loc="upper right")
        plt.grid(True, alpha=0.3)

        # --- [右上] Right Ch 時間波形 ---
        plt.subplot(2, 2, 2)
        plt.plot(t_axis, in_r[:limit], label="In (R)", color="red", alpha=0.5)
        plt.plot(
            t_axis,
            out_r[:limit],
            label="Out (R)",
            color="orange",
            alpha=0.8,
            linestyle="--",
        )
        plt.title("Right Channel (Time Domain)")
        plt.xlabel("Time [ms]")
        plt.legend(loc="upper right")
        plt.grid(True, alpha=0.3)

        # --- [左下] Left Ch 周波数特性 (PSD) ---
        plt.subplot(2, 2, 3)
        plt.title("Left Channel (PSD)")
        plt.psd(in_l, Fs=settings.AUDIO_FS, NFFT=1024, color="blue", label="In (L)")
        plt.psd(
            out_l,
            Fs=settings.AUDIO_FS,
            NFFT=1024,
            color="cyan",
            label="Out (L)",
            linestyle="--",
        )
        plt.xlim(0, 15000)
        plt.legend(loc="upper right")

        # --- [右下] Right Ch 周波数特性 (PSD) ---
        plt.subplot(2, 2, 4)
        plt.title("Right Channel (PSD)")
        plt.psd(in_r, Fs=settings.AUDIO_FS, NFFT=1024, color="red", label="In (R)")
        plt.psd(
            out_r,
            Fs=settings.AUDIO_FS,
            NFFT=1024,
            color="orange",
            label="Out (R)",
            linestyle="--",
        )
        plt.xlim(0, 15000)
        plt.legend(loc="upper right")

        plt.tight_layout()

        # 保存と表示
        image_filename = f"outputs/{base_name}_analysis.png"
        plt.savefig(image_filename)
        RadioUI.log("IO", f"Graph saved to {image_filename}", RadioUI.GREEN)
        plt.show()

    except Exception as e:
        import traceback

        traceback.print_exc()
        RadioUI.log("ERROR", f"Graph generation failed: {e}", RadioUI.RED)


if __name__ == "__main__":
    main()
