# ADR-005: 復調品質ゲートの方針(characterize / baseline / 回帰 / 絶対しきい値)

- ステータス: Accepted
- 日付: 2026-06-05
- 領域: algo
- 関連: [../roadmap.md](../roadmap.md) / [../architecture.md](../architecture.md) / [adr-001-rf-frontend-low-if-adc.md](adr-001-rf-frontend-low-if-adc.md)

## コンテキスト

1.6 で品質メトリクスの純粋関数(`src/algo/eval/metrics.py`: THD / SINAD / L-R セパレーション / PLL ロック時間)と CI ゲート(`make eval` = pytest)は整った。だが実際の復調パイプライン出力をそれに通して品質を判定する仕組みがない。roadmap で「方式の確立は 1.7 の定量評価に合格して初めて成立し、これが Phase 2/HDL の合格基準」と定めている以上、品質を「規律」ではなく「仕組み」で守る回帰ゲートが要る。

ゲートの作り方には判断点が複数ある:

1. **絶対しきい値のみ** — 各メトリクスに固定の下限/上限を置く。
   - 利点: 単純・基準が明快。欠点: 良い初期値が分からないと置けない。微小な劣化(基準内だが悪化)を見逃す。
2. **回帰(baseline)のみ** — 既知の good 値からの劣化を許容幅でブロック。
   - 利点: 微小な劣化も捕まえる。欠点: baseline が悪いと悪いまま固定される。絶対的な品質保証はない。
3. **両建て(絶対 + 回帰)** — 絶対しきい値で品質の床を、回帰ゲートで劣化検出を担う。
   - 利点: 床と差分の両方を守れる。欠点: 機構が増える。

品質の床(MVP 合格基準)と継続的な劣化検出は別物で、片方では足りない。両建てに収束した。

加えて、しきい値の「数値」を誰が決めるかという論点がある。本プロジェクトは学習者主体(rules.md 12)で、品質基準の確定は方式理解の核心。よって**機構は scaffold として用意し、数値は観測値を見て利用者が確定する**方針とする。

## 決定

**両建て(絶対しきい値ゲート + baseline 回帰ゲート)** を採用する。具体的には:

- **characterize**: 決定論パイプライン(`eval/harness.py`)で TX→AWGN(seed 固定)→RX を回し、メトリクスを集計する(`eval/characterize.py`)。測定条件は `settings.py` の `EVAL_*`(単一トーン 1kHz・1 秒・SNR=40dB・seed=12345)に固定する。トーンは FFT ビンに乗るコヒーレント周波数を選ぶ。
- **baseline.json**: characterize の結果スナップショット。`schema_version` と `conditions` を含め、条件が変われば基準を無効化できるようにする。生成は **`make characterize` 実行時のみ**(`--update`)。回帰ゲートが黙って基準ごと動く事故を防ぐ。
- **回帰ゲート**: baseline から「良い向きと逆」に `REGRESSION_TOL` を超えて劣化したら fail。dB 系(SINAD・セパレーション)は下振れ、THD・ロック時間は上振れを片側検出する。`conditions` 不一致時は比較しない。
- **絶対しきい値ゲート**: `THD_MAX` / `SINAD_MIN_DB` / `SEPARATION_MIN_DB` / `PLL_LOCK_MAX_S` を床/天井として assert する。目標値は **市販製品スペック**(下記「絶対しきい値の根拠」)に置く。現行アルゴが未達の間は **strict xfail** で CI を緑に保ちつつギャップを計測し、到達すると xpass(strict→fail)で「ハードゲートへ昇格」を通知する(ラチェット)。
- **回帰ゲートはハード**: `REGRESSION_TOL = 0.02`(2%)。パイプラインは決定論(seed 固定)なので本来は同値で、tol は numpy/scipy/BLAS の環境差ドリフト吸収分。
- **PLL ロックは未確定**: `pll_lock_time` の `tol` は `PilotPLL` の誤差出力(乗算検波の生値)に対する絶対値で、MPX のパイロット振幅に依存する。固定の汎用値がないため `settings.py` に `None` で置き、ゲートは `pytest.skip`。観測ログから利用者が決める。
- **スコープ外(今回やらない)**: 複数 SNR スイープ(SINAD カーブ)。MVP は単一 SNR 1 点とし、スイープは 1.7 完了後の拡張とする。

