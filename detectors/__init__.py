from .dependencies import DependencyDetector
from .imports import ImportDetector
from .env_vars import EnvVarDetector
from .configs import ConfigDetector
from .api_calls import ApiCallDetector

ALL_DETECTORS = [
    DependencyDetector,
    ImportDetector,
    EnvVarDetector,
    ConfigDetector,
    ApiCallDetector,
]
