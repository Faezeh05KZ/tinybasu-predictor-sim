from __future__ import annotations

import re

from isa import (
    INSTRUCTION_TABLE, NUM_REGISTERS, Format,
    I_IMM_BITS, J_IMM_BITS,
)
from models import Instruction
from utils import TinyBASUError, to_unsigned

_REG_RE = re.compile(r"^rx([0-7])$")
_LABEL_ONLY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):$")
_LABEL_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_I_IMM_MIN, _I_IMM_MAX = -(1 << (I_IMM_BITS - 1)), (1 << (I_IMM_BITS - 1)) - 1
_J_IMM_MIN, _J_IMM_MAX = -(1 << (J_IMM_BITS - 1)), (1 << (J_IMM_BITS - 1)) - 1


def _strip_comment(line: str) -> str:
    return line.split("#", 1)[0].strip()


def _parse_register(token: str, line_no: int) -> int:
    token = token.strip().rstrip(",")
    m = _REG_RE.match(token)
    if not m:
        raise TinyBASUError(
            f"Line {line_no}: invalid register name '{token}'. "
            f"Registers must be rx0 through rx{NUM_REGISTERS - 1}."
        )
    return int(m.group(1))


def _parse_immediate(token: str, line_no: int) -> int:
    token = token.strip().rstrip(",")
    try:
        return int(token, 0)
    except ValueError as exc:
        raise TinyBASUError(f"Line {line_no}: invalid immediate value '{token}'") from exc


def _check_range(value: int, low: int, high: int, line_no: int, field_name: str) -> None:
    if not (low <= value <= high):
        raise TinyBASUError(
            f"Line {line_no}: value {field_name}={value} is not within the allowed range "
            f"[{low}, {high}] (encoding field overflow)."
        )


def _encode(idef, rd: int, rs: int, rt: int, imm: int, line_no: int) -> int:
    if idef.fmt == Format.R:
        return (idef.opcode << 12) | (rd << 9) | (rs << 6) | (rt << 3) | idef.func
    if idef.fmt == Format.I:
        _check_range(imm, _I_IMM_MIN, _I_IMM_MAX, line_no, "immediate (I-format, 6 bits)")
        return (idef.opcode << 12) | (rd << 9) | (rs << 6) | to_unsigned(imm, I_IMM_BITS)
    _check_range(imm, _J_IMM_MIN, _J_IMM_MAX, line_no, "immediate (J-format, 12 bits)")
    return (idef.opcode << 12) | to_unsigned(imm, J_IMM_BITS)


def parse_assembly_file(path: str) -> list[Instruction]:
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    labels: dict[str, int] = {}
    cleaned: list[tuple[int, str]] = []
    addr = 0
    for line_no, raw in enumerate(raw_lines, start=1):
        code = _strip_comment(raw)
        if not code:
            continue

        m = _LABEL_ONLY_RE.match(code)
        if m:
            labels[m.group(1)] = addr
            continue

        if ":" in code:
            label_part, rest = code.split(":", 1)
            label_part = label_part.strip()
            rest = rest.strip()
            if not _LABEL_NAME_RE.match(label_part):
                raise TinyBASUError(f"Line {line_no}: invalid label name '{label_part}'")
            labels[label_part] = addr
            if not rest:
                continue
            code = rest

        cleaned.append((line_no, code))
        addr += 1

    if addr > 256:
        raise TinyBASUError(
            f"Number of instructions ({addr}) exceeds the instruction memory "
            f"space (256 addresses: 0 to 255)."
        )

    instructions: list[Instruction] = []
    for idx, (line_no, code) in enumerate(cleaned):
        parts = code.replace(",", " , ").split()
        if not parts:
            continue
        mnemonic = parts[0].lower()
        if mnemonic not in INSTRUCTION_TABLE:
            raise TinyBASUError(f"Line {line_no}: unknown instruction '{mnemonic}'")
        idef = INSTRUCTION_TABLE[mnemonic]
        operands = [p for p in parts[1:] if p != ","]

        rd = rs = rt = 0
        imm = 0

        if idef.fmt == Format.R:
            if len(operands) != 3:
                raise TinyBASUError(f"Line {line_no}: instruction {mnemonic} requires 3 operands.")
            rd = _parse_register(operands[0], line_no)
            rs = _parse_register(operands[1], line_no)
            rt = _parse_register(operands[2], line_no)

        elif idef.fmt == Format.I:
            if idef.is_register_jump:
                if len(operands) != 1:
                    raise TinyBASUError(f"Line {line_no}: instruction {mnemonic} requires 1 operand.")
                rd = _parse_register(operands[0], line_no)
            elif idef.is_branch:
                if len(operands) != 3:
                    raise TinyBASUError(f"Line {line_no}: instruction {mnemonic} requires 3 operands.")
                rd = _parse_register(operands[0], line_no)
                rs = _parse_register(operands[1], line_no)
                target = operands[2].strip().rstrip(",")
                imm = labels[target] - idx if target in labels else _parse_immediate(target, line_no)
            elif mnemonic in ("li", "lui"):
                if len(operands) != 2:
                    raise TinyBASUError(f"Line {line_no}: instruction {mnemonic} requires 2 operands.")
                rd = _parse_register(operands[0], line_no)
                target = operands[1].strip().rstrip(",")
                imm = labels[target] if target in labels else _parse_immediate(target, line_no)
            else:
                if len(operands) != 3:
                    raise TinyBASUError(f"Line {line_no}: instruction {mnemonic} requires 3 operands.")
                rd = _parse_register(operands[0], line_no)
                rs = _parse_register(operands[1], line_no)
                imm = _parse_immediate(operands[2], line_no)

        else:
            if len(operands) != 1:
                raise TinyBASUError(f"Line {line_no}: instruction {mnemonic} requires 1 operand.")
            target = operands[0].strip()
            imm = labels[target] - idx if target in labels else _parse_immediate(target, line_no)

        machine_code = _encode(idef, rd, rs, rt, imm, line_no)
        instructions.append(Instruction(
            address=idx, name=mnemonic, fmt=idef.fmt, machine_code=machine_code,
            rd=rd, rs=rs, rt=rt, imm=imm, raw_text=code,
        ))

    return instructions
