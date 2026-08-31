# アルゴリズム解説(algo モデリング記録)

algo(Python/NumPy)で FM ステレオ変復調方式を確立する過程の記録。
全体像は [../README.md](../README.md)、信号設計の現状は [architecture.md](architecture.md)、物理定数・レートは `../src/algo/settings.py` を参照。

## 概要

時報の音声ファイルを

1. FM 信号に変調し、
2. IQ 信号に変換、
3. 最後に音声信号に復調した。

通信路では、ホワイトノイズ(ガウス雑音)が乗ることを仮定してモデルの構築を行なった。

### モデル全体のシミュレーション動画

https://github.com/user-attachments/assets/f829db6a-4b2d-4762-8efc-568c4f685ed2

## 1.1 Transmit

擬似的な音声信号(440Hz の正弦波)を生成し、その信号を FM 信号に変調、ガウス雑音を乗せるところまでのモデルとシミュレーションを行なった。

### 音声信号 → FM 変調

- アップサンプリングを行い、FM 変調を行なった
- サンプリングには線形補完を利用

### FM 変調信号にガウス雑音を乗せる

- アップサンプリング済みの信号の電力から、ノイズ信号の電力を計算
- ノイズ信号の電力からガウス雑音の正規分布を計算

### 雑音が混じった FM 信号を可視化

<img width="1211" height="811" alt="signal_noisy" src="https://github.com/user-attachments/assets/983cb61c-0654-4bc8-b545-12008f4f4705" />

- 直感的で暫定的な理解: キャリア周波数の前後に元信号が含まれている。ガウス雑音を乗せたことで、元信号 + ガウス雑音が周波数特性のピークに存在。SN 比を大きくすることでガウス雑音を消す。

## 1.2 Receive

FM 信号を受け取り、

1. 選局 (Mixing): 目的の周波数を 0Hz 中心に移動
2. 帯域制限 (Filtering): 信号以外の余計なノイズを除去
3. 間引き (Decimation): サンプリングレートを RF 帯域(2.4MHz)から音声帯域(48kHz)へ変換

を実行してベースバンド IQ 信号に変換するまでのモデリングとシミュレーションを行なった。

### Mixing

搬送波周波数分だけ複素平面上で負の方向に回転させる操作を行なった。

### ベースバンド IQ 信号の可視化

<img width="1211" height="811" alt="recieved_sign" src="https://github.com/user-attachments/assets/4a3a1f7f-169f-4de6-8bb8-556860d1ed62" />

#### c.f. 最大周波数偏移の修正

