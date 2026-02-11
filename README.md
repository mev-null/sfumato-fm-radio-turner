This is FPGA-FM-radio project

# 1.Modeling and Simulation
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

- 直感的で暫定的な理解： キャリア周波数の前後に元信号が含まれている．ガウス雑音を乗せたことで，その２つの和が，BPFによって取り出される

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

#### c.f. 最大周波数遷移の修正
帯域制限を20kHzに設定してシミュレーションを行なった．理由は，出力レートを48kHz(音声帯域)に設定していたため．
しかし，最大周波数偏移 (Maximum Frequency Deviation)について，日本のFM放送規格に準拠 (+/- 75kHz)して実装していたため，可視化時に期待されれる結果を得られなかった．
フィルタのカットオフ周波数(帯域制限)を100kHzほどに修正したかったが，ベースバンドIQ信号は48kHzを期待しているため，最大周波数偏移を7.5kHzに落として実装した．
実際のFMラジオでは，２段階でDecimationを行なっていることを知ったため，今後の実装課題になる．
[fix: 最大周波数遷移を下げた](https://github.com/mev-null/sfumato-fm-radio-turner/pull/3/changes/afdc3e510589ab221ce63b8b71e9d62133b2f44d)
