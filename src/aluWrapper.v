module aluWrapper (
    clk,
    reset,
    enable,
    core_state,
    decoded_alu_arithmetic_mux,    // Used by the selected ALU sub-module for operation
    decoded_alu_output_mux,        // For the comparison operation
    rs,
    rt,
    alu_out
);
    input wire clk;
    input wire reset;
    input wire enable;
    input wire [2:0] core_state;
    // Removed aluSelect as we are only using ALU1
    input wire [1:0] decoded_alu_arithmetic_mux; // Renamed from 'opcode' to match port usage
    input wire decoded_alu_output_mux;           // To select between comparison and ALU result
    input wire [7:0] rs;
    input wire [7:0] rt;
    output wire [7:0] alu_out;

    // Intermediate wire for connecting ALU1 output
    wire [7:0] alu1_result;

    // Instantiate ALU_1 at the module level
    ALU_1 alu1_instance (
        .rs(rs),
        .rt(rt),
        .op(decoded_alu_arithmetic_mux), // Connects the operation select to ALU1
        .alu_out(alu1_result)
    );
    
    // With only ALU1, 'selected_alu_result' is simply alu1_result
    assign selected_alu_result = alu1_result; // This wire still helps conceptual clarity
    wire [7:0] selected_alu_result; // Declare it as a wire

    reg [7:0] alu_out_reg;
    assign alu_out = alu_out_reg;

    always @(posedge clk) begin
        if (reset) begin
            alu_out_reg <= 8'b00000000;
        end else if (enable) begin
            if (core_state == 3'b101) begin
                if (decoded_alu_output_mux == 1) begin
                    // Comparison operation
                    alu_out_reg <= {5'b00000, (rs > rt), (rs == rt), (rs < rt)};
                end else begin
                    // Output from ALU1 (which is now the only "selected" ALU)
                    alu_out_reg <= selected_alu_result;
                end
            end
        end
    end
endmodule