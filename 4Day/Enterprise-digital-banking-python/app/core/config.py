"""Loads application.yml (with ${VAR:default} interpolation from the
environment/.env, mirroring the Spring Boot config style used by the sibling
Java project) into a single importable `settings` object.
"""

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = BASE_DIR / "application.yml"
ENV_PATH = BASE_DIR / ".env"

_PLACEHOLDER = re.compile(r"\$\{([A-Z0-9_]+)(?::([^}]*))?\}")


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def _interpolate(value):
    if isinstance(value, str):
        match = _PLACEHOLDER.fullmatch(value)
        if match:
            name, default = match.group(1), match.group(2)
            return os.environ.get(name, default)
        return _PLACEHOLDER.sub(lambda m: os.environ.get(m.group(1), m.group(2) or ""), value)
    if isinstance(value, dict):
        return {k: _interpolate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_interpolate(v) for v in value]
    return value


def _load_yaml(path: Path) -> dict:
    with open(path, "r") as f:
        raw = yaml.safe_load(f) or {}
    return _interpolate(raw)


_load_dotenv(ENV_PATH)
_raw = _load_yaml(CONFIG_PATH)


class Settings(BaseModel):
    app_name: str
    app_version: str

    server_port: int

    database_url: str
    database_echo: bool

    jwt_secret: str
    jwt_expiration_minutes: int

    loan_default_interest_rate: float
    loan_max_tenure_months: int
    loan_min_amount: float
    loan_max_amount: float

    notification_channel: str


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes")


settings = Settings(
    app_name=_raw["app"]["name"],
    app_version=_raw["app"]["version"],
    server_port=int(_raw["server"]["port"]),
    database_url=_raw["database"]["url"],
    database_echo=_to_bool(_raw["database"]["echo"]),
    jwt_secret=_raw["jwt"]["secret"],
    jwt_expiration_minutes=int(_raw["jwt"]["expiration-minutes"]),
    loan_default_interest_rate=float(_raw["loan"]["default-interest-rate"]),
    loan_max_tenure_months=int(_raw["loan"]["max-tenure-months"]),
    loan_min_amount=float(_raw["loan"]["min-amount"]),
    loan_max_amount=float(_raw["loan"]["max-amount"]),
    notification_channel=_raw["notification"]["channel"],
)
