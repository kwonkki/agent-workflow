"""간단한 산술 계산기 — 에이전틱 리뷰 워크플로우의 시연 대상.

일부러 리뷰거리(0으로 나누기 미처리, 입력 검증 부재 등)를 남겨두어
CI 리뷰 에이전트가 무엇을 잡아내는지 보여준다.
"""

from __future__ import annotations

from typing import Iterable

# aaaa
def add(a: float, b: float) -> float:
    return a + b  


def subtract(a: float, b: float) -> float:
    return a - b  


def multiply(a: float, b: float) -> float:
    return a * b 


def divide(a: float, b: float) -> float:
    # NOTE: b == 0 케이스를 의도적으로 처리하지 않음 (리뷰 에이전트가 지적해야 함)
    return a / b 


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values)
