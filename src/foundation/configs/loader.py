import yaml
from pathlib import Path
from typing import Dict, Any, Type, TypeVar
from pydantic import BaseModel
import hashlib
import logging
logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class VoynichConfig(BaseModel):
    """Base configuration model."""
    project_name: str = "voynich-foundation"
    version: str = "0.1.0"

def load_config(config_path: Path, model: Type[T] = VoynichConfig) -> Tuple[T, str]:
    """
    Load a YAML configuration file and validate it against a Pydantic model.
    Returns the config object and the SHA256 hash of the raw config file.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        raw_content = f.read()
    
    # Calculate hash of raw content
    config_hash = hashlib.sha256(raw_content.encode('utf-8')).hexdigest()
    
    # Parse YAML
    try:
        config_dict = yaml.safe_load(raw_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}")

    # Validate with Pydantic
    try:
        config = model.model_validate(config_dict)
    except Exception as e:
        raise ValueError(f"Config validation failed: {e}")

    return config, config_hash
