# -*- coding: utf-8 -*-
"""
Motor de cálculo de vida útil por corrosión-erosión para tuberías.
Basado en la metodología del informe P2603-PR-INF-001 (convención 2026-06-12).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

# =============================================================================
# DATOS DE TUBERÍAS
# =============================================================================

# ASME B36.19M — espesores nominales para SS304 / SS304L
PIPES_SS = {
    'NPS 3"':  {'OD': 88.9,  't_10S': 3.05, 't_20S': 4.50, 't_30S': 5.00, 't_40S': 5.49},
    'NPS 4"':  {'OD': 114.3, 't_10S': 3.05, 't_20S': 4.50, 't_30S': 5.26, 't_40S': 6.02},
    'NPS 6"':  {'OD': 168.3, 't_10S': 3.40, 't_20S': 5.50, 't_30S': 6.31, 't_40S': 7.11},
    'NPS 8"':  {'OD': 219.1, 't_10S': 3.76, 't_20S': 6.35, 't_30S': 7.27, 't_40S': 8.18},
    'NPS 10"': {'OD': 273.1, 't_10S': 4.19, 't_20S': 6.35, 't_30S': 7.81, 't_40S': 9.27},
    'NPS 12"': {'OD': 323.9, 't_10S': 4.57, 't_20S': 6.35, 't_30S': 7.94, 't_40S': 9.53},
}


def _interp_a53(t10: float, t40: float, frac: float) -> float:
    """Interpola espesores A53 para cédulas no tabuladas en B36.10M."""
    return round(t10 + (t40 - t10) * frac, 2)


# ASME B36.10M — espesores nominales para A53 Gr B
PIPES_A53 = {
    'NPS 3"':  {'OD': 88.9,  't_10': 3.05, 't_20': _interp_a53(3.05, 5.49, 1/3), 't_30': _interp_a53(3.05, 5.49, 2/3), 't_40': 5.49},
    'NPS 4"':  {'OD': 114.3, 't_10': 3.05, 't_20': _interp_a53(3.05, 6.02, 1/3), 't_30': _interp_a53(3.05, 6.02, 2/3), 't_40': 6.02},
    'NPS 6"':  {'OD': 168.3, 't_10': 3.40, 't_20': _interp_a53(3.40, 7.11, 1/3), 't_30': _interp_a53(3.40, 7.11, 2/3), 't_40': 7.11},
    'NPS 8"':  {'OD': 219.1, 't_10': 3.76, 't_20': 6.35, 't_30': 7.04, 't_40': 8.18},
    'NPS 10"': {'OD': 273.1, 't_10': 4.19, 't_20': 6.35, 't_30': 7.80, 't_40': 9.27},
    'NPS 12"': {'OD': 323.9, 't_10': 4.57, 't_20': 6.35, 't_30': 8.38, 't_40': 10.31},
}


# =============================================================================
# MATERIALES
# =============================================================================

SCHEDULES_SS = ['10S', '20S', '30S', '40S']
SCHEDULES_A53 = ['10', '20', '30', '40']
DIAMETROS_ORDEN = ['NPS 3"', 'NPS 4"', 'NPS 6"', 'NPS 8"', 'NPS 10"', 'NPS 12"']

MATERIALS = {
    'SS304': {
        'pipes': PIPES_SS,
        'schedules': SCHEDULES_SS,
        'S_table': {38: 138, 100: 138, 150: 138, 200: 110, 250: 103, 300: 97, 350: 92, 400: 88},
        'E': 1.0,
        'c': 1.5,
        'k0': 0.008,
        'gamma': 1.0,
    },
    'SS304L': {
        'pipes': PIPES_SS,
        'schedules': SCHEDULES_SS,
        'S_table': {38: 115, 100: 115, 150: 115, 200: 104, 250: 96, 300: 90},
        'E': 1.0,
        'c': 1.5,
        'k0': 0.008,
        'gamma': 0.85,
    },
    'A53 GRB': {
        'pipes': PIPES_A53,
        'schedules': SCHEDULES_A53,
        'S_table': {38: 137, 100: 137, 150: 130, 200: 99, 250: 91, 300: 85, 350: 80, 400: 76},
        'E': 0.85,
        'c': 3.0,
        'k0': 0.025,
        'gamma': 1.0,
    },
}


# =============================================================================
# ESCENARIOS DE SERVICIO
# =============================================================================

ESCENARIOS = {
    'Alcalino': {
        'nombre': 'Alcalino (licor blanco/negro)',
        'W_quim_SS': 0.052,
        'W_quim_A53': 0.20,
        'T_ref': 150.0,
        'v_tip': 1.5,
        'Cs_tip': 8.0,
    },
    'Acido': {
        'nombre': 'Ácido severo (bleach plant C/D)',
        'W_quim_SS': 0.55,
        'W_quim_A53': 2.50,
        'T_ref': 70.0,
        'v_tip': 3.0,
        'Cs_tip': 8.0,
    },
    'Neutro': {
        'nombre': 'Neutro-oxidante (white water)',
        'W_quim_SS': 0.09,
        'W_quim_A53': 0.30,
        'T_ref': 50.0,
        'v_tip': 2.05,
        'Cs_tip': 3.0,
    },
    'Recuperacion': {
        'nombre': 'Recuperación (evaporadores)',
        'W_quim_SS': 0.035,
        'W_quim_A53': 0.14,
        'T_ref': 120.0,
        'v_tip': 1.15,
        'Cs_tip': 15.0,
    },
}


# =============================================================================
# PARÁMETROS COMUNES
# =============================================================================

P = 1.0          # MPa
Y = 0.4          # coeficiente ASME B31.3 eq. 3a
ALPHA = 0.06     # factor consistencia de pulpa
N_ERO = 2.3      # exponente velocidad erosión
DEFAULT_FS = 1.1
GAMMA_304L = 0.85


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _validate_material(material: str) -> str:
    material = material.upper()
    if material not in MATERIALS:
        raise ValueError(f"Material no soportado: {material}. Use: {list(MATERIALS.keys())}")
    return material


def _validate_escenario(escenario: str) -> str:
    escenario = escenario.capitalize()
    if escenario not in ESCENARIOS:
        raise ValueError(f"Escenario no soportado: {escenario}. Use: {list(ESCENARIOS.keys())}")
    return escenario


def get_S(material: str, T: float) -> float:
    """Interpola el esfuerzo admisible S (MPa) según ASME B31.3 Tabla A-1."""
    material = _validate_material(material)
    table = MATERIALS[material]['S_table']
    temps = sorted(table.keys())
    if T <= temps[0]:
        return float(table[temps[0]])
    if T >= temps[-1]:
        return float(table[temps[-1]])
    for i in range(len(temps) - 1):
        t0, t1 = temps[i], temps[i + 1]
        if t0 <= T <= t1:
            return float(table[t0] + (table[t1] - table[t0]) * (T - t0) / (t1 - t0))
    return float(table[temps[-1]])


def t_min(OD: float, material: str, T: float) -> float:
    """Espesor mínimo requerido por ASME B31.3 ecuación (3a), en mm."""
    material = _validate_material(material)
    mat = MATERIALS[material]
    S = get_S(material, T)
    return (P * OD) / (2 * (S * mat['E'] + P * Y)) + mat['c']


def get_t_nom(material: str, nps: str, schedule: str) -> float:
    """Devuelve el espesor nominal (mm) para una tubería dada."""
    material = _validate_material(material)
    mat = MATERIALS[material]
    key = f"t_{schedule.replace('S', '')}" if material == 'A53 GRB' else f"t_{schedule}"
    pipes = mat['pipes']
    if nps not in pipes:
        raise ValueError(f"Diámetro no soportado: {nps}. Use: {DIAMETROS_ORDEN}")
    if key not in pipes[nps]:
        raise ValueError(f"Cédula no soportada: {schedule} para {material}")
    return float(pipes[nps][key])


def get_OD(material: str, nps: str) -> float:
    """Devuelve el diámetro exterior (mm)."""
    material = _validate_material(material)
    pipes = MATERIALS[material]['pipes']
    if nps not in pipes:
        raise ValueError(f"Diámetro no soportado: {nps}")
    return float(pipes[nps]['OD'])


def calc_erosion(k0: float, v: float, Cs: float, beta: float = 0.0) -> float:
    """Tasa de erosión mecánica W_ero (mm/año)."""
    k_eff = k0 * (1 + ALPHA * Cs)
    return k_eff * (v ** N_ERO) * (1 - beta)


def generar_advertencias(
    material: str,
    escenario: str,
    Cs: float,
    v: float,
    T: Optional[float],
    beta: float,
    k0_override: Optional[float],
    fs: float,
) -> List[str]:
    """
    Genera advertencias de rango de validez basadas en la metodología del informe.
    """
    adv: List[str] = []
    esc = ESCENARIOS.get(_validate_escenario(escenario), {})
    T_ref = esc.get('T_ref', T)
    T_eff = T if T is not None else T_ref

    if v >= 3.0:
        adv.append("Velocidad ≥ 3,0 m/s: la sinergia erosión-corrosión (Ws) puede no ser despreciable.")
    if Cs >= 12.0:
        adv.append("Consistencia ≥ 12 %: la sinergia erosión-corrosión (Ws) puede no ser despreciable.")
    if T_ref is not None and abs(T_eff - T_ref) > 50.0:
        adv.append(f"Extrapolación de temperatura de {T_ref:.0f} °C a {T_eff:.0f} °C; el coeficiente de Arrhenius tiene incertidumbre ±30 %.")
    if beta > 0.0 and not (0.15 <= beta <= 0.40):
        adv.append("Factor β fuera del rango representativo calibrado (0,15–0,40); incertidumbre del modelo de pulpa refinada ±50 %.")
    if k0_override is not None and not math.isclose(k0_override, 0.0035, rel_tol=1e-3):
        adv.append("Coeficiente de erosión base alternativo; verificar validez para la aplicación específica.")
    if not math.isclose(fs, DEFAULT_FS, rel_tol=1e-3):
        adv.append(f"Factor de seguridad FS = {fs} distinto al adoptado en el informe (FS = {DEFAULT_FS:.1f}).")
    return adv


def calc_vida(
    OD: float,
    t_nom: float,
    material: str,
    escenario: str,
    Cs: float,
    v: float,
    T: Optional[float] = None,
    beta: float = 0.0,
    k0_override: Optional[float] = None,
    fs: float = DEFAULT_FS,
    W_quim_override: Optional[float] = None,
) -> Dict[str, float]:
    """
    Calcula la vida útil y descompone las tasas de desgaste.

    Si W_quim_override se proporciona, se usa ese valor directamente (sin gamma ni
    corrección de temperatura). Útil para la condición crítica 60 °C calibrada.

    Retorna dict con: vida_util, t_disp, t_min, W_quim, W_ero, W_total, S.
    """
    material = _validate_material(material)
    escenario = _validate_escenario(escenario)
    mat = MATERIALS[material]
    esc = ESCENARIOS[escenario]

    if T is None:
        T = esc['T_ref']

    # Componente química
    if W_quim_override is not None:
        W_quim = W_quim_override
    else:
        if material == 'A53 GRB':
            W_quim = esc['W_quim_A53']
        else:
            W_quim = esc['W_quim_SS']
        W_quim = W_quim * mat['gamma']

        # Corrección de temperatura Arrhenius sobre la componente química
        if T != esc['T_ref']:
            W_quim = W_quim * math.exp(0.015 * (T - esc['T_ref']))

    # Espesor disponible
    tm = t_min(OD, material, T)
    t_disp = t_nom - tm
    advertencias = generar_advertencias(material, escenario, Cs, v, T, beta, k0_override, fs)
    if t_disp <= 0:
        advertencias.insert(0, "El espesor nominal es insuficiente para la presión y temperatura dadas (t_disp ≤ 0).")
        return {
            'vida_util': 0.0,
            't_disp': t_disp,
            't_min': tm,
            'W_quim': W_quim,
            'W_ero': 0.0,
            'W_total': W_quim,
            'S': get_S(material, T),
            'advertencias': advertencias,
        }

    # Componente erosión
    k0 = k0_override if k0_override is not None else mat['k0']
    W_ero = calc_erosion(k0, v, Cs, beta)
    W_total = W_quim + W_ero

    vida = t_disp / (W_total * fs)
    advertencias = generar_advertencias(material, escenario, Cs, v, T, beta, k0_override, fs)
    return {
        'vida_util': vida,
        't_disp': t_disp,
        't_min': tm,
        'W_quim': W_quim,
        'W_ero': W_ero,
        'W_total': W_total,
        'S': get_S(material, T),
        'advertencias': advertencias,
    }


def calcular_tabla(
    material: str,
    Cs: float,
    v: float,
    escenario: Optional[str] = None,
    T: Optional[float] = None,
    beta: float = 0.0,
    k0_override: Optional[float] = None,
    fs: float = DEFAULT_FS,
) -> Dict[str, Dict[str, Dict[str, float]]]:
    """
    Genera matriz de vida útil [escenario][diámetro][cédula].
    Si se especifica escenario, el dict externo tiene una sola entrada.
    """
    material = _validate_material(material)
    mat = MATERIALS[material]
    schedules = mat['schedules']
    escenarios = [escenario] if escenario else list(ESCENARIOS.keys())

    resultados: Dict[str, Dict[str, Dict[str, float]]] = {}
    for esc in escenarios:
        resultados[esc] = {}
        for nps in DIAMETROS_ORDEN:
            resultados[esc][nps] = {}
            OD = get_OD(material, nps)
            for sch in schedules:
                t_nom = get_t_nom(material, nps, sch)
                res = calc_vida(OD, t_nom, material, esc, Cs, v, T, beta, k0_override, fs)
                resultados[esc][nps][sch] = res['vida_util']
    return resultados


def sensibilidad_fs(
    OD: float,
    t_nom: float,
    material: str,
    escenario: str,
    Cs: float,
    v: float,
    T: Optional[float] = None,
    beta: float = 0.0,
    k0_override: Optional[float] = None,
    fs_vals: Tuple[float, ...] = (1.1, 1.5, 2.0),
) -> Dict[float, float]:
    """Calcula vida útil para distintos factores de seguridad."""
    return {
        fs: calc_vida(OD, t_nom, material, escenario, Cs, v, T, beta, k0_override, fs)['vida_util']
        for fs in fs_vals
    }


def condicion_critica_60C() -> List[Dict[str, int]]:
    """
    Replica la tabla de condición crítica del Resumen Ejecutivo.
    Alcalino, 60 °C, Cs=6 %, v=3.5 m/s, pulpa refinada (β=0.25, k0_ref=0.0035).
    """
    T = 60.0
    T_ref = 150.0
    k0_ref = 0.0035
    beta = 0.25
    esc = 'Alcalino'

    rows = []
    for nps in DIAMETROS_ORDEN:
        data = PIPES_SS[nps]
        OD = data['OD']

        W_quim_ss = ESCENARIOS[esc]['W_quim_SS'] * math.exp(0.015 * (T - T_ref))
        W_quim_a53 = ESCENARIOS[esc]['W_quim_A53'] * math.exp(0.015 * (T - T_ref))
        k0_ref_a53 = 0.025 * (k0_ref / 0.008)

        t_40_a53 = PIPES_A53[nps]['t_40'] if nps != 'NPS 12"' else 10.31

        val_ss304_s10 = calc_vida(OD, data['t_10S'], 'SS304', esc, 6.0, 3.5, T, beta, k0_ref, W_quim_override=W_quim_ss)['vida_util']
        val_ss304L_s10 = calc_vida(OD, data['t_10S'], 'SS304L', esc, 6.0, 3.5, T, beta, k0_ref, W_quim_override=GAMMA_304L * W_quim_ss)['vida_util']
        val_ss304_s40 = calc_vida(OD, data['t_40S'], 'SS304', esc, 6.0, 3.5, T, beta, k0_ref, W_quim_override=W_quim_ss)['vida_util']
        val_ss304L_s40 = calc_vida(OD, data['t_40S'], 'SS304L', esc, 6.0, 3.5, T, beta, k0_ref, W_quim_override=GAMMA_304L * W_quim_ss)['vida_util']
        val_a53_s40 = calc_vida(OD, t_40_a53, 'A53 GRB', esc, 6.0, 3.5, T, beta, k0_ref_a53, W_quim_override=W_quim_a53)['vida_util']

        rows.append({
            'nps': nps.replace('NPS ', '').replace('"', '"'),
            'ss304_s10': int(math.floor(val_ss304_s10)),
            'ss304L_s10': int(math.floor(val_ss304L_s10)),
            'ss304_s40': int(math.floor(val_ss304_s40)),
            'ss304L_s40': int(math.floor(val_ss304L_s40)),
            'a53_s40': int(math.floor(val_a53_s40)),
        })
    return rows


def format_vida(vida: float) -> float:
    """Redondeo consistente con las tablas del informe."""
    if vida <= 0:
        return 0.0
    if vida < 1:
        return round(vida, 1)
    return float(int(math.floor(vida)))
