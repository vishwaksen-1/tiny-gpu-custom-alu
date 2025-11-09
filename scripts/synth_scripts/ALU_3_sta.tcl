read_liberty /home/lucky/skywater-pdk/libraries/sky130_fd_sc_hd/latest/timing/sky130_fd_sc_hd__tt_025C_1v80.lib
read_verilog "/home/lucky/Desktop/ASCA Project/tiny-gpu-custom-alu/scripts/synth_scripts/ALU_3_synth.v"
link_design alu_8bit
set_input_delay 0.1 [all_inputs]
set_output_delay 0.1 [all_outputs]
report_checks
exit
