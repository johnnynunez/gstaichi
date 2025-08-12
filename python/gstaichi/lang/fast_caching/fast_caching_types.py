from pydantic import BaseModel
import dataclasses
from gstaichi.lang._wrap_inspect import FunctionSourceInfo


# @dataclasses.dataclass(frozen=True)


class HashedFunctionSourceInfo(BaseModel):
    function_source_info: FunctionSourceInfo
    hash: str
