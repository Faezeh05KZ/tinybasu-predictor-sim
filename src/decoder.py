from __future__ import annotations

from dataclasses import dataclass

from isa import Format, lookup_by_opcode_func
from utils import TinyBASUError, extract_bits, sign_extend


@dataclass
class DecodedInstruction:
    opcode: int
    func: int | None
    fmt: Format
    rd: int
    rs: int
    rt: int
    imm: int
    mnemonic: str


def decode(word: int) -> DecodedInstruction:
    opcode = extract_bits(word, 15, 12)

    if opcode == 0b0000:
        rd = extract_bits(word, 11, 9)
        rs = extract_bits(word, 8, 6)
        rt = extract_bits(word, 5, 3)
        func = extract_bits(word, 2, 0)
        idef = lookup_by_opcode_func(opcode, func)
        if idef is None:
            raise TinyBASUError(f"opcode=0000 func={func:03b} combination is not defined in the ISA.")
        return DecodedInstruction(opcode, func, Format.R, rd, rs, rt, 0, idef.name)

    idef = lookup_by_opcode_func(opcode, None)
    if idef is None:
        raise TinyBASUError(f"opcode={opcode:04b} is not defined in the ISA.")

    if idef.fmt == Format.I:
        rd = extract_bits(word, 11, 9)
        rs = extract_bits(word, 8, 6)
        imm = sign_extend(extract_bits(word, 5, 0), 6)
        return DecodedInstruction(opcode, None, Format.I, rd, rs, 0, imm, idef.name)

    imm = sign_extend(extract_bits(word, 11, 0), 12)
    return DecodedInstruction(opcode, None, Format.J, 0, 0, 0, imm, idef.name)
