#!/usr/bin/env python3
from migen.genlib.io import CRG
from litex.soc.integration.builder import Builder
from litex.soc.integration.soc_core import SoCCore
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig
from litex.build.generic_platform import GenericPlatform
from litex.build.generic_platform import IOStandard, Pins, Subsignal
from litex.build.sim import SimPlatform

import argparse
import json


class DemoPlatform(SimPlatform):
    def load_io_from_json(self, json_path):
        def int_or_str(s):
            try:
                return int(s)
            except ValueError:
                return s

        with open(json_path, "r") as f:
            raw_io_data = json.load(f)

        parsed_io_array = []
        for raw_entry in raw_io_data:
            parsed_entry = [raw_entry["name"], raw_entry["index"]]

            if "subsignals" in raw_entry:
                subsignals = [
                    Subsignal(name, Pins(int_or_str(signal["pins"])))
                    for name, signal in raw_entry["subsignals"].items()
                ]
                parsed_entry.extend(subsignals)

            else:
                parsed_entry.append(Pins(int_or_str(raw_entry["pins"])))

            if raw_entry.get("iostandard"):
                parsed_entry.append(IOStandard(raw_entry["iostandard"]))

            parsed_io_array.append(tuple(parsed_entry))

        return parsed_io_array

    def __init__(self, io_path):
        io = self.load_io_from_json(json_path=io_path)
        SimPlatform.__init__(self, "SIM", io)


class DemoCore(SoCCore):

    def __init__(
        self,
        platform: GenericPlatform,
        sys_clk_freq: int,
        integrated_rom_size: int = None,
        integrated_rom_init: str = None,
    ):
        # SoC with CPU
        SoCCore.__init__(
            self,
            # System specs
            platform,
            ident="Demo Core",
            ident_version=True,
            # CPU specs
            cpu_type="rocket",
            cpu_variant="small",
            bus_data_width=64,
            clk_freq=sys_clk_freq,
            # Communication
            with_uart=True,
            uart_name="sim",
            # Memory specs
            integrated_rom_size=integrated_rom_size,
            integrated_rom_init=integrated_rom_init,
        )
        self.crg = CRG(self.platform.request("sys_clk"))


def main():
    parser = argparse.ArgumentParser(description="ROM Init demo")
    parser.add_argument(
        "--sys-clk-freq",
        help="clk frequency",
        default=1.25e6,
    )
    parser.add_argument(
        "--integrated-rom-size",
        help="ROM size in bytes",
        default=0x20000,
    )
    parser.add_argument(
        "--integrated-rom-init",
        type=str,
        help="Path to the firmware binary file.",
    )
    parser.add_argument(
        "--no-compile-gateware",
        help="Flag to skip gateware compilation",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--build-path",
        help="Target's build path (ex build/board_name).",
        default="./build",
    )
    args = parser.parse_args()

    # Platform definition
    platform = DemoPlatform(io_path="io_sim.json")

    # SoC definition
    soc = DemoCore(
        platform=platform,
        sys_clk_freq=args.sys_clk_freq,
        integrated_rom_size=args.integrated_rom_size,
        integrated_rom_init=args.integrated_rom_init,
    )

    # Building stage
    builder = Builder(
        soc=soc,
        output_dir=args.build_path,
        compile_gateware=not args.no_compile_gateware,
    )

    sim_config = SimConfig()
    sim_config.add_clocker("sys_clk", freq_hz=args.sys_clk_freq)
    sim_config.add_module("serial2console", "serial")

    builder.build(
        run=not args.no_compile_gateware,
        sim_config=sim_config,
    )


if __name__ == "__main__":
    main()
