# -*- coding: utf-8 -*-
"""
Tests de regresión del motor de cálculo contra audit_recalculo_v2.py.
Tolerancia: ±1 año (±0.05 para valores < 1).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

# Asegurar que webapp esté en el path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

from webapp import corrosion_model as cm


def _fmt(vida: float):
    if vida <= 0:
        return 0
    if vida < 1:
        return round(vida, 1)
    return int(math.floor(vida))


def _ok(calc, ref, tol=1.0):
    if isinstance(calc, float) and isinstance(ref, float):
        if calc < 1 and ref < 1:
            return abs(calc - ref) <= 0.05
        return abs(calc - ref) <= tol
    return calc == ref


# =============================================================================
# 1. Tablas SS304L Sección 14 (96 celdas)
# =============================================================================
# Rev.2 — SS304L dual certificado TP304/304L (S = 138 MPa); regen_valores_rev2.py
PUB_304L = {
    "10S": {
        "Alcalino": [15, 13, 15, 17, 20, 23],
        "Acido": [1, 1, 1, 2, 2, 2],
        "Neutro": [8, 8, 9, 10, 12, 13],
        "Recuperacion": [22, 20, 23, 26, 30, 34],
    },
    "20S": {
        "Alcalino": [32, 31, 41, 49, 47, 45],
        "Acido": [3, 3, 5, 5, 5, 5],
        "Neutro": [19, 18, 24, 29, 27, 26],
        "Recuperacion": [48, 46, 60, 72, 69, 65],
    },
    "30S": {
        "Alcalino": [38, 40, 51, 60, 65, 64],
        "Acido": [4, 4, 6, 7, 7, 7],
        "Neutro": [22, 24, 30, 36, 38, 38],
        "Recuperacion": [56, 60, 75, 89, 95, 94],
    },
    "40S": {
        "Alcalino": [44, 50, 61, 72, 83, 83],
        "Acido": [5, 6, 7, 8, 10, 10],
        "Neutro": [26, 29, 36, 42, 49, 49],
        "Recuperacion": [65, 73, 89, 105, 121, 122],
    },
}


def test_tablas_ss304l():
    fails = 0
    for sch in PUB_304L:
        for esc in PUB_304L[sch]:
            W = cm.GAMMA_304L * cm.ESCENARIOS[esc]['W_quim_SS'] + cm.calc_erosion(0.008, cm.ESCENARIOS[esc]['v_tip'], cm.ESCENARIOS[esc]['Cs_tip'])
            for i, nps in enumerate(cm.DIAMETROS_ORDEN):
                t_nom = cm.get_t_nom('SS304L', nps, sch)
                OD = cm.get_OD('SS304L', nps)
                vida = cm.calc_vida(OD, t_nom, 'SS304L', esc, cm.ESCENARIOS[esc]['Cs_tip'], cm.ESCENARIOS[esc]['v_tip'], fs=1.1)['vida_util']
                calc = _fmt(vida)
                ref = PUB_304L[sch][esc][i]
                if calc != ref:
                    fails += 1
                    print(f"DIFF SS304L {sch} {esc} {nps}: calc={calc} ref={ref}")
    print(f"1. Tablas SS304L Secc.14: {96 - fails}/96 celdas OK")
    return fails


# =============================================================================
# 2. Tabla A53 Sección 9 (18 celdas)
# =============================================================================
PUB_A53 = {
    "Alcalino": [6, 7, 10, 12, 15, 18],
    "Neutro": [4, 5, 6, 8, 10, 11],
    "Recuperacion": [9, 11, 14, 18, 22, 26],
}


def test_tabla_a53():
    fails = 0
    for esc in PUB_A53:
        T = cm.ESCENARIOS[esc]['T_ref']
        for i, nps in enumerate(cm.DIAMETROS_ORDEN):
            t_nom = cm.get_t_nom('A53 GRB', nps, '40')
            OD = cm.get_OD('A53 GRB', nps)
            W = cm.ESCENARIOS[esc]['W_quim_A53'] + cm.calc_erosion(0.025, cm.ESCENARIOS[esc]['v_tip'], cm.ESCENARIOS[esc]['Cs_tip'])
            vida = cm.calc_vida(OD, t_nom, 'A53 GRB', esc, cm.ESCENARIOS[esc]['Cs_tip'], cm.ESCENARIOS[esc]['v_tip'], T=T, fs=1.1)['vida_util']
            calc = _fmt(vida)
            ref = PUB_A53[esc][i]
            if calc != ref:
                fails += 1
                print(f"DIFF A53 {esc} {nps}: calc={calc} ref={ref}")
    print(f"2. Tabla A53 Secc.9: {18 - fails}/18 celdas OK")
    return fails


# =============================================================================
# 3. Condición crítica 60 °C (30 celdas)
# =============================================================================
# Rev.2 — dual certificado: SS304L >= SS304 en todas las celdas
PUB_CRITICA = {
    'NPS 3"':  [14, 14, 43, 44, 7],
    'NPS 4"':  [13, 13, 48, 49, 9],
    'NPS 6"':  [15, 15, 58, 60, 12],
    'NPS 8"':  [17, 17, 69, 71, 15],
    'NPS 10"': [20, 20, 79, 82, 18],
    'NPS 12"': [22, 22, 80, 82, 21],
}


def test_condicion_critica():
    filas = cm.condicion_critica_60C()
    fails = 0
    for r in filas:
        nps = 'NPS ' + r['nps']
        calc = [r['ss304_s10'], r['ss304L_s10'], r['ss304_s40'], r['ss304L_s40'], r['a53_s40']]
        ref = PUB_CRITICA[nps]
        for c, rv in zip(calc, ref):
            if c != rv:
                fails += 1
                print(f"DIFF critica {nps}: calc={calc} ref={ref}")
                break
    print(f"3. Condición crítica 60 °C: {30 - fails}/30 celdas OK")
    return fails


# =============================================================================
# 4. Ejemplo Sección 11 (9 celdas)
# =============================================================================
# Rev.2 — (T, vida 10S 304L, vida 40S 304L, vida 40S 304); regen_valores_rev2.py
EJEMPLO = [(60, 20, 82, 79), (80, 19, 77, 75), (120, 16, 67, 63)]


def test_ejemplo():
    fails = 0
    nps = 'NPS 10"'
    esc = 'Alcalino'
    for T, p10, p40L, p40 in EJEMPLO:
        OD = cm.get_OD('SS304L', nps)
        t10 = cm.get_t_nom('SS304L', nps, '10S')
        t40 = cm.get_t_nom('SS304L', nps, '40S')
        c10 = _fmt(cm.calc_vida(OD, t10, 'SS304L', esc, 6.0, 3.5, T=T, beta=0.25, k0_override=0.0035, fs=1.1)['vida_util'])
        c40L = _fmt(cm.calc_vida(OD, t40, 'SS304L', esc, 6.0, 3.5, T=T, beta=0.25, k0_override=0.0035, fs=1.1)['vida_util'])
        c40 = _fmt(cm.calc_vida(OD, t40, 'SS304', esc, 6.0, 3.5, T=T, beta=0.25, k0_override=0.0035, fs=1.1)['vida_util'])
        if (c10, c40L, c40) != (p10, p40L, p40):
            fails += 1
            print(f"DIFF ejemplo T={T}: ({c10},{c40L},{c40}) vs ({p10},{p40L},{p40})")
    print(f"4. Ejemplo Secc.11: {9 - fails*3}/9 celdas OK")
    return fails * 3


# =============================================================================
# 5. Anexo E (muestreo: 4 condiciones × 3 materiales × 4 escenarios × 6 NPS × 4 sch)
# =============================================================================
CONDICIONES = [
    {'Cs': 6.0, 'v': 2.5},
    {'Cs': 6.0, 'v': 3.5},
    {'Cs': 3.0, 'v': 2.5},
    {'Cs': 3.0, 'v': 3.5},
]


def test_anexo_e_muestreo():
    """Verifica que calcular_tabla() es consistente con calc_vida() celda a celda."""
    fails = 0
    for material in ['SS304', 'SS304L', 'A53 GRB']:
        for cond in CONDICIONES:
            tabla = cm.calcular_tabla(material, cond['Cs'], cond['v'])
            for esc in tabla:
                for nps in cm.DIAMETROS_ORDEN:
                    for sch in cm.MATERIALS[material]['schedules']:
                        t_nom = cm.get_t_nom(material, nps, sch)
                        OD = cm.get_OD(material, nps)
                        T = cm.ESCENARIOS[esc]['T_ref']
                        vida_direct = cm.calc_vida(OD, t_nom, material, esc, cond['Cs'], cond['v'], T=T, fs=1.1)['vida_util']
                        vida_tabla = tabla[esc][nps][sch]
                        if abs(vida_direct - vida_tabla) > 1e-9:
                            fails += 1
                            if fails <= 5:
                                print(f"DIFF AnexoE consistency {material} Cs={cond['Cs']} v={cond['v']} {esc} {nps} {sch}: {vida_direct} vs {vida_tabla}")
    print(f"5. Consistencia calc_tabla vs calc_vida: {fails} discrepancias")
    return fails


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("TESTS DE REGRESIÓN — webapp/corrosion_model.py")
    print("=" * 70)
    total = 0
    total += test_tablas_ss304l()
    total += test_tabla_a53()
    total += test_condicion_critica()
    total += test_ejemplo()
    total += test_anexo_e_muestreo()
    print()
    print("VEREDICTO:", "TODO OK" if total == 0 else f"{total} DISCREPANCIAS")
    return total


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
