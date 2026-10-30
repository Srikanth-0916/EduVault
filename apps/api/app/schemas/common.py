"""Shared Pydantic models and camelCase aliasing."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class CamelModel(BaseModel):
    """API models expose camelCase while Python code stays snake_case."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class Page[T](CamelModel):
    items: list[T]
    page: int
    page_size: int
    total: int


class MessageResponse(CamelModel):
    message: str
