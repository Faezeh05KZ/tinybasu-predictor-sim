from dataclasses import dataclass
from isa import Format


@dataclass
class Instruction:
    address: int
    name: str
    fmt: Format
    machine_code: int
    rd: int | None = None
    rs: int | None = None
    rt: int | None = None
    imm: int | None = None
    raw_text: str = ""
