`default_nettype none
module alu #(
    parameter ALU_VARIANT = 0      // 0=ripple, 1=cla, 2=wallace, etc.
)(
    input  wire        clk,
    input  wire        reset,
    input  wire        enable,
    input  wire [2:0]  core_state,
    input  wire [1:0]  decoded_alu_arithmetic_mux,
    input  wire        decoded_alu_output_mux,
    input  wire [7:0]  rs,
    input  wire [7:0]  rt,
    output wire [7:0]  alu_out
);

    localparam ADD = 2'b00;
    localparam SUB = 2'b01;
    localparam MUL = 2'b10;
    localparam DIV = 2'b11;

    wire [7:0] alu_core_out;

    // ────────── Compile-time ALU selection ──────────
    generate
        if (ALU_VARIANT == 0) begin
            alu_8bit_ripple u_alu (.rs(rs), .rt(rt),
                                   .op(decoded_alu_arithmetic_mux),
                                   .alu_out(alu_core_out));
        end else if (ALU_VARIANT == 1) begin
            alu_8bit_cla u_alu (.rs(rs), .rt(rt),
                                .op(decoded_alu_arithmetic_mux),
                                .alu_out(alu_core_out));
        end else if (ALU_VARIANT == 2) begin
            alu_8bit_wallace u_alu (.rs(rs), .rt(rt),
                                    .op(decoded_alu_arithmetic_mux),
                                    .alu_out(alu_core_out));
        end else begin
            // default to ripple if undefined
            alu_8bit_ripple u_alu (.rs(rs), .rt(rt),
                                   .op(decoded_alu_arithmetic_mux),
                                   .alu_out(alu_core_out));
        end
    endgenerate
    // ────────────────────────────────────────────────

    reg [7:0] alu_out_reg;
    assign alu_out = alu_out_reg;

    always @(posedge clk) begin
        if (reset)
            alu_out_reg <= 8'b0;
        else if (enable && core_state == 3'b101) begin
            if (decoded_alu_output_mux)
                alu_out_reg <= {5'b0, (rs-rt)>0, (rs-rt)==0, (rs-rt)<0};
            else
                alu_out_reg <= alu_core_out;
        end
    end
endmodule
