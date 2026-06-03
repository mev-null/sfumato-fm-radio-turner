# activate-cad.sh — oss-cad-suite (FPGA toolchain) をこのシェルで有効化する
#
# 使い方:  source ./activate-cad.sh
# 提供ツール: yosys / nextpnr-himbaechel / gowin_pack / openFPGALoader など
#
# 注意: 実行(./activate-cad.sh)ではなく source して使うこと。
#       source しないと PATH が呼び出し元シェルに反映されない。

# ツールチェーンの場所(必要なら環境変数で上書き可能)
: "${OSS_CAD_SUITE:=$HOME/tools/oss-cad-suite}"

if [ ! -f "$OSS_CAD_SUITE/environment" ]; then
  echo "oss-cad-suite が見つかりません: $OSS_CAD_SUITE" >&2
  echo "   別の場所にある場合は OSS_CAD_SUITE=/path/to/oss-cad-suite source ./activate-cad.sh" >&2
  return 1 2>/dev/null || exit 1
fi

source "$OSS_CAD_SUITE/environment"

echo "oss-cad-suite 有効化: $OSS_CAD_SUITE"
echo "   yosys: $(yosys --version 2>/dev/null | head -1)"
