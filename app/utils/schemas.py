import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    PlainSerializer,
)


class TemplateModel(BaseModel):
    """Base model for template with attribute docstrings enabled."""
    model_config = ConfigDict(use_attribute_docstrings=True)


def _strip_timezone(v: datetime.datetime) -> datetime.datetime:
    if v.tzinfo:
        # Convert to naive UTC
        return v.astimezone(datetime.UTC).replace(tzinfo=None)
    return v


NaiveDatetime = Annotated[datetime.datetime, AfterValidator(_strip_timezone)]
DatetimeSerializeAsUTC = Annotated[
    NaiveDatetime,
    PlainSerializer(
        lambda v: v.replace(tzinfo=datetime.UTC) if v.tzinfo is None else v,
        return_type=NaiveDatetime,
        when_used="json-unless-none",
    ),
]
