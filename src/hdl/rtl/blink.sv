// blink.sv — Tang Nano 9K ランニングライト(学習用スケルトン)
//
`timescale 1ns / 1ps
//
// 目標: 6個のオンボードLED(アクティブLow)を一定間隔で順に点灯させ、
//       ツールチェーン一周(yosys → nextpnr → gowin_pack → openFPGALoader)を確認する。
//
// ポート名は constraints/tangnano9k.cst と一致させてある。

module blink #(
    // 入力クロック周波数[Hz]。実機は 27MHz、テストベンチでは小さい値に差し替える。
    parameter int CLK_HZ = 27_000_000
) (
    input  logic       clk,    // 27 MHz オンボードクロック
    input  logic       rst_n,  // 負論理リセット(ボタン S1: 押すと 0)
    output logic [5:0] led      // オンボードLED(アクティブLow: 0 で点灯)
);

  // 分周カウンタ: CLK_HZ/2 まで数えると約0.5秒ごとに 1 イベント
  localparam int CntMax = CLK_HZ / 2 - 1;

  logic [$clog2(CLK_HZ)-1:0] tick;   // 分周カウンタ
  logic [5:0]                state;  // 点灯位置(1 のビットが点灯)

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // 負論理リセット: カウンタを 0、点灯は最下位 1 個に初期化
      tick  <= '0;
      state <= 6'b000001;
    end else if (tick == CntMax[$clog2(CLK_HZ)-1:0]) begin
      // 上限に達したらカウンタを戻し、点灯位置を 1 つ左へローテート
      tick  <= '0;
      state <= {state[4:0], state[5]};
    end else begin
      tick <= tick + 1'b1;
    end
  end

  // LED はアクティブLow(0 で点灯)なので反転して出力
  assign led = ~state;

endmodule
