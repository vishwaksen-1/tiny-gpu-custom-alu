.PHONY: test clean

ALU_VARIANT ?= 0     # 0=rippleAr, 1=claW, 2=cocsa

IVERILOG_FLAGS = -g2012 -s gpu -D ALU_VARIANT=$(ALU_VARIANT)
ALU_SRCS = ALUs/alu_8bit_ripple.v ALUs/alu_8bit_cla.v ALUs/alu_8bit_wallace.v

test_%:
	mkdir -p build
	iverilog $(IVERILOG_FLAGS) -o build/sim.vvp $(ALU_SRCS) build/gpu.v
	COCOTB_TEST_MODULES=test.test_$* \
	vvp -M $(shell cocotb-config --lib-dir) \
	    -m $(shell cocotb-config --lib-name vpi icarus) \
	    build/sim.vvp

clean:
	rm -rf build/sim.vvp