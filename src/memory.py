from __future__ import annotations

from isa import DATA_MEM_START, DATA_MEM_END, MEMORY_SIZE
from utils import TinyBASUError, hex_line_to_int16, to_unsigned


class Memory:
    def __init__(self) -> None:
        self._data: list[int] = [0] * MEMORY_SIZE

    def load_instructions(self, machine_codes: list[int]) -> None:
        if len(machine_codes) > (DATA_MEM_START):
            raise TinyBASUError("Number of instructions exceeds the instruction memory capacity (256).")
        for addr, word in enumerate(machine_codes):
            self._data[addr] = to_unsigned(word, 16)

    def load_data_file(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f.readlines()]

        for n, line in enumerate(lines, start=1):
            if not line:
                continue
            addr = DATA_MEM_START - 1 + n
            if addr > DATA_MEM_END:
                raise TinyBASUError(
                    f"Line {n} of the data file is outside the allowed data memory range "
                    f"({DATA_MEM_START}..{DATA_MEM_END})."
                )
            self._data[addr] = to_unsigned(hex_line_to_int16(line), 16)

    def read_instruction(self, addr: int) -> int:
        if not (0 <= addr < DATA_MEM_START):
            raise TinyBASUError(f"Address {addr} is outside the instruction memory range.")
        return self._data[addr]

    def read(self, addr: int) -> int:
        if not (0 <= addr < MEMORY_SIZE):
            raise TinyBASUError(f"Invalid memory access at address {addr}")
        return self._data[addr]

    def write(self, addr: int, value: int) -> None:
        if not (DATA_MEM_START <= addr <= DATA_MEM_END):
            raise TinyBASUError(
                f"Attempt to write to address {addr}, which is outside the data memory "
                f"range ({DATA_MEM_START}..{DATA_MEM_END})."
            )
        self._data[addr] = to_unsigned(value, 16)
