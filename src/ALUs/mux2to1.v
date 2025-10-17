module mux2to1 (
    input wire sel,   // select signal
    input wire in0,   // input 0
    input wire in1,   // input 1
    output wire out   // output
);

// Internal wires for gate outputs
wire sel_not;
wire and0_out;
wire and1_out;

// Invert select signal
not u_not(sel_not, sel);

// AND gates for inputs gated by select (and inverted select)
and u_and0(and0_out, in0, sel_not);
and u_and1(and1_out, in1, sel);

// OR gate to combine selected inputs
or u_or(out, and0_out, and1_out);

endmodule
