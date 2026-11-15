"""The three services an international adoption touches. Each is owned by another team."""

from __future__ import annotations

from dataclasses import dataclass, field


class TransientError(Exception):
    """Timeout or overload. The call may be retried with the same adoption id."""


class PermanentError(Exception):
    """The service said no. Retrying will not help."""


@dataclass
class _Faults:
    transient: int = 0
    permanent: bool = False

    def check(self) -> None:
        if self.permanent:
            raise PermanentError("refused")
        if self.transient:
            self.transient -= 1
            raise TransientError("timeout")


@dataclass
class Shelter:
    """Reserves kittens. Idempotent per adoption id."""

    reserved: dict[str, str] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)
    faults: dict[str, _Faults] = field(default_factory=dict)

    def fail(self, operation: str, transient: int = 0, permanent: bool = False) -> None:
        self.faults[operation] = _Faults(transient, permanent)

    def reserve(self, adoption_id: str, kitten: str) -> None:
        self.calls.append(("reserve", adoption_id))
        self.faults.get("reserve", _Faults()).check()
        holder = self.reserved.get(kitten)
        if holder not in (None, adoption_id):
            raise PermanentError(f"{kitten} is reserved by {holder}")
        self.reserved[kitten] = adoption_id

    def release(self, adoption_id: str, kitten: str) -> None:
        self.calls.append(("release", adoption_id))
        self.faults.get("release", _Faults()).check()
        if self.reserved.get(kitten) == adoption_id:
            del self.reserved[kitten]


@dataclass
class Payments:
    """Charges adoption fees. Idempotent per adoption id."""

    balance: dict[str, int] = field(default_factory=dict)
    charged: dict[str, int] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)
    faults: dict[str, _Faults] = field(default_factory=dict)

    def fail(self, operation: str, transient: int = 0, permanent: bool = False) -> None:
        self.faults[operation] = _Faults(transient, permanent)

    def charge(self, adoption_id: str, family: str, amount: int) -> None:
        self.calls.append(("charge", adoption_id))
        self.faults.get("charge", _Faults()).check()
        if adoption_id in self.charged:
            return
        self.charged[adoption_id] = amount
        self.balance[family] = self.balance.get(family, 0) - amount

    def refund(self, adoption_id: str, family: str) -> None:
        self.calls.append(("refund", adoption_id))
        self.faults.get("refund", _Faults()).check()
        amount = self.charged.pop(adoption_id, 0)
        self.balance[family] = self.balance.get(family, 0) + amount


@dataclass
class Transport:
    """Books the van that brings the kitten home. Idempotent per adoption id."""

    booked: dict[str, str] = field(default_factory=dict)
    calls: list[tuple[str, str]] = field(default_factory=list)
    faults: dict[str, _Faults] = field(default_factory=dict)

    def fail(self, operation: str, transient: int = 0, permanent: bool = False) -> None:
        self.faults[operation] = _Faults(transient, permanent)

    def book(self, adoption_id: str, kitten: str) -> None:
        self.calls.append(("book", adoption_id))
        self.faults.get("book", _Faults()).check()
        self.booked[adoption_id] = kitten

    def cancel(self, adoption_id: str) -> None:
        self.calls.append(("cancel", adoption_id))
        self.faults.get("cancel", _Faults()).check()
        self.booked.pop(adoption_id, None)
