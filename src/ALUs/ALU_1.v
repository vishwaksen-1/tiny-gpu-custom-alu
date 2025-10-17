module alu_8bit(
    input wire [7:0] rs,
    input wire [7:0] rt,
    input wire [1:0] op,      // 2-bit opcode: 00=ADD, 01=SUB, 10=MUL, 11=DIV
    output wire [7:0] alu_out
);

// Internal buses for arithmetic outputs (assume these modules exist and produce outputs)
wire [7:0] add_out;
wire [7:0] sub_out;
wire [7:0] mul_out;  // Assume truncated to 8 bits for simplicity
wire [7:0] div_out;

// Instantiate arithmetic units (example modules; replace with your implementation)
u_rca u_adder(.a(rs), .b(rt), .sum(add_out));
u_rbs u_sub(.a(rs), .b(rt), .diff(sub_out));
u_arrmul u_mul(.a(rs), .b(rt), .prod(mul_out));
arrdiv u_div(.a(rs), .b(rt), .quotient(div_out));

// First layer muxes: select between (ADD, SUB) and (MUL, DIV) per bit
wire [7:0] mux1_out;
wire [7:0] mux2_out;

genvar i;
generate
    for (i=0; i<8; i=i+1) begin : mux_layer1
        mux2to1 mux_add_sub(
            .sel(op[0]),
            .in0(add_out[i]),
            .in1(sub_out[i]),
            .out(mux1_out[i])
        );
        mux2to1 mux_mul_div(
            .sel(op[0]),
            .in0(mul_out[i]),
            .in1(div_out[i]),
            .out(mux2_out[i])
        );
    end
endgenerate

// Second layer mux: select between mux1_out and mux2_out per bit based on op[1]
generate
    for (i=0; i<8; i=i+1) begin : mux_layer2
        mux2to1 mux_final(
            .sel(op[1]),
            .in0(mux1_out[i]),
            .in1(mux2_out[i]),
            .out(alu_out[i])
        );
    end
endgenerate

endmodule