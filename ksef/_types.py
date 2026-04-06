"""Clean return types for the high-level KSeF API."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvoiceResult:
    """Result of sending a single invoice."""

    reference_number: str
    ksef_number: str | None = None
    status: str = "sent"


@dataclass
class TokenResult:
    """Result of creating or retrieving a KSeF API token."""

    reference_number: str
    token: str


@dataclass
class LimitsInfo:
    """Aggregated limits information for the authenticated context."""

    context: dict = field(default_factory=dict)
    subject: dict = field(default_factory=dict)
    rate: dict = field(default_factory=dict)


@dataclass
class SessionStatus:
    """Status of a KSeF session."""

    code: int
    description: str
    invoice_count: int | None = None
    successful_count: int | None = None
    failed_count: int | None = None
