# 学習インデックス — Roadmap 1.8(因果・ストリーミング参照モデル化)

各実装段階で「何を学ぶか」を引くためのインデックス。**進捗の正本は [roadmap.md](roadmap.md)**、設計の現状は [architecture.md](architecture.md)、方式決定は [adr/](adr/)。ここは進捗を繰り返さず、概念・コード・調べるキーワードへのリンク集に徹する。

## 1.8 の目的

受信機を「配列一括処理の非因果モデル」から「1 サンプルずつ・状態を持つ因果モデル」へ書き換え、固定小数点化(Phase 2.3)→ HDL 実装の土台にする。非因果・全体依存だった 4 点(`np.unwrap` 判別器 / `decimate` のゼロ位相 / 一括 LO / ブロック max 正規化)を解消する。

不変条件: 任意のブロック分割で `concat(f(x_1),…) == f(x)`。一致の強さは経路で異なる(IIR・遅延・ミキサ・判別器の自己一致 = bitwise / FIR・間引き = `rtol=1e-12`)。

## 現状スナップショット(正本は roadmap / TodoList)

| 段階 | ファイル | 状態 |
|---|---|---|
| 課題1 FIR | [fir.py](../src/algo/dsp/fir.py) | 完了 (6/6) |
| 課題2 純遅延 | [delay.py](../src/algo/dsp/delay.py) | 完了 (6/6) |
| 課題3 IIR | [iir.py](../src/algo/dsp/iir.py) | 実装中 |
| 課題4 ミキサ | [mixer.py](../src/algo/radio/mixer.py) | 未 |
| 課題5 判別器 | [discriminator.py](../src/algo/radio/discriminator.py) | 未 |
| 課題6 間引き | [decimator.py](../src/algo/dsp/decimator.py) | 未 |
| 統合 step4–7 | [receiver.py](../src/algo/radio/receiver.py) | 未 |

---

## 学習インデックス(段階別)

各段階: **概念 / コード / 調べるキーワード / HW 対応(2.3 で深掘り)**。

### 課題1 — 状態付き FIR

- **概念**: FIR フィルタ、畳み込み `y[n]=Σh[k]x[n−k]`、線形位相と群遅延、状態 = タップ遅延線(直近 N−1 入力)。
- **コード**: [fir.py](../src/algo/dsp/fir.py)、係数設計 [filters.py](../src/algo/dsp/filters.py) `design_audio_decimation_fir`。
- **キーワード**: FIR filter, group delay, linear phase, `scipy.signal.lfilter` の `zi`、overlap-save。
- **学びの要点**: FIR は scipy が `np.convolve` 一括に切り替わるため**加算順序が配列長依存 → bitwise 不可**(`rtol=1e-12`)。空ブロックは要ガード。
- **HW**: シフトレジスタ + 積和(MAC)、係数 ROM。

### 課題2 — 純遅延(DelayLine)

- **概念**: 純遅延 `y[n]=x[n−D]`(伝達関数 `z^−D`)、FIFO 状態、群遅延整合。
- **コード**: [delay.py](../src/algo/dsp/delay.py)、用途は [receiver.py](../src/algo/radio/receiver.py) `_stereo_decode`(main を D 遅らせ sub と総遅延 2D に揃える)。
- **キーワード**: pure delay, FIFO, group delay matching。
- **学びの要点**: `reset` は値を返すのではなく状態へ**代入**。
- **HW**: シフトレジスタ / BRAM。

### 課題3 — 状態付き IIR

- **概念**: IIR(フィードバック、極、無限インパルス応答)、1-pole ローパス = de-emphasis = 漏れ積分器、双一次変換(アナログ時定数 τ → デジタル係数)、直接形 I / II / **転置直接 II 型**と正準形。
- **コード**: [iir.py](../src/algo/dsp/iir.py)、[emphasis.py](../src/algo/dsp/emphasis.py)(de-emphasis 1 次)、[receiver.py](../src/algo/radio/receiver.py) `_channel_select`(6 次 Butterworth、複素 IQ)。
- **キーワード**: IIR feedback, poles/zeros, bilinear transform, direct form II transposed, Butterworth, complex filtering。
- **学びの要点**: `len(a)≥2` だと scipy は C 逐次ループ → **bitwise 一致**(FIR との対比)。複素 IQ には複素 `zi`。
- **HW(2.3 伏線)**: 6 次単段は固定小数点で脆い → **SOS(2 次節)カスケード**を検討。

### 課題4 — 複素ミキサ(BasebandMixer)

