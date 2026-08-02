from __future__ import annotations

from dataclasses import dataclass, field

import isa
from decoder import decode
from memory import Memory
from predictor import BranchPredictor, HeuristicPredictor
from utils import TinyBASUError, sign_extend, to_unsigned


@dataclass
class SimulationResult:
    num_asm_instructions: int = 0
    num_cycles: int = 0
    num_instructions_executed: int = 0
    ipc: float = 0.0
    registers: list[int] = field(default_factory=lambda: [0] * 8)
    final_pc: int = 0
    num_stalls: int = 0
    branch_count: int = 0
    mispredictions: int = 0
    accuracy_percent: float = 0.0
    speedup: float = 0.0
    halted_by_timeout: bool = False
    elapsed_wall_time_sec: float = 0.0


_CONDITIONAL_BRANCH_OPCODES = {isa.OPCODE_BEQ, isa.OPCODE_BNE, isa.OPCODE_BGT, isa.OPCODE_BLT}


class CPU:
    def __init__(self, predictor: BranchPredictor) -> None:
        self.predictor = predictor
        self.regs = [0] * 8
        self.pc = 0

    def _rs(self, idx: int) -> int:
        return sign_extend(self.regs[idx], 16)

    def _set_reg(self, idx: int, value: int) -> None:
        if idx == 0:
            self.regs[idx] = to_unsigned(value, 16)
        else:
            self.regs[idx] = to_unsigned(value, 16)

    def _predict(self, pc: int, imm: int) -> bool:
        if isinstance(self.predictor, HeuristicPredictor):
            return self.predictor.predict_with_offset(pc, imm)
        return self.predictor.predict(pc)

    def run(self, memory: Memory, num_instructions: int, timeout_cycles: int) -> SimulationResult:
        result = SimulationResult(num_asm_instructions=num_instructions)
        self.pc = 0
        self.regs = [0] * 8

        cycles = 0
        executed = 0
        stalls = 0
        branch_count = 0
        mispredictions = 0

        while True:
            if cycles > timeout_cycles:
                result.halted_by_timeout = True
                break
            if not (0 <= self.pc < num_instructions):
                break

            word = memory.read_instruction(self.pc)
            d = decode(word)

            if d.opcode in _CONDITIONAL_BRANCH_OPCODES:
                branch_count += 1
                actual_taken = self._evaluate_condition(d)
                predicted_taken = self._predict(self.pc, d.imm)
                self.predictor.update(self.pc, actual_taken)

                if predicted_taken != actual_taken:
                    mispredictions += 1
                    stalls += 1
                    cycles += isa.BRANCH_PENALTY

                self.pc = (self.pc + d.imm) if actual_taken else (self.pc + 1)
                cycles += 1
                executed += 1

            elif d.opcode in (isa.OPCODE_JMP, isa.OPCODE_JAL, isa.OPCODE_JR):
                if d.opcode == isa.OPCODE_JAL:
                    self._set_reg(isa.RETURN_ADDRESS_REG, self.pc + 1)
                if d.opcode == isa.OPCODE_JR:
                    self.pc = self.regs[d.rd] & 0xFFFF
                else:
                    self.pc = self.pc + d.imm
                cycles += 1
                executed += 1

            else:
                self._execute_non_control(d, memory)
                self.pc += 1
                cycles += 1
                executed += 1

        result.num_cycles = cycles
        result.num_instructions_executed = executed
        result.ipc = (executed / cycles) if cycles > 0 else 0.0
        result.registers = list(self.regs)
        result.final_pc = self.pc
        result.num_stalls = stalls
        result.branch_count = branch_count
        result.mispredictions = mispredictions
        result.accuracy_percent = (
            100.0 * (branch_count - mispredictions) / branch_count if branch_count > 0 else 0.0
        )
        cycles_without_prediction = executed + branch_count * isa.BRANCH_PENALTY
        result.speedup = (cycles_without_prediction / cycles) if cycles > 0 else 0.0
        return result

    def _evaluate_condition(self, d) -> bool:
        a, b = self._rs(d.rd), self._rs(d.rs)
        if d.opcode == isa.OPCODE_BEQ:
            return a == b
        if d.opcode == isa.OPCODE_BNE:
            return a != b
        if d.opcode == isa.OPCODE_BGT:
            return a > b
        if d.opcode == isa.OPCODE_BLT:
            return a < b
        raise TinyBASUError(f"Unknown conditional branch opcode: {d.opcode:04b}")

    def _execute_non_control(self, d, memory: Memory) -> None:
        op = d.opcode
        if op == isa.OPCODE_R:
            rs_v, rt_v = self._rs(d.rs), self._rs(d.rt)
            if d.func == isa.FUNC_ADD:
                self._set_reg(d.rd, rs_v + rt_v)
            elif d.func == isa.FUNC_SUB:
                self._set_reg(d.rd, rs_v - rt_v)
            elif d.func == isa.FUNC_SLT:
                self._set_reg(d.rd, 1 if rs_v < rt_v else 0)
            elif d.func == isa.FUNC_AND:
                self._set_reg(d.rd, rs_v & rt_v)
            elif d.func == isa.FUNC_MUL:
                self._set_reg(d.rd, rs_v * rt_v)
            elif d.func == isa.FUNC_DIV:
                if rt_v == 0:
                    raise TinyBASUError("Division by zero in DIV instruction.")
                q = abs(rs_v) // abs(rt_v)
                self._set_reg(d.rd, -q if (rs_v < 0) != (rt_v < 0) else q)
            elif d.func == isa.FUNC_SLL:
                self._set_reg(d.rd, (rs_v & 0xFFFF) << (rt_v & 0xF))
            elif d.func == isa.FUNC_SRL:
                self._set_reg(d.rd, (rs_v & 0xFFFF) >> (rt_v & 0xF))
            else:
                raise TinyBASUError(f"Unknown func under opcode R: {d.func:03b}")
            return

        if op == isa.OPCODE_ADDI:
            self._set_reg(d.rd, self._rs(d.rs) + d.imm)
        elif op == isa.OPCODE_LI:
            self._set_reg(d.rd, d.imm)
        elif op == isa.OPCODE_LUI:
            self._set_reg(d.rd, d.imm << 10)
        elif op == isa.OPCODE_LW:
            self._set_reg(d.rd, memory.read(self._rs(d.rs) + d.imm))
        elif op == isa.OPCODE_SW:
            memory.write(self._rs(d.rs) + d.imm, self.regs[d.rd])
        elif op == isa.OPCODE_ORI:
            self._set_reg(d.rd, self._rs(d.rs) | (d.imm & 0xFFFF))
        elif op == isa.OPCODE_ANDI:
            self._set_reg(d.rd, self._rs(d.rs) & (d.imm & 0xFFFF))
        elif op == isa.OPCODE_SLTI:
            self._set_reg(d.rd, 1 if self._rs(d.rs) < d.imm else 0)
        else:
            raise TinyBASUError(f"Unknown opcode in execute phase: {op:04b}")
