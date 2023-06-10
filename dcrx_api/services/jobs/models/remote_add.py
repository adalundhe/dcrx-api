from dcrx.layers import Add
from pydantic import (
    FileUrl,
    HttpUrl
)
from typing import Union


class RemoteAdd(Add):
    source: Union[FileUrl, HttpUrl]
    