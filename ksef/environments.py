from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class Environment:
    """KSeF API environment configuration."""

    name: str
    api_base_url: str
    qr_base_url: str

    TEST: ClassVar[Environment]
    DEMO: ClassVar[Environment]
    PRODUCTION: ClassVar[Environment]


Environment.TEST = Environment(
    name="TEST",
    api_base_url="https://api-test.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr-test.ksef.mf.gov.pl",
)

Environment.DEMO = Environment(
    name="DEMO",
    api_base_url="https://api-demo.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr-demo.ksef.mf.gov.pl",
)

Environment.PRODUCTION = Environment(
    name="PRODUCTION",
    api_base_url="https://api.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr.ksef.mf.gov.pl",
)
