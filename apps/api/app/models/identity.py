"""Protected academic identity storage.

Table: ``student_identities``.

APAAR protections (design §7 / PRD §10.2):

- raw APAAR values are Fernet-encrypted into ``apaar_ciphertext``, never stored
  in plaintext and never logged;
- ``apaar_lookup_token`` is a keyed HMAC token used for exact-duplicate lookup
  and is unique, so a person has at most one identity row;
- ``apaar_last4`` is the only displayable fragment.
"""

from __future__ import annotations

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, pk, sa_enum
from app.models.enums import IdentityStatus


class StudentIdentity(TimestampMixin, Base):
    """A person's APAAR academic identity reference.

    ``apaar_ciphertext``, ``apaar_lookup_token`` and ``apaar_last4`` are all
    nullable: identities that are ``MISSING`` or ``MALFORMED`` never have an
    encrypted value (they were never validly formatted).
    """

    __tablename__ = "student_identities"
    __table_args__ = (
        # Unique lookup token so cross-institution duplicates share one row.
        UniqueConstraint("apaar_lookup_token", name="uq_student_identities_apaar_lookup_token"),
    )

    id: Mapped[str] = pk()
    apaar_ciphertext: Mapped[str | None] = mapped_column(String(512), default=None)
    apaar_lookup_token: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    apaar_last4: Mapped[str | None] = mapped_column(String(4), default=None)
    identifier_status: Mapped[str] = mapped_column(
        sa_enum(IdentityStatus), default=IdentityStatus.MISSING.value
    )
    key_id: Mapped[str | None] = mapped_column(String(64), default=None)
    verification_reference: Mapped[str | None] = mapped_column(String(128), default=None)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<StudentIdentity {self.id!r} status={self.identifier_status!r}>"
