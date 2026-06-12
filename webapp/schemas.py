# -*- coding: utf-8 -*-
"""
Schemas Pydantic para la API de cálculo de vida útil.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMERACIONES / LISTAS
# =============================================================================

MATERIALES_VALIDOS = ['SS304', 'SS304L', 'A53 GRB']
ESCENARIOS_VALIDOS = ['Alcalino', 'Acido', 'Neutro', 'Recuperacion']
NPS_VALIDOS = ['NPS 3"', 'NPS 4"', 'NPS 6"', 'NPS 8"', 'NPS 10"', 'NPS 12"']
SCHEDULES_SS = ['10S', '20S', '30S', '40S']
SCHEDULES_A53 = ['10', '20', '30', '40']


# =============================================================================
# REQUESTS
# =============================================================================

class CalcularVidaRequest(BaseModel):
    material: str = Field(..., description="Material de la tubería")
    nps: str = Field(..., description="Diámetro nominal")
    schedule: str = Field(..., description="Cédula de la tubería")
    escenario: str = Field(..., description="Escenario de servicio")
    Cs: float = Field(8.0, ge=0, le=80, description="Consistencia de pulpa (%)")
    v: float = Field(2.0, ge=0, le=8, description="Velocidad de flujo (m/s)")
    T: Optional[float] = Field(None, ge=20, le=250, description="Temperatura (°C); por defecto la del escenario")
    beta: float = Field(0.0, ge=0, le=0.9, description="Factor de atenuación por pulpa refinada")
    k0_override: Optional[float] = Field(None, ge=0, description="Coef. de erosión base alternativo (mm/año)/(m/s)^2.3")
    fs: float = Field(1.1, ge=1.0, le=3.0, description="Factor de seguridad")

    @field_validator('material')
    @classmethod
    def check_material(cls, v: str) -> str:
        v = v.upper()
        if v not in MATERIALES_VALIDOS:
            raise ValueError(f"Material inválido: {v}")
        return v

    @field_validator('escenario')
    @classmethod
    def check_escenario(cls, v: str) -> str:
        v = v.capitalize()
        if v not in ESCENARIOS_VALIDOS:
            raise ValueError(f"Escenario inválido: {v}")
        return v

    @field_validator('nps')
    @classmethod
    def check_nps(cls, v: str) -> str:
        if v not in NPS_VALIDOS:
            raise ValueError(f"Diámetro inválido: {v}")
        return v

    @field_validator('schedule')
    @classmethod
    def check_schedule(cls, v: str, info) -> str:
        data = info.data
        material = data.get('material', '').upper()
        valid = SCHEDULES_A53 if material == 'A53 GRB' else SCHEDULES_SS
        if v not in valid:
            raise ValueError(f"Cédula inválida {v} para {material}")
        return v


class TablaRequest(BaseModel):
    material: str = Field(..., description="Material de la tubería")
    Cs: float = Field(6.0, ge=0, le=80, description="Consistencia de pulpa (%)")
    v: float = Field(2.5, ge=0, le=8, description="Velocidad de flujo (m/s)")
    escenario: Optional[str] = Field(None, description="Escenario a filtrar (opcional)")
    T: Optional[float] = Field(None, ge=20, le=250, description="Temperatura (°C)")
    beta: float = Field(0.0, ge=0, le=0.9, description="Factor de atenuación por pulpa refinada")
    k0_override: Optional[float] = Field(None, ge=0, description="Coef. de erosión base alternativo")
    fs: float = Field(1.1, ge=1.0, le=3.0, description="Factor de seguridad")

    @field_validator('material')
    @classmethod
    def check_material(cls, v: str) -> str:
        v = v.upper()
        if v not in MATERIALES_VALIDOS:
            raise ValueError(f"Material inválido: {v}")
        return v

    @field_validator('escenario')
    @classmethod
    def check_escenario(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.capitalize()
        if v not in ESCENARIOS_VALIDOS:
            raise ValueError(f"Escenario inválido: {v}")
        return v


class SensibilidadRequest(BaseModel):
    material: str = Field(..., description="Material de la tubería")
    nps: str = Field(..., description="Diámetro nominal")
    schedule: str = Field(..., description="Cédula de la tubería")
    escenario: str = Field(..., description="Escenario de servicio")
    Cs: float = Field(6.0, ge=0, le=80, description="Consistencia de pulpa (%)")
    v: float = Field(3.5, ge=0, le=8, description="Velocidad de flujo (m/s)")
    T: Optional[float] = Field(None, ge=20, le=250, description="Temperatura (°C)")
    beta: float = Field(0.0, ge=0, le=0.9, description="Factor de atenuación por pulpa refinada")
    k0_override: Optional[float] = Field(None, ge=0, description="Coef. de erosión base alternativo")
    fs_vals: List[float] = Field([1.1, 1.5, 2.0], description="Valores de FS a evaluar")

    @field_validator('material')
    @classmethod
    def check_material(cls, v: str) -> str:
        v = v.upper()
        if v not in MATERIALES_VALIDOS:
            raise ValueError(f"Material inválido: {v}")
        return v

    @field_validator('escenario')
    @classmethod
    def check_escenario(cls, v: str) -> str:
        v = v.capitalize()
        if v not in ESCENARIOS_VALIDOS:
            raise ValueError(f"Escenario inválido: {v}")
        return v

    @field_validator('nps')
    @classmethod
    def check_nps(cls, v: str) -> str:
        if v not in NPS_VALIDOS:
            raise ValueError(f"Diámetro inválido: {v}")
        return v

    @field_validator('schedule')
    @classmethod
    def check_schedule(cls, v: str, info) -> str:
        data = info.data
        material = data.get('material', '').upper()
        valid = SCHEDULES_A53 if material == 'A53 GRB' else SCHEDULES_SS
        if v not in valid:
            raise ValueError(f"Cédula inválida {v} para {material}")
        return v


class ExportRequest(BaseModel):
    material: str = Field(..., description="Material de la tubería")
    Cs: float = Field(6.0, ge=0, le=80, description="Consistencia de pulpa (%)")
    v: float = Field(2.5, ge=0, le=8, description="Velocidad de flujo (m/s)")
    escenario: Optional[str] = Field(None, description="Escenario a filtrar (opcional)")
    T: Optional[float] = Field(None, ge=20, le=250, description="Temperatura (°C)")
    beta: float = Field(0.0, ge=0, le=0.9, description="Factor de atenuación por pulpa refinada")
    k0_override: Optional[float] = Field(None, ge=0, description="Coef. de erosión base alternativo")
    fs: float = Field(1.1, ge=1.0, le=3.0, description="Factor de seguridad")

    @field_validator('material')
    @classmethod
    def check_material(cls, v: str) -> str:
        v = v.upper()
        if v not in MATERIALES_VALIDOS:
            raise ValueError(f"Material inválido: {v}")
        return v

    @field_validator('escenario')
    @classmethod
    def check_escenario(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.capitalize()
        if v not in ESCENARIOS_VALIDOS:
            raise ValueError(f"Escenario inválido: {v}")
        return v


# =============================================================================
# RESPONSES
# =============================================================================

class CalcularVidaResponse(BaseModel):
    material: str
    nps: str
    schedule: str
    escenario: str
    Cs: float
    v: float
    T: float
    fs: float
    vida_util: float
    t_disp: float
    t_min: float
    W_quim: float
    W_ero: float
    W_total: float
    S: float
    unidades: Dict[str, str]
    advertencias: List[str] = Field(default_factory=list, description="Advertencias de rango de validez del modelo")


class TablaResponse(BaseModel):
    material: str
    Cs: float
    v: float
    T: Optional[float]
    fs: float
    beta: float
    escenarios: List[str]
    diametros: List[str]
    schedules: List[str]
    valores: Dict[str, Dict[str, Dict[str, float]]]
    advertencias: List[str] = Field(default_factory=list, description="Advertencias de rango de validez del modelo")


class SensibilidadResponse(BaseModel):
    material: str
    nps: str
    schedule: str
    escenario: str
    Cs: float
    v: float
    T: Optional[float]
    resultados: Dict[str, float]
    advertencias: List[str] = Field(default_factory=list, description="Advertencias de rango de validez del modelo")


class CondicionCriticaRow(BaseModel):
    nps: str
    ss304_s10: int
    ss304L_s10: int
    ss304_s40: int
    ss304L_s40: int
    a53_s40: int


class CondicionCriticaResponse(BaseModel):
    parametros: Dict[str, float]
    filas: List[CondicionCriticaRow]
    advertencias: List[str] = Field(default_factory=list, description="Advertencias específicas de la condición crítica calibrada")


class MaterialInfo(BaseModel):
    material: str
    schedules: List[str]
    descripcion: str


class EscenarioInfo(BaseModel):
    id: str
    nombre: str
    T_ref: float
    v_tip: float
    Cs_tip: float
    W_quim_SS: float
    W_quim_A53: float


class MaterialesResponse(BaseModel):
    materiales: List[MaterialInfo]
    diametros: List[str]


class EscenariosResponse(BaseModel):
    escenarios: List[EscenarioInfo]


# =============================================================================
# DASHBOARD EJECUTIVO
# =============================================================================

class DashboardKpis(BaseModel):
    vida_ss304_40s: float
    vida_ss304l_40s: float
    vida_a53_40: float
    t_disp_ss304_40s: float
    W_quim: float
    W_ero: float
    W_total: float
    unidades: Dict[str, str]


class DashboardCasoBase(BaseModel):
    descripcion: str
    parametros: Dict[str, float]
    nps_ref: str
    kpis: DashboardKpis


class DashboardCondicionTipica(BaseModel):
    escenario: str
    T: float
    v: float
    Cs: float


class DashboardHeatmap(BaseModel):
    materiales: List[str]
    escenarios: List[str]
    escenarios_nombres: List[str]
    condiciones: List[DashboardCondicionTipica]
    valores: List[List[float]]


class DashboardSerie(BaseModel):
    id: str
    nombre: str
    valores: List[int]


class DashboardComparativa(BaseModel):
    nps: List[str]
    series: List[DashboardSerie]


class DashboardDescomposicion(BaseModel):
    materiales: List[str]
    W_quim: List[float]
    W_ero: List[float]
    unidad: str


class DashboardSensibilidad(BaseModel):
    material: str
    nps: str
    schedule: str
    fs: List[float]
    vida: List[float]


class DashboardResponse(BaseModel):
    caso_base: DashboardCasoBase
    heatmap: DashboardHeatmap
    comparativa: DashboardComparativa
    descomposicion: DashboardDescomposicion
    sensibilidad_fs: DashboardSensibilidad
    condicion_critica: CondicionCriticaResponse
    advertencias: List[str] = Field(default_factory=list)
