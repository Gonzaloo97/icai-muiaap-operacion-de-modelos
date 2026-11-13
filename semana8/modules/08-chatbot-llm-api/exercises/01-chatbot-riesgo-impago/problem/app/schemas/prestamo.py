from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PrestamoEntrada(BaseModel):
    # Rechaza campos inventados y números no finitos (NaN o infinito).
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    edad: int = Field(
        ge=18, le=75, description="Edad del solicitante (entre 18 y 75 años)"
    )
    ingresos_mensuales: float = Field(
        gt=0, description="Ingresos mensuales, mayores que 0"
    )
    importe_prestamo: float = Field(
        gt=0, description="Importe del préstamo, mayor que 0"
    )
    plazo_meses: int = Field(
        ge=6, le=84, description="Plazo del préstamo (entre 6 y 84 meses)"
    )
    antiguedad_laboral_anios: int = Field(
        ge=0,
        le=50,
        description="Antigüedad laboral del solicitante en años (entre 0 y 50 años)",
    )
    impagos_previos: int = Field(
        ge=0,
        le=20,
        description="Número de impagos previos del solicitante (entre 0 y 20)",
    )

    @field_validator("antiguedad_laboral_anios")
    @classmethod
    def antiguedad_no_incoherente(cls, valor, info):
        edad = info.data.get("edad")
        if edad is not None and valor > edad - 16:
            raise ValueError("La antigüedad laboral no es coherente con la edad.")
        return valor


class PrediccionSalida(BaseModel):
    probabilidad_impago: float = Field(
        ge=0, le=1, description="Probabilidad de impago (entre 0 y 1)"
    )
    decision: Literal["aprobar", "revisar", "rechazar"] = Field(
        description="Decisión del modelo: aprobar, revisar o rechazar"
    )
