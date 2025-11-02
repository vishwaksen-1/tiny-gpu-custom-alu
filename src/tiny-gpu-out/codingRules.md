## 🧩 **Unsaid but Inferred Rules for Writing Assembly for this GPU ISA**

These are the “practical ground rules” a programmer must follow — based on the way GPU is designed.

---

### 🧱 1. **Thread and Block Model**

| Concept                                                                       | Description                                                                               |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `%blockIdx`, `%blockDim`, `%threadIdx`                                        | Built-in *special registers* provided to each thread, similar to CUDA.                    |
| `R0` is typically used to store `i = blockIdx * blockDim + threadIdx`.        | Every kernel begins with: <br> `MUL R0, %blockIdx, %blockDim`<br>`ADD R0, R0, %threadIdx` |
| Each thread’s global index (`R0`) determines which data element it processes. | e.g. `C[i] = A[i] + B[i]` or `C[i] = sum(A[row,k]*B[k,col])`.                             |
| Threads execute independently.                                                | No barriers, atomics, or synchronization primitives are present.                          |
| To restrict work to one thread, compare `R0` with zero.                       | `CMP R0, #0` then branch to skip compute region.                                          |

---

### ⚙️ 2. **Instruction Semantics and Syntax**

| Category                         | Notes                                                                                                                            |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Registers**                    | General-purpose: `R0–R14` (≈15 registers total). <br> Some reserved or conventionally used.                                      |
| **Constants**                    | You *must* load immediates using `CONST`: <br> e.g., `CONST R1, #5` — loads literal 5 into R1.                                   |
| **No immediate arithmetic.**     | All arithmetic is register–register. <br> So use: `CONST Rtmp, #1` then `ADD R3, R1, Rtmp`.                                      |
| **Arithmetic ops:**              | `ADD`, `SUB`, `MUL`, `DIV` — all operate on registers only.                                                                      |
| **Load/Store:**                  | `LDR Rdst, Raddr`  ← loads from memory address in `Raddr`. <br> `STR Raddr, Rsrc` ← stores `Rsrc` to address in `Raddr`.         |
| **Branch/Compare:**              | `CMP Rx, Ry` → sets condition codes (negative if Rx < Ry). <br> `BRn label` → branch if last compare was *negative* (`Rx < Ry`). |
| **Flow control:**                | No `RET` (return) instruction — thread naturally terminates at end of program.                                                   |
| **Labels:**                      | Used for structured control flow (`LOOP:`, `END:` etc).                                                                          |
| **Constants must be preloaded.** | All loop increments, offsets, array indices, etc. must come from `CONST` values.                                                 |

---

### 🧠 3. **Execution and Thread Behavior**

| Behavior                                    | Description                                                                          |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| No call stack or subroutines.               | Straight-line kernel execution; `RET` signals thread completion, not return.         |
| No global synchronization.                  | Each thread executes independently until completion.                                 |
| Memory accesses are assumed safe.           | Programmer must ensure address validity (`base + offset` in range).                  |
| Each thread must calculate its own offsets. | Typically from global thread index `R0`.                                             |
| Loop structures use compare/branch.         | Standard form: <br>`CMP counter, limit`<br>`BRn LOOP`  ← loops while counter < limit |

---

### 💾 4. **Memory Model**

| Property                          | Description                                                                 |
| --------------------------------- | --------------------------------------------------------------------------- |
| **Global memory only**            | Accessed via `LDR`/`STR` using base + offset. No shared/local memory shown. |
| **Row-major layout for matrices** | Inferred from address math in matrix multiplication kernel.                 |
| **Base addresses**                | Passed in via constants (`CONST R1, #baseA`, etc.).                         |
| **No memory aliasing protection** | Programmer must manage overlaps between `baseA`, `baseB`, `baseC`.          |
| **Address arithmetic**            | Must be done manually: `addr = base + (row * N + col)`.                     |

---

### 🔁 5. **Loop and Control Structure Conventions**

All examples follow this loop pattern:

