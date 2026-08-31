# ADR-003: [hdl] コンテキスト認識(Brain)の実装方式

- ステータス: Deferred (2026-08-31)(保留前は Proposed・未決)
- 保留理由: 2026-08-31 にプロジェクトを「Python/NumPy の DSP モデルが成果物」と再定義し、FPGA 移植を将来の拡張としたため。決定内容は再開時の出発点として保持する(経緯は [../README.md](../README.md))。
- 日付: 2026-06-04
- 領域: hdl
- 関連: [../roadmap-hardware.md](../roadmap-hardware.md) / [../architecture-hardware.md](../architecture-hardware.md) / [../diagrams/system-architecture.mmd](../diagrams/system-architecture.mmd)

## コンテキスト

ビジョン図の上段 **Brain(Context Awareness Engine)** = `I2S Rx → FFT/Feature → Edge AI Inference → Parameter Controller` を、Tang Nano 9K でどう実装するかを決める必要がある。これは MVP の射程外(将来 Phase 4)だが、方式が I/O 語長や Muscle 側の制御 I/F(Register Bus)に影響するため、方向性を早めに記録する。

制約:

- GW1NR-9C はリソースが小さい(LUT ≈ 8.6k、BRAM・乗算器も限定的)。大規模 NN 推論はそのままでは載らない。
- 図では Brain ブロックが C/C++ 色で描かれており、ソフトコア or HLS を示唆していたが、これは未決定であり RTL 二本立ての前提を変えうる大きな判断。

実現方式の候補は以下:

1. **専用 RTL(固定機能パイプライン)**
   - 利点: 最小リソース・最速。algo↔hdl の検証フロー(`make sim`)にそのまま乗る。
   - 欠点: アルゴリズム変更の柔軟性が低い。特徴量・分類器を作り込むたび RTL を書き換える。
2. **ソフトコア(RISC-V; VexRiscv / PicoRV32 等)上の C/C++**
   - 利点: 制御ロジック・特徴量・推論をソフトで柔軟に書ける。図の C++ 表現と整合。
   - 欠点: コア + メモリでリソースを食う。Muscle(DSP)との面積競合。ツールチェーンが増える。
3. **HLS(C/C++ → RTL)**
   - 利点: C 記述から合成。アルゴリズム反復が速い。
   - 欠点: Gowin 系での HLS 整備コスト。生成 RTL の面積・検証性に不確実性。
4. **外部エッジ AI コプロセッサ(Sony Spresense 等)**
   - 利点: マイク+音声 DSP+エッジ AI を一基板に閉じられ、反復が速く FPGA 面積を食わない。身体ループ(知覚→理解→変容)を一箇所に集約できる。
   - 欠点: FPGA に閉じない。チップ間 I/F・依存ツールチェーンが増える。詳細・スコープ(適応オーディオの実装基板も含む)は [adr-004](adr-004-sfumato-core-substrate-spresense.md) が扱う。

## 決定

**未決(Proposed)。** 現時点の方向性のみ記録する:

- **MVP では Brain を作らない。** Muscle 経路(FM 受信 → 復調 → 出力)を優先する。
- 先に **Muscle 側の制御 I/F(Register Bus / パラメータ書き換え方式)を Phase 3 で定義**し、Brain はそのレジスタを操作する主体として後から差し替え可能にする(疎結合)。
- Brain 着手(Phase 4)時に、本 ADR を更新して案1〜4 から確定する。FPGA に閉じるならリソース制約上**専用 RTL もしくは軽量ソフトコア**が有力。大規模 NN は範囲外候補(スコープは [../roadmap-hardware.md](../roadmap-hardware.md) Phase 4 を参照)。外部 DSP(案4 / Spresense)に出す場合は適応オーディオの実装基板と一体で [adr-004](adr-004-sfumato-core-substrate-spresense.md) として検討する。

## 影響

### 良い影響
- Register Bus を先に決めることで、Brain の実装方式を後から選べる(MVP を止めない)。

### 受け入れるトレードオフ / 負の影響
- Brain の実現性(特に推論規模)が未確定のまま。Phase 4 で再評価が要る。

### 将来への含み
- Phase 4 着手時に本 ADR を Accepted へ更新。方式確定後、algo↔hdl 対応表([../architecture-hardware.md](../architecture-hardware.md))に追記する。

## 備考
- "Edge AI" の中身(NN か軽量分類器/ヒューリスティクスか)のスコープは [../roadmap-hardware.md](../roadmap-hardware.md) Phase 4 を参照(軽量側から。大規模 NN は範囲外候補)。
