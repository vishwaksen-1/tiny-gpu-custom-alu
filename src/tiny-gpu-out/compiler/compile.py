import re

# --- Instruction and Encoding Definitions (unchanged except keys normalized) ---

OPCODES = {
    'NOP': '0000', 'BRnzp': '0001', 'CMP': '0010', 'ADD': '0011',
    'SUB': '0100', 'MUL': '0101', 'DIV': '0110', 'LDR': '0111',
    'STR': '1000', 'CONST': '1001', 'RET': '1111'
}

# Original mapping (kept same values) but we normalize keys to UPPER for case-insensitive lookup
RAW_REG_MAP = {
    'R0': '0000', 'R1': '0001', 'R2': '0010', 'R3': '0011',
    'R4': '0100', 'R5': '0101', 'R6': '0110', 'R7': '0111',
    'R8': '1000', 'R9': '1001', 'R10': '1010', 'R11': '1011',
    'R12': '1100', 'R13': '1101', 'R14': '1110', 'R15': '1111',
    # Custom mappings for special registers (original style)
    '%blockIdx': '1101',  # Mapped to R13
    '%blockDim': '1110',  # Mapped to R14
    '%threadIdx': '1111'  # Mapped to R15
}

# Normalize keys to uppercase so get_reg_encoding can uppercase the input and find a match
REG_MAP = {k.upper(): v for k, v in RAW_REG_MAP.items()}


# --- Helper Functions (updated robustness) ---

def get_reg_encoding(reg_str):
    """Converts 'R#' or '%special' string to its 4-bit binary code."""
    reg_norm = reg_str.strip().upper()
    # Direct map lookup (case-insensitive via REG_MAP keys normalized)
    if reg_norm in REG_MAP:
        return REG_MAP[reg_norm]
    # Fallback to R<number> pattern
    match = re.match(r'^R(\d+)$', reg_norm)
    if match:
        reg_num = int(match.group(1))
        if 0 <= reg_num <= 15:
            return format(reg_num, '04b')
    raise ValueError(f"Invalid or unmapped register: {reg_str}")


def get_imm_encoding(imm_str, bits=8):
    """Converts immediate value string '#VAL' to N-bit two's complement binary."""
    imm_str = imm_str.strip()
    if imm_str.startswith('#'):
        try:
            val = int(imm_str[1:])
        except ValueError as e:
            raise ValueError(f"Invalid immediate value: {imm_str}. Error: {e}")
        min_val = -(2**(bits-1))
        max_val = (2**(bits-1)) - 1
        if not (min_val <= val <= max_val):
            raise ValueError(f"Immediate value {val} out of range for {bits} bits (Min: {min_val}, Max: {max_val})")
        # encode (handles negative by two's complement)
        return format(val & ((1 << bits) - 1), f'0{bits}b')
    raise ValueError(f"Immediate must start with '#': {imm_str}")


# --- Core Compiler Logic (Two-pass; robust label/instruction list building) ---

def preprocess_code(assembly_code):
    """Removes comments and extracts non-empty lines (trimmed)."""
    cleaned_lines = []
    for raw in assembly_code.split('\n'):
        line = raw.split(';')[0].strip()
        if line:
            cleaned_lines.append(line)
    return cleaned_lines


def pass1_build_symbol_table_and_instr_list(cleaned_lines):
    """
    Build:
      - symbol_table: LABEL -> instruction index (address)
      - instruction_list: list of instruction lines (labels removed)
    The label address is defined as the index of the next instruction (consistent).
    """
    symbol_table = {}
    instruction_list = []

    for line in cleaned_lines:
        # if the line is a label definition
        if line.endswith(':'):
            label = line[:-1].strip()
            label_up = label.upper()
            if label_up in symbol_table:
                raise ValueError(f"Duplicate label definition: {label}")
            # label points to the address of the next instruction
            symbol_table[label_up] = len(instruction_list)
        else:
            # real instruction: append and its address is current len(instruction_list)
            instruction_list.append(line)

    total_instructions = len(instruction_list)
    return symbol_table, instruction_list, total_instructions


