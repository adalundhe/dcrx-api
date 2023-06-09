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


class NewImage(BaseModel):
    name: StrictStr
    tag: StrictStr='latest'
    files: Optional[List[StrictStr]]
    build_options: Optional[BuildOptions]
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
