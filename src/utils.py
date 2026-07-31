from __future__ import annotations

WORD_MASK = 0xFFFF


def sign_extend(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)


def to_unsigned(value: int, bits: int) -> int:
    return value & ((1 << bits) - 1)


def extract_bits(word: int, high: int, low: int) -> int:
    width = high - low + 1
    return (word >> low) & ((1 << width) - 1)


def hex_line_to_int16(hex_str: str) -> int:
    hex_str = hex_str.strip()
    if not hex_str:
        raise ValueError("Hexadecimal value is empty.")
    value = int(hex_str, 16)
    return sign_extend(value & WORD_MASK, 16)


class TinyBASUError(Exception):
    pass
