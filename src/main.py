from __future__ import annotations

import sys
import time

from cpu import CPU
from memory import Memory
from parser import parse_assembly_file
from predictor import create_predictor
from report import write_report
from utils import TinyBASUError


def run_simulation(
    timeout_cycles: int, prediction_method: str, inst_file: str, data_file: str, report_file: str
) -> None:
    instructions = parse_assembly_file(inst_file)

    memory = Memory()
    memory.load_instructions([instr.machine_code for instr in instructions])
    memory.load_data_file(data_file)

    predictor = create_predictor(prediction_method)
    cpu = CPU(predictor)

    start = time.perf_counter()
    result = cpu.run(memory, len(instructions), timeout_cycles)
    result.elapsed_wall_time_sec = time.perf_counter() - start

    write_report(report_file, inst_file, prediction_method, result)
    print(f"Simulation complete. Report saved to '{report_file}'.")


def main() -> None:
    if len(sys.argv) != 6:
        print(
            "Usage: python main.py [total_cycles] [prediction_method] "
            "[inst_file] [data_file] [report_file]"
        )
        sys.exit(1)

    timeout_cycles = int(sys.argv[1])
    prediction_method = sys.argv[2]
    inst_file = sys.argv[3]
    data_file = sys.argv[4]
    report_file = sys.argv[5]

    try:
        run_simulation(timeout_cycles, prediction_method, inst_file, data_file, report_file)
    except TinyBASUError as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
