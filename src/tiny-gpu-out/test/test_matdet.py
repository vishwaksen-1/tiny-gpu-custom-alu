import cocotb
from cocotb.triggers import RisingEdge, Timer
# Removed import of TestFailure, as cocotb.exceptions is not found in your environment.
# We will use Python's standard AssertionError or cocotb.result.TestFailure 
# if available, or simply assert False to fail the test on timeout.
# Assuming helpers are located relative to the test directory
from .helpers.setup import setup
from .helpers.memory import Memory
from .helpers.format import format_cycle
from .helpers.logger import logger

# The custom exception handling will now use a standard Python exception 
# that cocotb's test runner can catch.

@cocotb.test()
async def test_det2x2(dut):
    """Test the GPU kernel for calculating the determinant of a 2x2 matrix:
       | a b |
       | c d |
       Determinant = a*d - b*c
    """
    logger.info("Starting Determinant (2x2) Test")
    
    # --- SIMULATION TIMEOUT DEFINITION ---
    MAX_CYCLES = 100 

    # --- 1. Program Memory ---
    program_memory = Memory(dut=dut, addr_bits=8, data_bits=16, channels=1, name="program")
    
    # Compiled binary from the provided assembly
    # CHANGED: Using R12, R13, R14, R15 for constants instead of R1-R4 just in case R1-R4 are special/read-only.
    # New Registers: R12=baseA(0), R13=baseB(8), R14=baseC(16), R15=baseD(24)
    program = [
        0b0101000011011110, # 0: MUL R0, %blockIdx, %blockDim 
        0b0011000000001111, # 1: ADD R0, R0, %threadIdx 

        # CONSTs now target R12-R15
        0b1001110000000000, # 2: CONST R12, #0    ; baseA (a)
        0b1001110100001000, # 3: CONST R13, #8    ; baseB (b)
        0b1001111000010000, # 4: CONST R14, #16   ; baseC (c)
        0b1001111100011000, # 5: CONST R15, #24   ; baseD (d)

        # LDR source registers (Rs) updated to R12-R15
        0b0111010111000000, # 6: LDR R5, R12    ; R5 = data[0] = a
        0b0111011011010000, # 7: LDR R6, R13    ; R6 = data[8] = b
        0b0111011111100000, # 8: LDR R7, R14    ; R7 = data[16] = c
        0b0111100011110000, # 9: LDR R8, R15    ; R8 = data[24] = d

        0b0101100101011000, # 10: MUL R9, R5, R8   ; R9 = a*d
        0b0101101001100111, # 11: MUL R10, R6, R7  ; R10 = b*c
        0b0100101110011010, # 12: SUB R11, R9, R10 ; R11 = D = a*d - b*c

        # STR source register (Rs) for address updated to R12 (address 0)
        0b1000000011001011, # 13: STR R12, R11 ; Store R11 (D) at address R12 (0)
        0b1111000000000000, # 14: RET        
    ]

    # --- 2. Data Memory Setup (Input Matrix) ---
    data_memory = Memory(dut=dut, addr_bits=8, data_bits=8, channels=4, name="data")
    
    # 2x2 matrix elements:
    # a=5, b=2
    # c=4, d=3
    a, b = 5, 2
    c, d = 4, 3
    
    # The addresses are: 
    # Base 0: a
    # Base 8: b
    # Base 16: c
    # Base 24: d
    
    data = [0] * 32 # Initialize 32 elements (0 to 31)
    data[0] = a
    data[8] = b
    data[16] = c
    data[24] = d
    
    # --- 3. Device Control & Setup ---
    # Only one thread is needed for a single determinant calculation
    threads = 1 

    await setup(
        dut=dut,
        program_memory=program_memory,
        program=program,
        data_memory=data_memory,
        data=data,
        threads=threads
    )
    
    logger.info(f"Input Matrix: a={a}, b={b}, c={c}, d={d}")
    data_memory.display(32)

    # --- 4. Simulation Execution ---
    cycles = 0
    while dut.done.value != 1:
        # Run memories/drivers each cycle (matches pattern in matadd/matmul tests)
        data_memory.run()
        program_memory.run()

        await cocotb.triggers.ReadOnly()
        format_cycle(dut, cycles)

        await RisingEdge(dut.clk)
        cycles += 1

        if cycles > MAX_CYCLES:
            # Timeout: fail the test with a clear message and current state snapshot
            logger.error(f"Simulation timeout after {MAX_CYCLES} cycles. 'done' signal was never asserted.")
            data_memory.display(32)
            program_memory.display(len(program))
            raise AssertionError(f"Simulation timeout after {MAX_CYCLES} cycles. 'done' signal was never asserted.")

    logger.info(f"Completed successfully in {cycles} cycles")
    data_memory.display(32)

    # --- 5. Verification ---
    # Expected result: D = a*d - b*c
    expected_determinant = (a * d) - (b * c)
    
    # The result is stored at address 0 
    result_address = 0 
    
    # If your GPU handles 2's complement, the result (7) should fit.
    actual_determinant = data_memory.memory[result_address]

    logger.info(f"Expected Determinant: {expected_determinant}")
    logger.info(f"Actual Determinant from memory[{result_address}]: {actual_determinant}")

    assert actual_determinant == expected_determinant, \
        f"Result mismatch: Expected D={expected_determinant}, Got D={actual_determinant}"
    
    logger.info("Determinant calculation passed!")
