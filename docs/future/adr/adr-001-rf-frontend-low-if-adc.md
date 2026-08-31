# ADR-001: [hdl] FM RF フロントエンドは低IF + 高速ADC方式(方式A)

- ステータス: Deferred (2026-08-31)(保留前は Accepted)
- 保留理由: 2026-08-31 にプロジェクトを「Python/NumPy の DSP モデルが成果物」と再定義し、FPGA 移植を将来の拡張としたため。決定内容は再開時の出発点として保持する(経緯は [../README.md](../README.md))。
- 日付: 2026-06-03
- 領域: hdl
- 関連: [../roadmap-hardware.md](../roadmap-hardware.md) / [../architecture-hardware.md](../architecture-hardware.md)

## コンテキスト

FM RF をどうやって FPGA に取り込むかを決める必要がある。制約と要件:

- Tang Nano 9K(GW1NR-9C)に **ADC が無い**。日本の FM は 76–95 MHz、**到達目標は 81.3 MHz の実局受信**。
- algo の受信器は **RF を実数で標本化 → digital mix で選局 → デシメーション → ベースバンド IQ** という構造で既に確立済み(`RF_FS` = 2.304 MHz、`CARRIER_FREQ` = 250 kHz)。
- ワイド FM は ±約 100 kHz の帯域を持ち、ステレオ MPX(〜53 kHz)を含む。
- 80 MHz 帯のアナログ部はブレッドボード(EIC-801)では安定しないため、基板化(or ベタアース実装)が前提。

実現方式の候補は以下:

1. **方式A: 低IF + 高速ADC 1個で実数標本化**
   - 利点: algo の RF 段に **1 対 1 対応**(コード・数値をそのまま検証基準に使える)。広帯域 ADC でワイド FM の帯域不足を心配しなくてよい。ADC は 1ch。
   - 欠点: 数 MSPS 級の高速 ADC が必要。IF フィルタ・ミキサのアナログ設計が要る。
2. **方式B: Tayloe QSD でベースバンドIQ**
   - 利点: 部品が枯れている。ベースバンドなので原理上 ADC は低速でよい(狭帯域前提)。
   - 欠点: ワイド FM 帯域には音声 ADC では帯域不足。IQ 2ch・I/Q 不平衡補正が要る。algo 受信器の前段(digital mix で選局する部分)を作り直すことになる。

algo との整合・検証容易性と、ワイド FM の帯域確保を優先した結果、**方式A** に収束した。

## 決定

**方式A(低IF + 高速ADC 1個で実数標本化)** に決定する。具体的には:

- 信号経路: アンテナ → BPF/LNA → ミキサ(LO は Si5351)→ 低IF → 高速 ADC → FPGA。
- IF は シミュレーションの `CARRIER_FREQ` = 250 kHz に合わせ、ADC サンプリングは `RF_FS` = 2.304 MSPS 相当を狙う(LO・IF・実サンプリング値の本番値は実装時に詰める)。
- ADC 候補は AD9226 系(12bit / 65MSPS)。FPGA へは並列ディジタル I/F。
- スコープ外(やらないこと): 方式B(Tayloe QSD)、80 MHz の直接サンプリング、既製 FM チューナ IC による復調(DSP を FPGA で行う本プロジェクトの目的に反するため)。

## 影響

### 良い影響
- algo の受信チェーン(digital mix → デシメーション → 復調 → ステレオ分離)を**作り直さずそのまま RTL 化の基準**にできる。
- 固定小数点モデルの**入力語長が ADC のビット数(12bit)で確定**する(roadmap 2.3)。

### 受け入れるトレードオフ / 負の影響
- 高速 ADC の並列 I/F 配線、IF フィルタ・ミキサのアナログ設計、基板化が必要。ブレッドボードでは完結しない。

### 将来への含み
- LO・IF・実サンプリングレートの本番値は実装で確定し、決まり次第 [../architecture-hardware.md](../architecture-hardware.md) に反映する。
- 感度・選択度・帯域が不足する場合は、別 ADR を追加して再検討する(本 ADR を Superseded にする)。

## 備考
- ADC のビット幅(12bit)が roadmap 2.3 の固定小数点モデルの入力語長を決める前提となる。
- 調達タイミング・候補は [../roadmap-hardware.md](../roadmap-hardware.md) の「ハードウェア調達」を参照。