def pass2_generate_binary(instruction_list, symbol_table):
    """
    Generate a list of (binary_str, source_line) for the given instruction_list.
    Use enumerate(instruction_list) so addresses are consistent with pass1.
    """
    compiled_output = []

    for current_address, instruction in enumerate(instruction_list):
        parts = [p.strip() for p in re.split(r'[\s,]+', instruction) if p.strip()]
        if not parts:
            # should not happen because instruction_list contains only instructions
            compiled_output.append(("ERROR", instruction))
            continue

        try:
            # --- HARDCODED START ---
            # Keep your special hardcoded encodings for the two starter lines
            if instruction.upper() == "MUL R0, %BLOCKIDX, %BLOCKDIM":
                binary = "0101000011011110"   # 0b0101 0000 1101 1110
                compiled_output.append((f"0b{binary}", instruction))
                continue

            if instruction.upper() == "ADD R0, R0, %THREADIDX":
                binary = "0011000000001111"   # 0b0011 0000 0000 1111
                compiled_output.append((f"0b{binary}", instruction))
                continue
            # --- HARDCODED END ---

            mnemonic = parts[0].upper()

            # Branch handling (BR, BRn, BRz, BRp, BRnz, BRzp, etc.)
            # --- Replace your existing 'if mnemonic.startswith("BR"):' block with this ---
            if mnemonic.startswith('BR'):
                # BR is encoded as: 0001 n z p x iiii iiii
                opcode = OPCODES['BRnzp']
                cond = mnemonic[2:]  # e.g., 'n', 'z', 'p', 'nz', etc.
                n_bit = '1' if 'N' in cond.upper() else '0'
                z_bit = '1' if 'Z' in cond.upper() else '0'
                p_bit = '1' if 'P' in cond.upper() else '0'

                if len(parts) != 2:
                    raise ValueError(f"BR instruction expected 1 label operand, got {len(parts) - 1}.")

                target_label = parts[1].upper()
                if target_label not in symbol_table:
                    raise ValueError(f"Undefined label: {target_label}")

                # IMPORTANT: IMM8 is the absolute instruction address (not PC-relative)
                target_address = symbol_table[target_label]
                Imm8 = format(target_address & 0xFF, '08b')  # absolute address, 8-bit

                # build binary: opcode + n + z + p + x (set to 0) + IMM8
                binary_raw = opcode + n_bit + z_bit + p_bit + '0' + Imm8

            elif mnemonic == 'CONST':
                opcode = OPCODES[mnemonic]
                if len(parts) != 3:
                    raise ValueError("CONST expects: CONST Rd, #IMM8")
                Rd = get_reg_encoding(parts[1])
                Imm8 = get_imm_encoding(parts[2], bits=8)
                binary_raw = opcode + Rd + Imm8

            elif mnemonic == 'CMP':
                opcode = OPCODES[mnemonic]
                if len(parts) != 3:
                    raise ValueError("CMP expects: CMP Rs, Rt")
                Rs = get_reg_encoding(parts[1])
                Rt = get_reg_encoding(parts[2])
                binary_raw = opcode + 'xxxx' + Rs + Rt

            elif mnemonic in ['ADD', 'SUB', 'MUL', 'DIV']:
                opcode = OPCODES[mnemonic]
                if len(parts) != 4:
                    raise ValueError(f"{mnemonic} expects: {mnemonic} Rd, Rs, Rt")
                Rd = get_reg_encoding(parts[1])
                Rs = get_reg_encoding(parts[2])
                Rt = get_reg_encoding(parts[3])
                binary_raw = opcode + Rd + Rs + Rt

            elif mnemonic == 'LDR':
                opcode = OPCODES[mnemonic]
                if len(parts) != 3:
                    raise ValueError("LDR expects: LDR Rd, Rs")
                Rd = get_reg_encoding(parts[1])
                Rs = get_reg_encoding(parts[2])
                binary_raw = opcode + Rd + Rs + 'xxxx'

            elif mnemonic == 'STR':
                opcode = OPCODES[mnemonic]
                if len(parts) != 3:
                    raise ValueError("STR expects: STR Rs, Rt")
                Rs = get_reg_encoding(parts[1])  # address base
                Rt = get_reg_encoding(parts[2])  # data
                binary_raw = opcode + 'xxxx' + Rs + Rt

            elif mnemonic in ['NOP', 'RET']:
                opcode = OPCODES[mnemonic]
                if len(parts) != 1:
                    raise ValueError(f"{mnemonic} expects no operands")
                binary_raw = opcode + 'xxxx' * 3

            else:
                raise ValueError(f"Unknown mnemonic: {mnemonic}")

            final_binary = binary_raw.replace('x', '0')
            compiled_output.append((f"0b{final_binary}", instruction))

        except Exception as e:
            print(f"Error compiling instruction at address {current_address} ('{instruction}'): {e}")
            compiled_output.append(("ERROR", instruction))

    return compiled_output


