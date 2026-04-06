from dataclasses import dataclass


@dataclass(frozen=True)
class Environment:
    """KSeF API environment configuration."""

    name: str
    api_base_url: str
    qr_base_url: str


Environment.TEST = Environment(  # type: ignore[attr-defined]
    name="TEST",
    api_base_url="https://api-test.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr-test.ksef.mf.gov.pl",
)

Environment.DEMO = Environment(  # type: ignore[attr-defined]
    name="DEMO",
    api_base_url="https://api-demo.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr-demo.ksef.mf.gov.pl",
)

Environment.PRODUCTION = Environment(  # type: ignore[attr-defined]
    name="PRODUCTION",
    api_base_url="https://api.ksef.mf.gov.pl/v2",
    qr_base_url="https://qr.ksef.mf.gov.pl",
)
