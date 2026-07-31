from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Format(Enum):
    R = "R"
    I = "I"
    J = "J"


@dataclass(frozen=True)
class InstructionDef:
    name: str
    opcode: int
    fmt: Format
    func: int | None = None
    is_branch: bool = False
    is_jump: bool = False
    is_register_jump: bool = False


BASE_INSTRUCTIONS: dict[str, InstructionDef] = {
    "add":  InstructionDef("add",  0b0000, Format.R, func=0b001),
    "sub":  InstructionDef("sub",  0b0000, Format.R, func=0b010),
    "slt":  InstructionDef("slt",  0b0000, Format.R, func=0b100),
    "addi": InstructionDef("addi", 0b0001, Format.I),
    "li":   InstructionDef("li",   0b0010, Format.I),
    "lui":  InstructionDef("lui",  0b0011, Format.I),
    "lw":   InstructionDef("lw",   0b0100, Format.I),
    "sw":   InstructionDef("sw",   0b0101, Format.I),
    "beq":  InstructionDef("beq",  0b1010, Format.I, is_branch=True),
    "bne":  InstructionDef("bne",  0b1011, Format.I, is_branch=True),
    "jmp":  InstructionDef("jmp",  0b1110, Format.J, is_jump=True),
    "jal":  InstructionDef("jal",  0b1111, Format.J, is_jump=True),
}

EXTENDED_INSTRUCTIONS: dict[str, InstructionDef] = {
    "and":  InstructionDef("and",  0b0000, Format.R, func=0b000),
    "mul":  InstructionDef("mul",  0b0000, Format.R, func=0b011),
    "div":  InstructionDef("div",  0b0000, Format.R, func=0b101),
    "sll":  InstructionDef("sll",  0b0000, Format.R, func=0b110),
    "srl":  InstructionDef("srl",  0b0000, Format.R, func=0b111),
    "ori":  InstructionDef("ori",  0b0110, Format.I),
    "andi": InstructionDef("andi", 0b0111, Format.I),
    "slti": InstructionDef("slti", 0b1000, Format.I),
    "bgt":  InstructionDef("bgt",  0b1001, Format.I, is_branch=True),
    "blt":  InstructionDef("blt",  0b1100, Format.I, is_branch=True),
    "jr":   InstructionDef("jr",   0b1101, Format.I, is_jump=True, is_register_jump=True),
}

INSTRUCTION_TABLE: dict[str, InstructionDef] = {**BASE_INSTRUCTIONS, **EXTENDED_INSTRUCTIONS}

_DECODE_TABLE: dict[tuple[int, int | None], InstructionDef] = {}
for _idef in INSTRUCTION_TABLE.values():
    _key = (_idef.opcode, _idef.func if _idef.fmt == Format.R else None)
    _DECODE_TABLE[_key] = _idef


def lookup_by_opcode_func(opcode: int, func: int | None) -> InstructionDef | None:
    return _DECODE_TABLE.get((opcode, func))


OPCODE_R = 0b0000
OPCODE_ADDI, OPCODE_LI, OPCODE_LUI = 0b0001, 0b0010, 0b0011
OPCODE_LW, OPCODE_SW = 0b0100, 0b0101
OPCODE_BEQ, OPCODE_BNE = 0b1010, 0b1011
OPCODE_JMP, OPCODE_JAL = 0b1110, 0b1111
OPCODE_ORI, OPCODE_ANDI, OPCODE_SLTI = 0b0110, 0b0111, 0b1000
OPCODE_BGT, OPCODE_BLT, OPCODE_JR = 0b1001, 0b1100, 0b1101

FUNC_ADD, FUNC_SUB, FUNC_SLT = 0b001, 0b010, 0b100
FUNC_AND, FUNC_MUL, FUNC_DIV, FUNC_SLL, FUNC_SRL = 0b000, 0b011, 0b101, 0b110, 0b111

NUM_REGISTERS = 8
DATA_BUS_WIDTH = 16
I_IMM_BITS = 6
J_IMM_BITS = 12

INSTR_MEM_START = 0
INSTR_MEM_END = 255
DATA_MEM_START = 256
DATA_MEM_END = 511
MEMORY_SIZE = 512

BRANCH_PENALTY = 3
RETURN_ADDRESS_REG = 7
