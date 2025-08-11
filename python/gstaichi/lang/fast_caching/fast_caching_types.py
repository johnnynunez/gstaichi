import dataclasses


@dataclasses.dataclass(frozen=True)
class FunctionSourceInfo:
    function_name: str
    filepath: str
    start_lineno: int
    end_lineno: int
