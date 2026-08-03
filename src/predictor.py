from __future__ import annotations

from abc import ABC, abstractmethod


class BranchPredictor(ABC):
    name: str = "abstract"

    @abstractmethod
    def predict(self, pc: int) -> bool:
        ...

    @abstractmethod
    def update(self, pc: int, taken: bool) -> None:
        ...


class AlwaysTakenPredictor(BranchPredictor):
    name = "ST"

    def predict(self, pc: int) -> bool:
        return True

    def update(self, pc: int, taken: bool) -> None:
        pass


class AlwaysNotTakenPredictor(BranchPredictor):
    name = "SN"

    def predict(self, pc: int) -> bool:
        return False

    def update(self, pc: int, taken: bool) -> None:
        pass


class SaturatingCounterPredictor(BranchPredictor):
    def __init__(self, bits: int, name: str) -> None:
        self.bits = bits
        self.name = name
        self.max_state = (1 << bits) - 1
        self.taken_threshold = 1 << (bits - 1)
        self._table: dict[int, int] = {}

    def _state(self, pc: int) -> int:
        default = self.taken_threshold - 1 if self.taken_threshold > 0 else 0
        return self._table.get(pc, default)

    def predict(self, pc: int) -> bool:
        return self._state(pc) >= self.taken_threshold

    def update(self, pc: int, taken: bool) -> None:
        state = self._state(pc)
        state = min(state + 1, self.max_state) if taken else max(state - 1, 0)
        self._table[pc] = state


def make_D1() -> SaturatingCounterPredictor:
    return SaturatingCounterPredictor(bits=1, name="D1")


def make_D2() -> SaturatingCounterPredictor:
    return SaturatingCounterPredictor(bits=2, name="D2")


class HeuristicPredictor(BranchPredictor):
    name = "IQ"
    STATES = 8
    TAKEN_THRESHOLD = STATES // 2

    def __init__(self) -> None:
        self._table: dict[int, int] = {}

    def predict_with_offset(self, pc: int, imm: int) -> bool:
        if pc not in self._table:
            self._table[pc] = self.TAKEN_THRESHOLD if imm < 0 else self.TAKEN_THRESHOLD - 1
        return self._table[pc] >= self.TAKEN_THRESHOLD

    def predict(self, pc: int) -> bool:
        if pc not in self._table:
            self._table[pc] = self.TAKEN_THRESHOLD - 1
        return self._table[pc] >= self.TAKEN_THRESHOLD

    def update(self, pc: int, taken: bool) -> None:
        state = self._table.get(pc, self.TAKEN_THRESHOLD - 1)
        state = min(state + 1, self.STATES - 1) if taken else max(state - 1, 0)
        self._table[pc] = state


def create_predictor(method: str) -> BranchPredictor:
    method = method.upper()
    if method == "ST":
        return AlwaysTakenPredictor()
    if method == "SN":
        return AlwaysNotTakenPredictor()
    if method == "D1":
        return make_D1()
    if method == "D2":
        return make_D2()
    if method == "IQ":
        return HeuristicPredictor()
    raise ValueError(f"Invalid prediction method: '{method}'. Allowed values: ST, SN, D1, D2, IQ")