帯域制限を 20kHz に設定してシミュレーションを行なった。理由は、出力レートを 48kHz(音声帯域)に設定していたため。
しかし、最大周波数偏移 (Maximum Frequency Deviation) について、日本の FM 放送規格に準拠 (+/- 75kHz) して実装していたため、可視化時に期待される結果を得られなかった。
フィルタのカットオフ周波数(帯域制限)を 100kHz ほどに修正したかったが、ベースバンド IQ 信号は 48kHz を期待しているため、最大周波数偏移を 7.5kHz に落として実装した。
実際の FM ラジオでは、2 段階で Decimation を行なっていることを知ったため、今後の実装課題になる。
[fix: 最大周波数遷移を下げた](https://github.com/mev-null/sfumato-fm-radio-tuner/pull/3/changes/afdc3e510589ab221ce63b8b71e9d62133b2f44d)

## 1.3 Demodulation

IQ 信号から位相変化を取り出し、音声に変換した。

### IQ 信号 → 位相

実部と虚部から正接の逆関数で計算。

### 位相 → 音声情報

位相を微分し、位相変化を計算。位相変化がそのまま音の周波数の一部になる。

### 復調された音声を可視化

<img width="1211" height="811" alt="output3" src="https://github.com/user-attachments/assets/5a5b3f1c-a1d5-492b-9918-5766e2ce95a9" />

それなりに元の信号と同じ形に復元できた。また、周波数特性も 440Hz に生じており、妥当。

この時点におけるモデルで時報音声を復調した際の結果は以下の通り。

- 変調前の信号
  [time-tone.wav](https://github.com/user-attachments/files/25239643/time-tone.wav)
- 復調後の信号
  [time-tone_restored.wav](https://github.com/user-attachments/files/25239641/time-tone_restored.wav)
  (ラジオ特有の雑音が混じっていることが確認できる)

## 1.4 Stereo Multiplexing

FM 変復調に、ステレオ音源が対応できるようになった。
シミュレーションに使用した信号は、L 成分が 440Hz, R 成分が 880Hz のステレオ信号。

<img width="857" height="393" alt="stereo_sine" src="https://github.com/user-attachments/assets/2b5e5257-e11e-4676-8d7c-e58ff5eda417" />

簡易的に、音声信号レート(48kHz)とラジオ波レート(約 2.4MHz)の双方向から decimation する過程において、中間に MPX 信号レート(192kHz)を設けた。

### 送信機

送信信号について、左右の信号から MPX 信号を生成する。

#### 手順

1. 音声信号レートから、MPX 信号レートに decimation
2. MPX 信号レートで上記の規則に従って信号を生成
3. 信号を RF レートに upsampling
4. FM 変調を行い、IQ 信号生成

<img width="1211" height="811" alt="fm-stereo-signal" src="https://github.com/user-attachments/assets/361cd65f-9424-4ac1-af2d-7238fedf39b6" />

#### MPX 信号とは?

モノラル成分に L+R の信号を、19kHz にパイロット信号を、38kHz のサブキャリアに L-R の信号を埋め込んだもの。
全てで 57kHz の帯域幅を必要とする。

<img width="1189" height="790" alt="mpx_signal" src="https://github.com/user-attachments/assets/adeb4c12-eb41-4f08-af76-472c83ad5d5c" />
<img width="1489" height="490" alt="mpx-pds" src="https://github.com/user-attachments/assets/bab0122c-3105-4f71-94da-6b07dcd81f6d" />

19kHz のパイロット信号を利用して、送信機と受信機の時間を同期させる。

### 通信路

ガウス雑音が乗るとしてモデリング。

<img width="1211" height="811" alt="fm-stereo-signal-awgn" src="https://github.com/user-attachments/assets/86c17e8e-4881-4053-9066-a530c76c38eb" />

### 復調機

#### MPX 信号に復調まで

1. RF 信号をベースバンドの IQ 信号にする
2. RF 信号レート帯で IQ 信号を MPX 信号に復調
3. RF 信号レートから MPX 信号レートに decimation

<img width="1211" height="811" alt="decimated_signal" src="https://github.com/user-attachments/assets/b5ade06a-ec35-4624-8dae-6d16c4a63fae" />

元信号の形状にかなり一致している。

#### 復調した MPX 信号をステレオ信号に分離

1. Main(L+R) の信号を抽出。(LPF(15kHz) を通した。)
2. Sub(L-R) の信号を抽出。
3. マトリクス回路に通して、二元一次連立方程式を解き、L, R 信号を抽出
4. MPX 信号レートから音声信号レートに decimation

<img width="1021" height="1035" alt="stereo-decode-process" src="https://github.com/user-attachments/assets/c508d596-df0f-4da8-88ec-f01d4ecb4069" />

#### Sub 信号の抽出: DSB-SC(Double Sideband Suppressed Carrier: 抑圧搬送波両側波帯)

1. L-R 成分(変調波)の抽出: MPX 信号に BPF(23k〜53k) をかける。
2. 19kHz パイロット信号から 38kHz 搬送波を再生する。
3. 検波: フィルタリングした MPX 信号に、再生した 38kHz 搬送波を掛け算する(復調)
4. 復調した信号に LPF(15kHz) をかけて、音声信号に戻す。

現時点で、音楽の信号を、それなりの音質で復調できるようになった。

- 変調前の音楽: [first_ancem92.wav](https://github.com/user-attachments/files/25324970/first_ancem92.wav)
- 復調後の音楽: [first_ancem92_restored.wav](https://github.com/user-attachments/files/25324963/first_ancem92_restored.wav)

## 1.5 Refine Algorithm

実際に人間が FM 放送を聴けるようにフィルター処理などを追加した。

### 1.5.1 pre-emphasis と de-emphasis の実装

FM 信号は、復調する際に三角関数を時間微分する。位相には周波数情報が含まれているため、微分した結果、復調信号は振幅に比例することになる。
いま、通信路ではガウス雑音が乗ることを仮定しているが、これは、すべての周波数のノイズが乗ることを意味する。
したがって、信号は高周波成分になるほど雑音の影響を受けやすくなる。
さらに、音声は、エネルギー保存則によって、高周波成分ほどエネルギーが小さくなるという特性がある。
これらの課題を克服するために、以下の処理を行った。

1. 送信機側で、送信信号を High-Shelf Filter にかけて、高周波成分を増幅する
2. 受信機側では、受信信号に LPF にかけて高周波成分をカットする

#### 結果

結果を分かりやすくするために、ガウス雑音が大きめにかかるモデルを想定してシミュレーションを行った。

- 追加処理前の復調した音楽信号
  <img width="1400" height="1000" alt="ancem92_10db_analysis" src="https://github.com/user-attachments/assets/23bfe13e-03c4-4a58-a298-58803de16a13" />
- 追加処理後の復調した音楽信号
  <img width="1400" height="1000" alt="ancem92_emphasised_10db_analysis" src="https://github.com/user-attachments/assets/9137d37b-cdd3-4cf1-9c2f-9e06f2ef189a" />

高周波数領域をみると、元信号と同じように周波数の増加に伴って振幅が減少するようになった。
これは、pre-emphasis と de-emphasis の処理によって、信号の高周波成分がノイズに強くなったこと、三角ノイズを減らせるようになったことを示唆していると考えられる。

### 1.5.2 PLL の実装

ステレオ信号の復調において、パイロット信号(19kHz)を使って搬送波(38kHz)を計算する。
前章までの実装では、簡易的にステレオ信号に BPF をかけてパイロット信号を抽出し、その信号に「二乗法」(三角関数を二乗して、位相を 2 倍にする)を適応して搬送波を計算していた。
これは、L-R 成分がパイロット信号に依存することを意味する。もしパイロット信号がノイズなどの影響を受けている場合、搬送波にノイズを伝播することになり、ステレオ信号を正しく左右に分離することが難しくなる。
実際、FM ラジオの受信環境では、ドップラー効果や水晶の誤差により、パイロット信号に周波数のステップ入力(一定の周波数ズレ)が必ず生じる。
この課題を解決するために、以下のブロック図に示す、PLL(Phase Lock Loop)を実装した。
このシステムの実装により、パイロット信号のタイミングに合わせた、純粋な正弦波を生成できるようになる。この正弦波を搬送波として利用することで、同期検波の精度が向上し、結果、L-R 信号をきれいに復元することができる。

<img width="1935" height="365" alt="PLL-block" src="https://github.com/user-attachments/assets/38084fad-d7c1-4b78-9220-e77ac16c95ce" />

#### 1.5.2.1 デジタル 2 次 Type-II PLL の概要

本システムは、入力を 19kHz pilot 信号、出力を NCO の位相特性とし、その出力を再び入力側へ戻して誤差を計算する閉ループ(フィードバック制御系)である。
位相比較器、ループフィルタ(PI)、NCO を通る系の中に積分器が 2 つ(ループフィルタ内と NCO 自身)存在するため、Type-II に分類される。

##### システム制御の基礎知識(PI 制御)

実装時点で、システム制御に関する知識がほとんどなかったため、本システムに関連する理解を記す。
まず、ラジオ受信機において、上記に述べた通り、ドップラー効果や水晶の誤差により、パイロット信号に周波数のステップ入力が生じるため、システムの定常状態に対して、継続的な外乱が加わっていると考えられる。
したがって、このシステムを安定に保つためには、コントローラーが、ゼロではない一定の値(定常値)であることが要請される。本実装では、以下の 2 つの制御を組み合わせた PI 制御を採用した。

- P 制御(比例制御): 誤差に、P ゲインを掛け算する。力学における、バネのような役割であり、瞬時のズレに対して機敏な反発力を生み出し、過渡応答(スピード)を改善する。
- I 制御(積分制御): 過去の誤差を累積(積分)し I ゲインをかける。離散時間において、以下のようにコードで記述できる。

  ```
  integrator += i_gain * error
  ```

システムの安定性のためには、PI 制御の両方が必要となる。仮に P 制御のみのシステムの場合、

```
control = p_gain * error
```

となるが、コントローラがゼロではない一定の値を出力し続けるためには、誤差 `error` が常にゼロではない状態を維持しなければならないという自己矛盾に陥る。
結果として、入力信号に対して位相が常に少しズレた状態となる **定常位相誤差(Steady-State Phase Error)** が生じてしまい、ステレオ信号の正確な分離が不可能になる。

一方、I 制御のみのシステムの場合、

```
control = integrator
```

となり、P 制御のみのシステムにおける自己矛盾を解決することはできる。
しかし、NCO 自体が持つ積分特性と合わさってシステム内に積分器が直列に 2 つ並ぶ状態(二重積分系)となる。
これによりシステムは過度な振動(発振)を引き起こしやすく、入力信号の位相変化に機敏に追従できない(過渡応答が悪化する)ため、実装上望ましくない。
最終的な PI 制御のコードを以下に示す。

```
control = p_gain * error + integrator
```

##### Gain の決定

PI 制御を採用した場合、システムの安定性は、P ゲインと I ゲインに依存することになる。2 つの係数を、ループ帯域幅(`bandwidth`)と、減衰比 `zeta` の二変数を用いて、以下のように決定した。

```
wn = 2 * np.pi * bandwidth  # wn: 自然角周波数
alpha = (2 * zeta * wn) / fs  # P-gain * Ts
beta = (wn * wn) / (fs * fs)  # I-gain * Ts**2
```

##### c.f. Gain の変数変換について

制御器の伝達関数は、PI 制御のため、`p_gain + i_gain / s`、対象系の伝達関数は積分器であるため、`1/s` であるから、PLL 全体の開ループ伝達関数は、`(p_gain*s + i_gain)/s**2` で表せる。
よって、システム全体の閉ループ伝達関数 G(s) は、`(p_gain*s + i_gain)/(s**2 + p_gain*s + i_gain)` と導出される。この伝達関数の分母の次数から、「2 次遅れ系」のシステムであることがわかり、

```
s**2 + 2*zeta*wn*s + wn**2
```

と分母の係数比較を行ない、連続時間における Gain は、

```
p_gain = 2*zeta*wn
i_gain = wn**2
```

離散時間において、この Gain を決定するために、前進オイラー法を考える。これにより、離散時間の PI 制御の Gain `alpha`, `beta` が決定される。

#### 1.5.2.2 システムの最適化

PLL を入れた後も、ステレオ・セパレーションは 0.84 dB(目標 42 dB)に留まり、THD / SINAD も目標に届いていなかった。原因の切り分けと対策は ADR に記録した。ここでは何をしたかと結果だけを要約する(切り分けの図と導出は今後追記する)。

- **復調純度(THD / SINAD)— [ADR-006](adr/adr-006-receiver-filter-fir-iir.md)**
  - THD / SINAD はステレオ・マトリクスを通さないモノラル経路(main = L+R)で測り、FM 復調チェーン単体の純度を見る。
  - 19 kHz パイロットの漏れを、15 kHz 通過 / 18 kHz 阻止の等リプル FIR による 192k→48k ポリフェーズ間引きで除去する。
  - 複素ミキシング後・判別器の前にチャネル選択 LPF を入れ、2·fc の像を除去してから位相を取る。
  - フィルタ方式は「位相が効く段は線形位相 FIR、それ以外は低次 IIR」で使い分ける。
- **ステレオ・セパレーション — [ADR-007](adr/adr-007-stereo-separation.md)**
  - main LPF と sub BPF を同じ長さの線形位相 FIR にし、main を群遅延ぶん遅らせて main / sub の総遅延を揃える(遅延整合)。
  - PLL の NCO 出力に定数の位相オフセット(`STEREO_CARRIER_PHASE_RAD`)を加え、38 kHz 再生搬送波を副搬送波に位相整合する。
  - PLL のループ帯域を 50 Hz → 200 Hz に広げ、NCO の追従残差を減らす(高 SNR 側で分離が上がり、低 SNR でも悪化しないことを SNR スイープで確認)。

結果(1 kHz・SNR 40 dB・シード固定、`make eval` の測定条件):

| メトリクス | 対策前 | 対策後 | 目標(Sony ST-5130) |
|---|---|---|---|
| THD | 1.45 % | 0.0072 % | ≤ 0.3 %(達成・ハードゲート昇格) |
| セパレーション | 0.84 dB | 45.04 dB | ≥ 42 dB(達成・ハードゲート昇格) |
| SINAD | 32 dB | 66.8 dB | ≥ 75 dB(未達・残り 8.2 dB) |

残る SINAD のギャップは [roadmap.md](roadmap.md) の「次にやること(モデル)」で追跡する。
