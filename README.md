This is FPGA-FM-radio project
<img width="2811" height="853" alt="sfumato-radio-v1-0" src="https://github.com/user-attachments/assets/dd557f31-7457-422a-b91d-ca37e6aa2c50" />

# 1.Modeling and Simulation
## 概要
時報の音声ファイルを
1. FM信号に変調し，
2. IQ信号に変換,
4. 最後に音声信号に復調した.
   
通信路では，ホワイトノイズ(ガウス雑音)が乗ることを仮定してモデルの構築を行なった.

- 変調前の信号
[time-tone.wav](https://github.com/user-attachments/files/25239643/time-tone.wav)

- 復調後の信号
[time-tone_restored.wav](https://github.com/user-attachments/files/25239641/time-tone_restored.wav)
  (ラジオ特有の雑音が混じっていることが確認できる)

### モデル全体のシミュレーション動画

https://github.com/user-attachments/assets/f829db6a-4b2d-4762-8efc-568c4f685ed2

また，440Hzの正弦波を生成し，周波数特性のグラフを可視化し，モデルの正当性について考察した．


## 1.1 Transmit
擬似的な音声信号を生成し，その信号をFM信号に変調，ガウス雑音を乗せるところまでのモデルとシミュレーションを行なった

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