```asm
CONST Rk, #0             ; loop counter
CONST Rlimit, #N
LOOP:
  ; ... body ...
  ADD Rk, Rk, R1         ; increment (usually by 1)
  CMP Rk, Rlimit
  BRn LOOP               ; loop while Rk < N
```

✅ **Notes:**

* `BRn` checks the negative flag from `CMP`, so this pattern loops while the counter is less than the limit.
* There are **no `BRz` or `BRp`** branch types shown — all loops rely on `BRn`.

---

### 🔢 6. **Typical Register Usage Convention**

| Register  | Typical role                                                                               | Seen in examples |
| --------- | ------------------------------------------------------------------------------------------ | ---------------- |
| `R0`      | Thread/global index (`i`)                                                                  | All kernels      |
| `R1–R5`   | Base addresses, constants, and dimensions (`baseA`, `baseB`, `baseC`, `N`, `stride`, etc.) | MatAdd, MatMul   |
| `R6–R9`   | Temporary addresses, loop counters                                                         | MatMul, Det2x2   |
| `R10–R14` | Arithmetic temporaries and loop state                                                      | Det2x2, MatMul   |
| `R15`     | Often used as constant `1` (increment)                                                     | Det2x2           |

---

### 🧮 7. **Computation Model Expectations**

| Operation Type                                | Parallelism                                                     |
| --------------------------------------------- | --------------------------------------------------------------- |
| Element-wise ops (add, scale, etc.)           | Fully parallel, one element per thread.                         |
| Dot-product / matrix multiplication           | Parallel across output elements (each thread one output).       |
| Global reductions (sum, determinant, inverse) | Serial (done by one thread).                                    |
| Synchronization                               | Not supported in ISA — emulate via “thread 0 only” computation. |

---

### 🧰 8. **Kernel Structure Template**

Every kernel follows this skeleton:

```asm
MUL R0, %blockIdx, %blockDim
ADD R0, R0, %threadIdx          ; global thread index

; set up constants
CONST R1, #baseA
CONST R2, #baseB
CONST R3, #baseC
CONST R4, #N
CONST R5, #0
CONST R6, #1
; ...

; (optional) restrict to one thread
CMP R0, R5
BRn MAIN
BRn END

MAIN:
  ; your compute logic here
  ; loops, loads, stores, math, etc.

  ; optional loop (CMP / BRn pattern)
  ; ...
END:
  ; thread naturally terminates
```

---

### ⚡ 9. **Limitations (as of current ISA)**

* No floating-point arithmetic (integer only).
* No immediate arithmetic operands (must load constants).
* No branching on equality (only `<` via `BRn`).
* No conditional moves.
* No subroutine call/return.
* No synchronization or inter-thread communication.
* Limited register file (~15 general-purpose).
* Single memory space (no shared/constant/cache qualifiers).

---

### 🧾 10. **Example Compliance Checks**

| Example                      | Verified Compliance                                                |
| ---------------------------- | ------------------------------------------------------------------ |
| Matrix Addition              | ✅ Uses parallel element-wise ops, register-only math.              |
| Matrix Multiplication        | ✅ Uses per-thread compute, register-based loops.                   |
| Determinant (2×2, corrected) | ✅ Serial (thread 0), register-only arithmetic, BRn loop structure. |

---

## 🚀 TL;DR – The “Programmer Rules” Summary

| #  | Rule                                                                               |
| -- | ---------------------------------------------------------------------------------- |
| 1  | Always compute global thread index first (`R0 = blockIdx * blockDim + threadIdx`). |
| 2  | Load all literals via `CONST` — never use immediates in arithmetic.                |
| 3  | Use registers only for all arithmetic operations.                                  |
| 4  | Loop structure = `CMP + BRn` pattern (loop while counter < limit).                 |
| 5  | No `RET`; thread ends when instruction stream ends.                                |
| 6  | Access memory via `LDR`/`STR` — base + offset arithmetic must be explicit.         |
| 7  | Matrices are row-major in memory.                                                  |
| 8  | Thread 0 executes serial logic (no sync available).                                |
| 9  | Keep under ~15 registers per thread.                                               |
| 10 | No implicit synchronization, no branching on equality, no immediate addressing.    |
