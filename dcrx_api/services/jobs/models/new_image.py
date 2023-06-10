from pydantic import (
    BaseModel,
    StrictStr,
    conlist
)

from dcrx.layers import (
    Add,
    Arg,
    Cmd,
    Copy,
    Entrypoint,
    Env,
    Expose,
    Healthcheck,
    Label,
    Run,
    Stage,
    User,
    Volume,
    Workdir
)
from typing import List, Union, Optional
from .build_options import BuildOptions
from .registry import Registry


Layer = Union[
    Add,
    Arg,
    Cmd,
    Copy,
    Entrypoint,
    Env,
    Expose,
    Healthcheck,
    Label,
    Run,
    Stage,
    User,
    Volume,
    Workdir
]


class NewImage(BaseModel):
    name: StrictStr
    tag: StrictStr='latest'
    files: Optional[List[StrictStr]]
    registry: Optional[Registry]
    build_options: Optional[BuildOptions]
    layers: conlist(Layer, min_items=1)
