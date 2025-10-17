from ariths_gen.wire_components import Bus
from ariths_gen.multi_bit_circuits.multipliers import UnsignedArrayMultiplier

# Create 8-bit input buses for a and b
a = Bus("a",8)
b = Bus("b",8)

# Create an 8-bit adder (change a_width and b_width for different sizes)
multiplier = UnsignedArrayMultiplier(a = a, b = b)

# Save to a file
with open("amu16.v", "w") as f:
    multiplier.get_v_code_flat(f)