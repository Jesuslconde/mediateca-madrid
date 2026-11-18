from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mediateca_shared.identity import MADRID


@dataclass(frozen=True, slots=True)
class FuenteProfile:
    codigo: str
    nombre: str
    adapter: str = "absysnet"
    base_url: str = ""
    opac_path: str = ""
    session_pattern: str = r"/abnetopac/([A-Za-z0-9]+)"
    format_field: str = "select03"
    format_value: str = "6"
    enabled: bool = True
    delay: float = 1.0
    captcha_policy: str = "pause"
    options: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_model(cls, fuente: Any) -> FuenteProfile:
        return cls(
            codigo=fuente.codigo,
            nombre=fuente.nombre,
            adapter=fuente.adapter,
            base_url=fuente.base_url,
            opac_path=fuente.opac_path or "",
            session_pattern=fuente.session_pattern,
            format_field=fuente.format_field,
            format_value=fuente.format_value,
            enabled=fuente.enabled,
            delay=fuente.delay,
            captcha_policy=fuente.captcha_policy,
            options=dict(fuente.options or {}),
        )

    @property
    def opac_url(self) -> str:
        return self.base_url.rstrip("/") + (self.opac_path or "")

    def source_url(self, titn: str) -> str:
        return f"{self.opac_url}?TITN={titn}"


MADRID_PROFILE = FuenteProfile(
    codigo=MADRID,
    nombre="Madrid",
    base_url="https://gestiona.comunidad.madrid",
    opac_path="/biblio_publicas/cgi-bin/abnetopac",
)


def source_url(profile: FuenteProfile | None, titn: str) -> str:
    base = profile or MADRID_PROFILE
    return base.source_url(titn)
