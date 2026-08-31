// blink_tb.sv — blink のテストベンチ(学習用スケルトン)
//
// `make -C src/hdl sim`(Verilator --binary --timing --trace)で実行され、
// build/blink.vcd(src/hdl/build/)を出力する。波形は `make -C src/hdl wave`(surfer)で確認。
//
// --timing モードで動かすので #遅延 / always によるクロック生成が使える(Verilator)。

`timescale 1ns / 1ps

module blink_tb;

  // ---- DUT 接続線 ----
  logic       clk;
  logic       rst_n;
  logic [5:0] led;

  // 実機は27MHzだが、シミュレーションでは小さい値にして点滅を素早く観測する
  localparam int SimClkHz = 20;

  // ---- DUT インスタンス化 ----
  blink #(
      .CLK_HZ(SimClkHz)
  ) dut (
      .clk  (clk),
      .rst_n(rst_n),
      .led  (led)
  );

  // ---- クロック生成: 周期10ns(=100MHz相当) ----
  initial clk = 1'b0;
  always #5 clk = ~clk;

  // ---- 波形ダンプ ----
  initial begin
    $dumpfile("build/blink.vcd");
    $dumpvars(0, blink_tb);
  end

  // ---- 刺激シーケンス ----
  initial begin
    // リセットを与えてから解除
    rst_n = 1'b0;
    #20;
    rst_n = 1'b1;

    // TODO: led が順送りに点灯していくのを確認できるだけの時間だけ走らせる。
    //       SimClkHz=20 なら CLK_HZ/2=10 サイクルごとに 1 段送られる。
    //       例) 数百〜数千 ns 待ってから終了する。
    // TODO(任意): $display や assert で期待する点灯パターンを自動チェックする。

    #4000;
    $finish;
  end

endmodule