baseline 更新タイミング: **改善を確認したときだけ手動で `make characterize`** し、生成された diff を PR レビューで確認してからコミットする。

## 絶対しきい値の根拠(出典)

目標は「世の中の製品が満たす品質」をアルゴリズムに課す方針(ボトムアップの現状追認ではなくトップダウンの仕様)。基準は **Sony ST-5130 FM ステレオチューナ**の公称仕様。市販 FM 受信 IC(Skyworks/Silicon Labs Si4730/35)とも整合する。

| 設定値 | 値 | 出典(Sony ST-5130 / 測定条件) | クロスチェック(Si4730/35) |
|---|---|---|---|
| `THD_MAX` | 0.3%(= 0.003 線形比) | ステレオ THD 0.3% @ 400Hz・100%変調 | typ 0.1% / max 0.5% |
| `SEPARATION_MIN_DB` | 42 dB | ステレオセパレーション 42 dB @ 400Hz | typ 42 dB(min 35) |
| `SINAD_MIN_DB` | 75 dB | FM S/N 75 dB(モノ) | ステレオ S/N typ 58 dB |

- Sony ST-5130 仕様: <https://reverb.com/item/68501767-sony-st-5130-fm-stereo-fm-am-tuner-fully-capacitors-upgraded-led-hifi-fuse>
- Sony ST-S170 仕様(参考・SNR 69dB / THD 0.5%): <https://www.hifiengine.com/manual_library/sony/st-s170.shtml>
- Si4730/35-D60 データシート Table 7「FM Receiver Characteristics」: <https://www.skyworksinc.com/-/media/Skyworks/SL/documents/public/data-sheets/Si4730-31-34-35-D60.pdf>

注意:
- 本メトリクスの `sinad_db` は **SINAD**(雑音+歪み込み)で、Sony の "S/N" は雑音のみ。THD 0.3% は歪み下限 ≈ 50 dB に相当するため、SINAD が 75 dB に達するには THD も同時に抑える必要がある。`SINAD_MIN_DB = 75` は雑音側の到達目標として置く。
- セパレーションの Sony 値は 400Hz、本測定は 1kHz。中域では同程度で、目標として妥当とみなす。
- 値の単位整合: `metrics.thd` は線形比を返すため百分率 0.3% を 0.003 で置く。

## 影響

### 良い影響
- 品質の床(回帰ゲート)と製品スペック到達(絶対しきい値)の両方を CI で自動化できる。`make eval` 経由で既存 CI に無改修で乗る。
- ラチェット運用で「1.7 合格 = Sony 絶対ゲートが全て昇格しきった状態」と達成判定が測定可能になる(= 方式確立 = Phase 2/HDL 合格基準)。未達のギャップが毎 PR で可視化される。
- メトリクス関数は algo↔hdl 共通のアクセプタンス・オラクル。同じ characterize 機構を後で HDL シミュ出力にも適用できる。

### 受け入れるトレードオフ / 負の影響
- 絶対ゲートは strict xfail のため、未達の間は「緑(xfail)」で表示され、見かけ上 pass と紛らわしい。ギャップは characterize の出力で確認する。
- baseline は手動更新のため、更新忘れ/誤更新の余地が残る。PR レビューでの diff 確認に依存する。
- 単一 SNR・単一トーンの 1 点測定で、帯域全体・低 SNR 領域の品質は別途評価が要る。
- しきい値の出典(Sony ST-5130)は 1970 年代のアナログチューナで、現代の DSP 受信機とは測定条件・前提が異なりうる。クロスチェックに市販 IC を併記してある。

### 将来への含み
- SNR スイープ・多トーン・帯域端での評価は 1.7 完了後に拡張する。
- 1.8(因果・ストリーミング参照モデル)や 75kHz 偏移検証も同じ characterize 機構の上に乗せられる。
- HDL 実装時、同メトリクスで algo↔hdl を apples-to-apples 比較する(Phase 2 アクセプタンス)。

## 備考
- 実装: `src/algo/eval/harness.py`(ドライバ)/ `characterize.py`(集計・baseline I/O)/ `tests/test_quality_gate.py`(ゲート)/ `settings.py`(条件・しきい値)/ `Makefile`(`characterize` ターゲット)。
- メトリクス定義の正本は [adr 無し]・`src/algo/eval/metrics.py` と契約テスト `tests/test_metrics.py`。
