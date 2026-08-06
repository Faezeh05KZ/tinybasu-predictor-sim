from __future__ import annotations

import os
import time

from cpu import CPU
from memory import Memory
from parser import parse_assembly_file
from predictor import create_predictor
from report import write_report

PREDICTION_METHODS = ["ST", "SN", "D1", "D2", "IQ"]

PROGRAMS = [
    ("fibo_beq", "asm/fibo_beq.asm", "asm/fibo_beq.data"),
    ("fibo_bne", "asm/fibo_bne.asm", "asm/fibo_bne.data"),
    ("fact", "asm/fact.asm", "asm/fact.data"),
]

DEFAULT_TIMEOUT_CYCLES = 200_000


def run_all(reports_dir: str = "reports", timeout_cycles: int = DEFAULT_TIMEOUT_CYCLES) -> list[str]:
    os.makedirs(reports_dir, exist_ok=True)
    generated: list[str] = []

    for program_name, asm_path, data_path in PROGRAMS:
        instructions = parse_assembly_file(asm_path)
        machine_codes = [instr.machine_code for instr in instructions]

        for method in PREDICTION_METHODS:
            memory = Memory()
            memory.load_instructions(machine_codes)
            memory.load_data_file(data_path)
            predictor = create_predictor(method)
            cpu = CPU(predictor)

            start = time.perf_counter()
            result = cpu.run(memory, len(instructions), timeout_cycles)
            result.elapsed_wall_time_sec = time.perf_counter() - start

            report_path = os.path.join(reports_dir, f"{program_name}_{method.lower()}.txt")
            write_report(report_path, asm_path, method, result)
            generated.append(report_path)
            print(f"[OK] {program_name:10s} + {method:2s}  ->  {report_path}")

    return generated


if __name__ == "__main__":
    run_all()
