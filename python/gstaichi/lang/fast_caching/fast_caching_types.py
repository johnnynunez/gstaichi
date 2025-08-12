from pydantic import BaseModel
import dataclasses


# @dataclasses.dataclass(frozen=True)
class FunctionSourceInfo(BaseModel):
    function_name: str
    filepath: str
    start_lineno: int
    end_lineno: int
    # hash: str | None = None

    class Config:
        frozen = True


class HashedFunctionSourceInfo(BaseModel):
    function_source_info: FunctionSourceInfo
    hash: str