def compile_two_pass(assembly_code: str):
    cleaned_lines = preprocess_code(assembly_code)
    print(f"Total lines after cleaning: {len(cleaned_lines)}")

    symbol_table, instruction_list, total_instructions = pass1_build_symbol_table_and_instr_list(cleaned_lines)
    print(f"Pass 1 complete. Total instructions: {total_instructions}. Symbol Table: {symbol_table}")

    binary_output = pass2_generate_binary(instruction_list, symbol_table)
    return binary_output, instruction_list


# ---------------- Example usage (keeps your existing sample) ----------------

assembly_input = """
; ===== determinant of 2x2 matrix =====
; A = [a b; c d]
; det = a*d - b*c
; baseA -> matrix start (4 elements)
; baseDet -> scalar output (determinant)

MUL R0, %blockIdx, %blockDim
ADD R0, R0, %threadIdx          ; R0 = global thread id

CONST R1, #0                    ; baseA
CONST R2, #8                    ; baseDet (output address)

; --- constants ---
CONST R14, #0                   ; const 0
CONST R15, #1                   ; const 1

; only thread 0 computes
CMP R0, R14
BRn COMPUTE_DET                 ; if R0 < 1 → thread 0
BRn END                         ; others skip (structure match)

COMPUTE_DET:
  ; --- Load matrix elements ---
  ADD R3, R1, R14               ; addr = baseA + 0
  LDR R4, R3                    ; R4 = a

  ADD R3, R1, R15               ; addr = baseA + 1
  LDR R5, R3                    ; R5 = b

  CONST R6, #2
  ADD R3, R1, R6                ; addr = baseA + 2
  LDR R7, R3                    ; R7 = c

  CONST R8, #3
  ADD R3, R1, R8                ; addr = baseA + 3
  LDR R9, R3                    ; R9 = d

  ; --- dummy loop structure to match matmul pattern ---
  CONST R10, #0                 ; k = 0
  CONST R11, #1                 ; N = 1 (loop once)

LOOP:
    ; det = a*d - b*c
    MUL R12, R4, R9             ; R12 = a * d
    MUL R13, R5, R7             ; R13 = b * c
    SUB R12, R12, R13           ; R12 = ad - bc

    STR R2, R12                 ; store det to baseDet

    ; increment loop counter
    ADD R10, R10, R15
    CMP R10, R11
    BRn LOOP                    ; run once

END:
  ; thread naturally finishes here
"""

binary_output, instr_list = compile_two_pass(assembly_input)

print("\n--- FINAL COMPILED OUTPUT (READY TO COPY) ---")
for binary, src in binary_output:
    print(f"        {binary}, # {src}")

# Optional: verbose address listing
print("\n--- Verbose Compiled Binary Output ---")
for addr, (binary, src) in enumerate(binary_output):
    print(f"Address {addr} ({binary}): {src}")
