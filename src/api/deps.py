from dataclasses import dataclass


@dataclass
class RuntimeContext:
    api_version: str = "v1"
    inference_mode: str = "preseason"
    model_version: str = "dev"


RUNTIME = RuntimeContext()


def get_runtime() -> RuntimeContext:
    return RUNTIME
