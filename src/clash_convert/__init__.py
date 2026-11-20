"""Convert proxy share links into Clash Meta / Mihomo YAML."""

__version__ = "1.0.0"

from .generate import build_config, dumps
from .parsers import ParseError, extract_links, parse_link

__all__ = [
    "__version__",
    "ParseError",
    "build_config",
    "dumps",
    "extract_links",
    "parse_link",
]
