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


from typing import List, Union
from .build_options import BuildOptions
from .registry import Registry


class NewImage(BaseModel):
    name: StrictStr
    tag: StrictStr='latest'
    files: List[StrictStr]=[]
    build_options: BuildOptions
    layers: conlist(Union[
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
    ], min_items=1)
