from __future__ import annotations

from cpu import SimulationResult


def build_report_text(program_name: str, prediction_method: str, result: SimulationResult) -> str:
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("TinyBASU CPU Simulation Report")
    lines.append("=" * 60)
    lines.append(f"Program: {program_name}")
    lines.append(f"Branch prediction method: {prediction_method}")
    lines.append("-" * 60)

    if result.halted_by_timeout:
        lines.append(
            "Warning: program execution reached the cycle timeout and was stopped "
            "(possible infinite loop or bug in the simulator/assembly code)."
        )
        lines.append("-" * 60)

    lines.append(f"Simulator execution time (seconds): {result.elapsed_wall_time_sec:.6f}")
    lines.append(f"Number of assembly instructions (program length): {result.num_asm_instructions}")
    lines.append(f"Number of cycles required to run the program: {result.num_cycles}")
    lines.append(f"Total number of instructions executed: {result.num_instructions_executed}")
    lines.append(f"IPC (Instructions Per Cycle): {result.ipc:.4f}")
    lines.append("")
    lines.append("Register contents after the last cycle:")
    for i, val in enumerate(result.registers):
        lines.append(f"  rx{i} = {val} (0x{val & 0xFFFF:04X})")
    lines.append(f"Final PC value: {result.final_pc}")
    lines.append("")
    lines.append(f"Number of stalls (due to branches): {result.num_stalls}")
    lines.append(f"Total number of conditional branch instructions executed: {result.branch_count}")
    lines.append(f"Number of mispredictions: {result.mispredictions}")
    lines.append(f"Branch prediction algorithm accuracy: {result.accuracy_percent:.2f}%")
    lines.append(f"Speedup relative to not using branch prediction: {result.speedup:.4f}x")
    lines.append("=" * 60)
    return "\n".join(lines) + "\n"


def write_report(path: str, program_name: str, prediction_method: str, result: SimulationResult) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_report_text(program_name, prediction_method, result))