- **概念**: 複素ミキシング/ヘテロダイン、デジタルダウンコンバージョン(DDC)、実信号×複素 LO で生じる 2fc 像 → チャネル選択の必要性、位相アキュムレータ。
- **コード**: [mixer.py](../src/algo/radio/mixer.py)、現行 [receiver.py](../src/algo/radio/receiver.py) `_mix_to_baseband`。
- **キーワード**: heterodyne, DDC, NCO, phase accumulator, image rejection。
- **学びの要点**: 状態は**整数の通算サンプル番号**(浮動小数点位相の累積はドリフトして bitwise が崩れる)。
- **HW**: 位相アキュムレータ + sin/cos LUT(または CORDIC)。`fc/fs=125/1152` は有理数 → mod-1152 カウンタ。

### 課題5 — I/Q 差分形判別器

- **概念**: FM 復調原理(瞬時周波数 = `dφ/dt`)、共役積 `z[n]·conj(z[n−1])` で絶対位相を消す、atan2 と主値、`|Δφ|<π` なら unwrap 不要。
- **コード**: [discriminator.py](../src/algo/radio/discriminator.py)、現行 [receiver.py](../src/algo/radio/receiver.py) `_demodulate`(`np.unwrap` 版)。
- **キーワード**: FM discriminator, instantaneous frequency, quadrature demod, cross-product discriminator, atan2 principal value。
- **学びの要点**: 状態は `z_prev` 1 語、先頭種付けで `y[0]=0`。unwrap 形との一致は経路差のため `atol=1e-9`。
- **HW**: atan2 → **CORDIC(vectoring mode)**(2.3)。

### 課題6 — ポリフェーズ間引き(PolyphaseDecimator)

- **概念**: デシメーション(帯域制限 + 間引き)、エイリアシング、ポリフェーズ分解 `h_p[k]=h[kM+p]`(乗算を出力レート化)、位相カウンタと可変長出力。
- **コード**: [decimator.py](../src/algo/dsp/decimator.py)、現行 [receiver.py](../src/algo/radio/receiver.py) `_decimate`(`signal.decimate`)。
- **キーワード**: decimation, anti-aliasing, polyphase, noble identity, multirate DSP。
- **学びの要点**: `scipy.signal.decimate` の既定 `zero_phase=True` は **filtfilt 相当の非因果**(1.8 で因果化)。ブロック長は任意(M 未満なら出力 0)。
- **HW**: mod-M カウンタ + MAC、**valid ストローブ**(M に 1 回データが立つ)。多段間引きは roadmap の宿題。

### 統合 step4–7 — ストリーミング・パイプライン

- **概念**: 状態のクロストーク回避(**1 適用箇所 = 1 インスタンス**)、レート域(RF 2.304M / MPX 192k / 音声 48k)、レイテンシ予算、golden モデル ↔ テストベンチのオラクル、baseline ラチェットと回帰ゲート。
- **コード**: [receiver.py](../src/algo/radio/receiver.py)、評価 [eval/harness.py](../src/algo/eval/harness.py)・[eval/metrics.py](../src/algo/eval/metrics.py)・[tests/test_quality_gate.py](../tests/test_quality_gate.py)。
- **キーワード**: streaming pipeline, AXI-Stream valid/ready, latency budget, golden reference model, regression gate。
- **学びの要点**: step6 の間引き因果化のみ baseline を 1 回更新(`make characterize`)。他は bitwise / ε 中立。

---

## 横断トピック(Phase 2.3 以降で深掘り)

- **固定小数点**: Q フォーマット、語長設計、量子化雑音、オーバーフロー/丸め、SOS カスケード。語長は ADC/DAC ビット幅で決まる(RF 方式 [adr-001](adr/adr-001-rf-frontend-low-if-adc.md))。
- **マルチレート信号処理**: ポリフェーズ、Noble identity、多段間引き。
- **検証フロー**: golden float → ビット精密固定小数点 → RTL、各層を 1 つ前と照合。
- **業界ツール**(大学 MATLAB ライセンス活用、適期は 2.3): Simulink、Fixed-Point Designer、HDL Coder(自動生成 RTL は**手書き RTL の照合用**に留める)。
- **音質メトリクス**: THD、SINAD、L–R セパレーション、PLL ロック時間(= オーディオエンジニアの共通言語)。[eval/metrics.py](../src/algo/eval/metrics.py)。

## 決定ログ(コード外の方針)

- **設計図**: 受信機データフロー図を Mermaid で作成予定([diagrams/](diagrams/)、PLL は [pll-block.mmd](diagrams/pll-block.mmd) が前例)。TikZ は文書清書のときだけ。
- **MATLAB/Simulink**: 投入は Phase 2.3、1.8 は Python の golden モデルのまま。
- **方式に関わる判断**(SOS 化 / CORDIC / 語長)は確定時に [adr/](adr/) へ。

## 参照

- 進捗: [roadmap.md](roadmap.md) / 設計: [architecture.md](architecture.md) / 方式: [adr/](adr/)
- 定数の正本: [settings.py](../src/algo/settings.py)
- ルール: [.claude/rules.md](../.claude/rules.md)
