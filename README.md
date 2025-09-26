# Overview

This repo is a minimal example of an error found when building a Litex SoC, which causes simulations to crash.

Especifically, in the ```SoCCore``` initializer, if ```integrated_rom_init``` is passed as a ```str``` path to a .bin file, Litex underestimates the total rom size:

```
if isinstance(integrated_rom_init, str):
    integrated_rom_init = get_mem_data(integrated_rom_init,
        endianness = "little", # FIXME: Depends on CPU.
        data_width = bus_data_width
    )
    integrated_rom_size = 4*len(integrated_rom_init)
```

The last line seems to be the problem: it assumes a 32-bit CPU. Instead, we should do:

```
integrated_rom_size = (bus_data_width // 8) * len(integrated_rom_init)
```


# Running the demo

1. Create a python venv:
```
python3 -m venv .venv
source .venv/bin/activate
```

2. Download and install litex (standard) + Rocket CPU:
```
mkdir tools && cd tools
wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
chmod +x litex_setup.py && python3 ./litex_setup.py --init --install --config=standard
cd .. && pip3 install tools/litex && pip3 install git+https://github.com/litex-hub/pythondata-cpu-rocket.git
```

3. Generate the SoC software without compiling the gateware:
```
./soc.py --no-compile-gateware
```

4. Compile Litex's baremetal demo into a .bin file:
```
litex_bare_metal_demo --build-path=build/ --mem=rom
```

5. Simulate the design:
```
./soc.py --integrated-rom-init=demo.bin
```

After several compilation logs, the simulation should crash, showing:
```
[ethernet] loaded (0x617e6bf2c2f0)
[serial2tcp] loaded (0x617e6bf2c2f0)
[xgmii_ethernet] loaded (0x617e6bf2c2f0)
[gmii_ethernet] loaded (0x617e6bf2c2f0)
[clocker] loaded
[serial2console] loaded (0x617e6bf2c2f0)
[jtagremote] loaded (0x617e6bf2c2f0)
[spdeeprom] loaded (addr = 0x0)
MDEBUG: Save time: -1, load_time: 0
[clocker] sys_clk: freq_hz=1250000, phase_deg=0
Found port 4327
%Error: sim_rom.init:325: $readmem file address beyond bounds of array
Aborting...
run_sim.sh: line 1: 128024 Aborted                 (core dumped) obj_dir/Vsim
```
