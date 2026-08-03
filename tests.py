from __future__ import annotations

from cpu import CPU
from memory import Memory
from parser import parse_assembly_file
from predictor import create_predictor
from utils import TinyBASUError

PASSED = 0
FAILED = 0


def check(condition: bool, message: str) -> None:
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  [PASS] {message}")
    else:
        FAILED += 1
        print(f"  [FAIL] {message}")


def _run(asm_path: str, data_path: str, method: str = "D2", timeout: int = 1_000_000):
    instructions = parse_assembly_file(asm_path)
    memory = Memory()
    memory.load_instructions([i.machine_code for i in instructions])
    memory.load_data_file(data_path)
    cpu = CPU(create_predictor(method))
    return cpu.run(memory, len(instructions), timeout)


def test_fibonacci_30_bne():
    print("Test: fibo_bne.asm should produce F(30) mod 65536 = 45608 in rx1")
    result = _run("../asm/fibo_bne.asm", "../asm/fibo_bne.data")
    check(result.registers[1] == 45608, f"rx1 == 45608 (actual: {result.registers[1]})")
    check(result.registers[4] == 45608, f"rx4 == 45608 (actual: {result.registers[4]})")
    check(not result.halted_by_timeout, "execution did not stop due to timeout")


def test_fibonacci_30_beq():
    print("Test: fibo_beq.asm should produce the same result as fibo_bne.asm")
    result = _run("../asm/fibo_beq.asm", "../asm/fibo_beq.data")
    check(result.registers[4] == 45608, f"rx4 == 45608 (actual: {result.registers[4]})")


def test_factorial_50():
    print("Test: fact.asm should produce 50! mod 65536 = 0 (since the power of 2 in 50! exceeds 16)")
    result = _run("../asm/fact.asm", "../asm/fact.data")
    check(result.registers[1] == 0, f"rx1 == 0 (actual: {result.registers[1]})")


def test_all_five_predictors_run_without_error():
    print("Test: all 5 prediction algorithms should run on all 3 programs without error")
    programs = [
        ("../asm/fibo_bne.asm", "../asm/fibo_bne.data"),
        ("../asm/fibo_beq.asm", "../asm/fibo_beq.data"),
        ("../asm/fact.asm", "../asm/fact.data"),
    ]
    for asm, data in programs:
        for method in ["ST", "SN", "D1", "D2", "IQ"]:
            try:
                result = _run(asm, data, method=method)
                check(not result.halted_by_timeout, f"{asm} + {method}: no timeout")
            except TinyBASUError as exc:
                check(False, f"{asm} + {method}: unexpected error: {exc}")


def test_st_predictor_accuracy_matches_taken_ratio():
    print("Test: ST accuracy should exactly equal the ratio of taken branches (since ST always predicts taken)")
    result = _run("../asm/fibo_bne.asm", "../asm/fibo_bne.data", method="ST")
    expected_accuracy = 100.0 * (result.branch_count - result.mispredictions) / result.branch_count
    check(abs(result.accuracy_percent - expected_accuracy) < 1e-9, "computed accuracy is correct")


def test_extended_instructions_demo():
    print("Test: ext_demo.asm (optional module 6-a) should correctly execute all 11 new instructions")
    result = _run("../misc/ext_demo.asm", "../misc/ext_demo.data", method="ST")
    check(result.registers[6] == 9, f"BGT was taken and rx6==9 (actual: {result.registers[6]})")
    check(result.registers[7] == 19, f"BLT was taken and rx7==19 (actual: {result.registers[7]})")
    check(result.registers[2] == 31, f"JR jumped correctly and rx2==31 (actual: {result.registers[2]})")


def test_invalid_register_raises_error():
    print("Test: an invalid register (rx9) should raise a TinyBASUError")
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
        f.write("add rx9, rx0, rx0\n")
        bad_path = f.name
    try:
        parse_assembly_file(bad_path)
        check(False, "should have raised an error but did not")
    except TinyBASUError:
        check(True, "expected error was raised")
    finally:
        os.unlink(bad_path)


def test_immediate_overflow_raises_error():
    print("Test: an immediate larger than the 6-bit I-format range should raise an error")
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".asm", delete=False) as f:
        f.write("addi rx1, rx0, 100\n")
        bad_path = f.name
    try:
        parse_assembly_file(bad_path)
        check(False, "should have raised an error but did not")
    except TinyBASUError:
        check(True, "expected error was raised")
    finally:
        os.unlink(bad_path)


if __name__ == "__main__":
    test_fibonacci_30_bne()
    test_fibonacci_30_beq()
    test_factorial_50()
    test_all_five_predictors_run_without_error()
    test_st_predictor_accuracy_matches_taken_ratio()
    test_extended_instructions_demo()
    test_invalid_register_raises_error()
    test_immediate_overflow_raises_error()

    print(f"\nResult: {PASSED} passed, {FAILED} failed")
    if FAILED:
        raise SystemExit(1)
