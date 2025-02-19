import os
from pathlib import Path
import yaml
from pydantic import BaseModel

class ResponseLength(BaseModel):
    min: int = 10
    max: int = 50

class Config(BaseModel):
    ai_model_name: str = "gpt-4o-mini"
    temperature: float = 1.0
    previous_context_messages: int = 3
    response_length: ResponseLength = ResponseLength()

def load_config(path: str | os.PathLike = "config.yaml") -> Config:
    config_path = Path(path)
    if config_path.exists():
        with config_path.open("r", encoding="utf8") as f:
            data = yaml.safe_load(f)
            return Config(**data)
    return Config()

config = load_config()