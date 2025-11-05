# tiny-gpu-custom-alu

This repository contains a Tiny-GPU project extended to allow experimenting with custom ALUs and measuring trade-offs between area, delay and throughput. It includes Verilog sources, generated arithmetic modules, a small testbench/test infrastructure (Cocotb), and example programs for matrix operations.

### Highlights
- Verilog ALU modules and helpers in `src/`.
- A number of generated arithmetic circuits under `src/arithsgen_out/`.
- Tiny GPU reference implementations and builds under `src/tiny-gpu` and `src/tiny-gpu-out`.
- Cocotb-based tests in `src/tiny-gpu-out/test/` for matrix add/multiply/determinant examples.

## Repository layout (top-level)

- `src/` — Verilog sources, generated ALUs and utilities.
  - `ALUs/` — ALU implementations and generator scripts.
  - `arithsgen_out/` — generated circuits and helper tooling.
  - `tiny-gpu/` and `tiny-gpu-out/` — GPU builds, tests and example build artifacts.

## How to run (high level)

Use the Makefiles in `src/tiny-gpu-out` to run builds and tests. Example (from the project root):

```bash
cd src/tiny-gpu-out
make help     # shows available targets (build/sim/test/etc.)
make test     # runs the test flow configured in the Makefile
```

Note: this project relies on `make` being available in your environment (system `make` is sufficient).

## About `src/tiny-gpu-out`

This is the main working area of the project — everything we actively develop and modify lives here. Key contents include:
- `ALUs/` — alternative ALU implementations (ripple, CLA, custom generated ones) that can be swapped into the tiny GPU.
- `build/` — generated Verilog glue and builds used for simulation.
- `compiler/` — contains a basic light-weight python based custom compiler/assembler 
- `test/` — Cocotb test harness, helper scripts and tests for matadd/matmul/matdet; these tests drive the DUT and the on-chip memory model.
- `docs/`, `Makefile`, and `gpuREADME.md` — documentation and build orchestration for the tiny-GPU portion.

## About the compiler and documentation files

- `compiler/compile.py` — this compiler is built specifically for this specific gpu's isa, and it handles nothing about optimizations for now, it just looks at written assembly and translates it to binary as long as it's syntactically correct and prints in the console. If you modify the ISA or add instructions, update the compiler accordingly.

- `gpuREADME.md` — originally taken from the upstream tiny-gpu project (included as a submodule under `src/tiny-gpu/`). It documents the base GPU design and how the top-level system integrates the ALU. There is also a copy under `src/tiny-gpu-out/` which you can edit for local/project-specific notes and modifications; changes to the local copy do not automatically propagate upstream. If you want to change the upstream documentation, edit the README in the `src/tiny-gpu/` submodule and sync/push upstream as appropriate.

- `codingRules.md` — a short rulebook describing coding conventions and constraints when working on this GPU. It captures architecture-specific rules (ISA encoding constraints, register usage conventions, memory layout) that help contributors avoid subtle bugs.

## Submodules and inspiration

- The upstream [`tiny-gpu`](https://github.com/adam-maj/tiny-gpu)(also added as a sub-module) project is an educational resource: the original author designed it to teach GPU microarchitecture concepts via a small, runnable GPU implementation. Its README and docs walk through fetch/dispatch/LSU/ALU, the ISA, and integration points — making it very informative for learning and experimentation.

- We included the [ArithsGen](https://github.com/ehw-fit/ariths-gen) project as a submodule under `src/arithsgen_out/`. ArithsGen (see https://arxiv.org/abs/2203.04649) is an excellent tool that modularly generates arithmetic building blocks in HDL; we use it to generate and experiment with custom ALUs.

## Contributing
- If you add new ALUs, place them under `src/ALUs/` and document their behavior and expected area/timing tradeoffs.

- For questions about the test harness or assembly encoding, check the code under `src/tiny-gpu-out/test/helpers/` and the compiler under `src/tiny-gpu-out/compiler/`.

---

Small edits were made to test files to improve test stability; see `src/tiny-gpu-out/test/test_matdet.py` for details.

## TODO

- [ ] Add some simple compiler optimizations for parallelism (like proof of concept or educational demonstrations)
- [ ] Add waveform visualization options (for GTKWave)
- [ ] Add comparative studies for GPUs with different ALUs -- in terms of their area, delay and stuff
- [ ] modify testbenches to use assembly codes and call compiler instead of using FIXED binaries
- [ ] Add basic pipelining
