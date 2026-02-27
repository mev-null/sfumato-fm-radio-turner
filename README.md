This is FPGA-FM-radio project
<img width="2811" height="853" alt="sfumato-radio-v1-0" src="https://github.com/user-attachments/assets/dd557f31-7457-422a-b91d-ca37e6aa2c50" />

# 1.Modeling and Simulation
## 概要
時報の音声ファイルを
1. FM信号に変調し，
2. IQ信号に変換,
4. 最後に音声信号に復調した.
   
通信路では，ホワイトノイズ(ガウス雑音)が乗ることを仮定してモデルの構築を行なった.

### モデル全体のシミュレーション動画

https://github.com/user-attachments/assets/f829db6a-4b2d-4762-8efc-568c4f685ed2


## 1.1 Transmit
擬似的な音声信号(440Hzの正弦波)を生成し，その信号をFM信号に変調，ガウス雑音を乗せるところまでのモデルとシミュレーションを行なった

### 音声信号→FM変調
- アップサンプリングを行い，FM変調を行なった
- サンプリングには線形補完を利用
### FM変調信号にガウス雑音を乗せる
- アップサンプリング済みの信号の電力から，ノイズ信号の電力を計算
- ノイズ信号の電力からガウス雑音の正規分布を計算
### 雑音が混じったFM信号を可視化
<img width="1211" height="811" alt="signal_noisy" src="https://github.com/user-attachments/assets/983cb61c-0654-4bc8-b545-12008f4f4705" />

- 直感的で暫定的な理解： キャリア周波数の前後に元信号が含まれている．ガウス雑音を乗せたことで，元信号＋ガウス雑音が周波数特性のピークに存在．SN比を大きくすることでガウス雑音を消す．

## 1.2 Recieve
FM信号を受け取り，       
1. 選局 (Mixing): 目的の周波数を0Hz中心に移動
2. 帯域制限 (Filtering): 信号以外の余計なノイズを除去
3. 間引き (Decimation): サンプリングレートをRF帯域(2.4MHz)から音声帯域(48kHz)へ変換

を実行してベースバンドIQ信号に変換するまでのモデリングとシミュレーションを行なった

### Mixing
搬送波周波数分だけ複素平面上で負の方向に回転させる操作を行なった

### ベースバンドIQ信号の可視化
<img width="1211" height="811" alt="recieved_sign" src="https://github.com/user-attachments/assets/4a3a1f7f-169f-4de6-8bb8-556860d1ed62" />

