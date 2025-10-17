import logging
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import BaseModel
from .loader import (
    read_yaml_object,
    deep_merge,
    read_dotenv,
    read_env
)


logger = logging.getLogger(__file__)
T = TypeVar("T", bound=BaseModel)

class ConfigProvider:
    def __init__(
        self,
        *,
        yaml_path: str | Path | None = None,
        env_path: str | Path | None = None,
        use_env: bool = True,
        env_prefix: str = "APP",
        env_nested_delimiter: str = "_",
    ):
        
        acc: dict[str, Any] = {}
        
        if yaml_path:
            path = Path(yaml_path).resolve()
            acc = deep_merge(acc, read_yaml_object(path))
            logger.info(f"Applied config ({path})")
        
        if env_path:
            path = Path(env_path).resolve()
            acc = deep_merge(acc, read_dotenv(path, nested_delimiter=env_nested_delimiter, prefix=env_prefix))
            logger.info(f"Applied env file ({path})")
        if use_env:
            acc = deep_merge(acc, read_env(nested_delimiter=env_nested_delimiter, prefix=env_prefix))
            logger.info(f"Applied ENV variables")
            
        self.acc = acc
        return
    
    def as_object(self, cls: Type[T]) -> T:
        return cls.model_validate(self.acc)
    
    def as_dict(self) -> dict[str, Any]:
        return self.acc