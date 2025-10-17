from ariths_gen.wire_components import Bus
from ariths_gen.multi_bit_circuits.dividers import ArrayDivider

# Create 8-bit input buses for a and b
a = Bus("a",8)
b = Bus("b",8)

# Create an 8-bit adder (change a_width and b_width for different sizes)
divider = ArrayDivider(a = a, b = b)

# Save to a file
with open("div8.v", "w") as f:
    divider.get_v_code_flat(f)