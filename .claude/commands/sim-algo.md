# /sim-algo — algo(Python DSP)シミュレーション

algo(`src/sfumato/`)の FM ステレオ変復調モデルを実行し、出力(復調音声・解析グラフ)を確認する。hdl 実装の前に、方式・数値を algo で確かめるためのフロー。手早く回すだけなら `make run` でよい。

## 手順

1. **依存の用意**: `make install`
   - 初回や依存追加後のみ。`uv sync` で `.venv` を構築する。
2. **整形・静的チェック**: `make fmt` → `make lint`
   - コードに手を入れた場合のみ。ruff のエラーが残るなら止めて直す。
3. **シミュレーション実行**: `make run`
   - `src/sfumato/main.py` が送信 → 通信路(AWGN)→ 受信 → 復調を実行する。入力音源が無ければ自動でステレオ時報を生成する。
   - 出力: 復調音声 `outputs/<name>_restored.wav`、解析グラフ `outputs/<name>_analysis.png`。
4. **結果の確認**: `outputs/` の波形・PSD・音声を確認する。
   - 入力と出力の時間波形・周波数特性(PSD)を比較し、期待どおり復元されているかを根拠に判断する(コードだけで結論づけない)。

## 注意

- サンプリングレート・帯域・偏移などの物理定数は `src/sfumato/settings.py` が単一の出どころ。条件を変えるときはここを編集する。
- SN 比は `settings.DEFAULT_SNR_DB`。ノイズ耐性を見たいときは下げて挙動を確認する。