#### c.f. 最大周波数偏移の修正
帯域制限を20kHzに設定してシミュレーションを行なった．理由は，出力レートを48kHz(音声帯域)に設定していたため．
しかし，最大周波数偏移 (Maximum Frequency Deviation)について，日本のFM放送規格に準拠 (+/- 75kHz)して実装していたため，可視化時に期待されれる結果を得られなかった．
フィルタのカットオフ周波数(帯域制限)を100kHzほどに修正したかったが，ベースバンドIQ信号は48kHzを期待しているため，最大周波数偏移を7.5kHzに落として実装した．
実際のFMラジオでは，２段階でDecimationを行なっていることを知ったため，今後の実装課題になる．
[fix: 最大周波数遷移を下げた](https://github.com/mev-null/sfumato-fm-radio-turner/pull/3/changes/afdc3e510589ab221ce63b8b71e9d62133b2f44d)

## 1.3 Demodulation
IQ信号から位相変化を取り出し，音声に変換した
### IQ信号→ 位相
実部と虚部から正接の逆関数で計算
### 位相→音声情報
位相を微分し，位相変化を計算．位相変化がそのまま音の周波数の一部になる．
### 復調された音声を可視化
<img width="1211" height="811" alt="output3" src="https://github.com/user-attachments/assets/5a5b3f1c-a1d5-492b-9918-5766e2ce95a9" />

それなりに元の信号と同じ形に復元できた．また，周波数特性も440Hzに生じており，妥当．

この時点におけるモデルで時報音声を復調した際の結果は以下の通り．

- 変調前の信号
[time-tone.wav](https://github.com/user-attachments/files/25239643/time-tone.wav)

- 復調後の信号
[time-tone_restored.wav](https://github.com/user-attachments/files/25239641/time-tone_restored.wav)
  (ラジオ特有の雑音が混じっていることが確認できる)

## 1.4 Stereo Multiplexing
FM変復調に，ステレオ音源が対応できるようになった．
シミュレーションに使用した信号は，L成分が440Hz, R成分が880Hzのステレオ信号
<img width="857" height="393" alt="stereo_sine" src="https://github.com/user-attachments/assets/2b5e5257-e11e-4676-8d7c-e58ff5eda417" />

簡易的に，音声信号レート(48kHz)とラジオ波レート(約2.4MHz)の双方向からdecimationする過程において，中間にMPX信号レート(192kHz)を設けた．

### 送信機
送信信号について，左右の信号からMPX信号を生成する．

#### 手順
1. 音声信号レートから，MPX信号レートにdecimation
2. MPX信号レートで上記の規則に従って信号を生成
3. 信号をRFレートにupsampling
4. FM変調を行い，IQ信号生成
<img width="1211" height="811" alt="fm-stereo-signal" src="https://github.com/user-attachments/assets/361cd65f-9424-4ac1-af2d-7238fedf39b6" />

#### MPX信号とは？
モノラル成分にL+Rの信号を，19kHzにパイロット信号を，38kHzのサブキャリアにL-Rの信号を埋め込んだもの．
全てで57kHzの帯域幅を必要とする．
<img width="1189" height="790" alt="mpx_signal" src="https://github.com/user-attachments/assets/adeb4c12-eb41-4f08-af76-472c83ad5d5c" />
<img width="1489" height="490" alt="mpx-pds" src="https://github.com/user-attachments/assets/bab0122c-3105-4f71-94da-6b07dcd81f6d" />
19kHzのパイロット信号を利用して，送信機と受信機の時間を同期させる．

### 通信路
ガウス雑音が乗るとしてモデリング
<img width="1211" height="811" alt="fm-stereo-signal-awgn" src="https://github.com/user-attachments/assets/86c17e8e-4881-4053-9066-a530c76c38eb" />

### 復調機
#### MPX信号に復調まで
1. RF信号をベースバンドのIQ信号にする
2. RF信号レート帯でIQ信号をMPX信号に復調
3. RF信号レートからMPX信号レートにdecimation
<img width="1211" height="811" alt="decimated_signal" src="https://github.com/user-attachments/assets/b5ade06a-ec35-4624-8dae-6d16c4a63fae" />

元信号の形状にかなり一致している．
#### 復調したMPX信号をステレオ信号に分離
1. Main(L+R)の信号を抽出．(LPF(15kHz)を通した．)
2. Sub(L-R)の信号を抽出．
3. マトリクス回路に通して，二元一次連立方程式を解き，L, R信号を抽出
4. MPX信号レートから音声信号レートにdecimation
<img width="1021" height="1035" alt="stereo-decode-process" src="https://github.com/user-attachments/assets/c508d596-df0f-4da8-88ec-f01d4ecb4069" />

#### Sub信号の抽出: DSB-SC（Double Sideband Suppressed Carrier：抑圧搬送波両側波帯）
1.  L-R成分（変調波）の抽出: MPX信号にBPF(23k~53k) をかける.
2. 19kHzパイロット信号から38kHz搬送波を再生する．
3. 検波: フィルタリングしたMPX信号に，再生した 38kHz 搬送波を掛け算する（復調）
4.  復調した信号にLPF(15kHz) をかけて、音声信号に戻す.

現時点で，音楽の信号を，それなりの音質で復調できるようになった

- 変調前の音学：[first_ancem92.wav](https://github.com/user-attachments/files/25324970/first_ancem92.wav)

- 復調後の音楽：[first_ancem92_restored.wav](https://github.com/user-attachments/files/25324963/first_ancem92_restored.wav)

---
## 🎧 Audio Credits & License

The audio files used in this project have two different origins:

### Original Composition
- **"first_ancem92.wav"**
  - **Composer/Producer:** mev-null
  - **Copyright:** © 2026 mev-null. All rights reserved.
  - **Description:** An original piece composed to test the fidelity of the stereo FM demodulation. It blends mathematical precision with aesthetic sensibility.

### Usage License for the Code and Music
- **Code:** Licensed under the [MIT License](LICENSE).
- **Music (first_ancem92.wav):** Licensed under [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/). 
  - (You are free to share the audio, but you must provide credit, and you cannot use it for commercial purposes or create derivative works.)

## 1.5 Refine Algorithm
実際に人間がFM放送を聴けるようにフィルター処理などを追加した
### 1.5.1 pre-emphasis と　de-emphasis の実装
FM信号は，復調する際に三角関数を時間微分する．位相には周波数情報が含まれているため，微分した結果，復調信号は振幅に比例することになる．
いま，通信路ではガウス雑音が乗ることを仮定しているが，これは，すべての周波数のノイズが乗ることを意味する．
したがって，信号は高周波成分になるほど雑音の影響を受けやすくなる．
さらに，音声は，エネルギー保存則によって，高周波成分ほどエネルギーが小さくなるという特性がある．
これらの課題を克服するために，以下の処理を行った．

1. 送信機側で，送信信号をHigh-Shelf Filterにかけて，高周波成分を増幅する
2. 受信機側では，受信信号にLPFにかけて高周波成分をカットする

#### 結果
結果を分かりやすくするために，ガウス雑音が大きめにかかるモデルを想定してシミュレーションを行った
- 追加処理前の復調した音楽信号
<img width="1400" height="1000" alt="ancem92_10db_analysis" src="https://github.com/user-attachments/assets/23bfe13e-03c4-4a58-a298-58803de16a13" />

- 追加処理後の復調した音楽信号
<img width="1400" height="1000" alt="ancem92_emphasised_10db_analysis" src="https://github.com/user-attachments/assets/9137d37b-cdd3-4cf1-9c2f-9e06f2ef189a" />

高周波数領域をみると，元信号と同じように周波数の増加に伴って振幅が減少するようになった．
これは、pre-emphasis と　de-emphasisの処理によって，信号の高周波成分がノイズに強くなったこと，三角ノイズを減らせるようになったことを示唆していると考えられる．
## 1.5.2 PLLの実装
ステレオ信号の復調において，パイロット信号(19kHz)を使って搬送波(38kHz)を計算する．
前章までの実装では，簡易的にステレオ信号にBPFをかけてパイロット信号を抽出し，その信号に「二乗法」（三角関数を二乗して，位相を２倍にする）を適応して搬送波を計算していた．
これは，L-R成分がパイロット信号に依存することを意味し，ステレオ信号を正しく左右に分離することが難しくなる．
この課題を解決するために，以下のブロック図に示す，PLL(Phase Lock Loop)を実装した．
 
<img width="1935" height="365" alt="PLL-block" src="https://github.com/user-attachments/assets/38084fad-d7c1-4b78-9220-e77ac16c95ce" />

### 1.5.2.1 デジタル2次Type-II PLLの概要
本システムは，入力を19kHz pilot信号，出力を位相としている開ループである．入力に対して，順番に，位相比較器，ループフィルタ(PI)，NCO(積分器)を通る．
PIに積分器が含まれるため，積分器は２つ存在し，Type-II PLLに分類される．
