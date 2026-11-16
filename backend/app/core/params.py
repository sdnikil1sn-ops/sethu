"""Query parameter rules shared by list and report endpoints: surrounding spaces are dropped,
and a blank value ("" or spaces) means "no filter", the same as leaving the parameter out."""
from datetime import date
from typing import Annotated, Any

from pydantic import BeforeValidator, StringConstraints


def blank_to_none(value: Any) -> Any:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


Blank = BeforeValidator(blank_to_none)
Day = Annotated[date | None, Blank]
Text100 = Annotated[Annotated[str, StringConstraints(max_length=100)] | None, Blank]
Text20 = Annotated[Annotated[str, StringConstraints(max_length=20)] | None, Blank]
