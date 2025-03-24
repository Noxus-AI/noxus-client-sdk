from typing import TypeVar, Generic, TYPE_CHECKING
from pydantic import BaseModel, ConfigDict

from noxus_sdk.client import Client

T = TypeVar("T")


class BaseResource(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    client: Client


class BaseService(Generic[T]):
    def __init__(self, client: "Client"):
        self.client = client
