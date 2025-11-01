.PHONY: test clean

ALU_VARIANT ?= 0     # 0=rippleAr, 1=claW, 2=cocsa

export LIBPYTHON_LOC=$(shell cocotb-config --libpython)
export PYGPI_PYTHON_BIN=$(shell which python)

IVERILOG_FLAGS = -g2012 -s gpu -D ALU_VARIANT=$(ALU_VARIANT)
ALU_SRCS = ALUs/alu_8bit_rippleAr.v ALUs/alu_8bit_claW.v ALUs/alu_8bit_cocsa.v

# usage
# make test_matadd ALU_VARIANT=0   # ripple
# make test_matmul ALU_VARIANT=1   # cla
# make test_matinv ALU_VARIANT=2   # wallace

test_%:
# 	mkdir -p build
	iverilog $(IVERILOG_FLAGS) -o build/sim.vvp $(ALU_SRCS) build/gpu.v
	COCOTB_TEST_MODULES=test.test_$* \
	vvp -M $(shell cocotb-config --lib-dir) \
	    -m $(shell cocotb-config --lib-name vpi icarus) \
	    build/sim.vvp

clean:
	rm -rf build/sim.vvp