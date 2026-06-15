# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# MÓDULO: motor_calculo.py (VERSÃO 2.1 - CORRIGIDA)
# --------------------------------------------------------------------------
import numpy as np
from typing import List, Dict
import estruturas

# --- As funções de cálculo (_calcular_mhs_svaj, etc.) permanecem as mesmas ---
def _calcular_mhs_svaj(theta_rad_trecho: np.ndarray, seg: estruturas.SegmentoCame) -> tuple:
    H = seg.H
    beta_rad = np.deg2rad(seg.beta)
    theta_norm = theta_rad_trecho - np.deg2rad(seg.theta_inicio)
    s_local = (H / 2) * (1 - np.cos(np.pi * theta_norm / beta_rad))
    s_prime = (H * np.pi / (2 * beta_rad)) * np.sin(np.pi * theta_norm / beta_rad)
    s_double_prime = (H * np.pi**2 / (2 * beta_rad**2)) * np.cos(np.pi * theta_norm / beta_rad)
    s_triple_prime = -(H * np.pi**3 / (2 * beta_rad**3)) * np.sin(np.pi * theta_norm / beta_rad)
    if seg.tipo == 'subida':
        S = seg.S_inicio + s_local
        V_geo, A_geo, J_geo = s_prime, s_double_prime, s_triple_prime
    elif seg.tipo == 'descida':
        S = seg.S_inicio - s_local
        V_geo, A_geo, J_geo = -s_prime, -s_double_prime, -s_triple_prime
    return S, V_geo, A_geo, J_geo

def _calcular_cicloidal_svaj(theta_rad_trecho: np.ndarray, seg: estruturas.SegmentoCame) -> tuple:
    H = seg.H
    beta_rad = np.deg2rad(seg.beta)
    theta_norm = theta_rad_trecho - np.deg2rad(seg.theta_inicio)
    s_local = H * (theta_norm / beta_rad - (1 / (2 * np.pi)) * np.sin(2 * np.pi * theta_norm / beta_rad))
    s_prime = (H / beta_rad) * (1 - np.cos(2 * np.pi * theta_norm / beta_rad))
    s_double_prime = (2 * H * np.pi / beta_rad**2) * np.sin(2 * np.pi * theta_norm / beta_rad)
    s_triple_prime = (4 * H * np.pi**2 / beta_rad**3) * np.cos(2 * np.pi * theta_norm / beta_rad)
    if seg.tipo == 'subida':
        S = seg.S_inicio + s_local
        V_geo, A_geo, J_geo = s_prime, s_double_prime, s_triple_prime
    elif seg.tipo == 'descida':
        S = seg.S_inicio - s_local
        V_geo, A_geo, J_geo = -s_prime, -s_double_prime, -s_triple_prime
    return S, V_geo, A_geo, J_geo

def _calcular_polinomial_345_svaj(theta_rad_trecho: np.ndarray, seg: estruturas.SegmentoCame) -> tuple:
    H = seg.H
    beta_rad = np.deg2rad(seg.beta)
    theta_norm = theta_rad_trecho - np.deg2rad(seg.theta_inicio)
    ratio = theta_norm / beta_rad
    s_local = H * (10 * ratio**3 - 15 * ratio**4 + 6 * ratio**5)
    s_prime = (H / beta_rad) * (30 * ratio**2 - 60 * ratio**3 + 30 * ratio**4)
    s_double_prime = (H / beta_rad**2) * (60 * ratio - 180 * ratio**2 + 120 * ratio**3)
    s_triple_prime = (H / beta_rad**3) * (60 - 360 * ratio + 360 * ratio**2)
    if seg.tipo == 'subida':
        S = seg.S_inicio + s_local
        V_geo, A_geo, J_geo = s_prime, s_double_prime, s_triple_prime
    elif seg.tipo == 'descida':
        S = seg.S_inicio - s_local
        V_geo, A_geo, J_geo = -s_prime, -s_double_prime, -s_triple_prime
    return S, V_geo, A_geo, J_geo


FUNCOES_MOVIMENTO = {
    'mhs': _calcular_mhs_svaj,
    'cicloidal': _calcular_cicloidal_svaj,
    'polinomial_345': _calcular_polinomial_345_svaj,
}

def processar_perfil_completo(segmentos: List[estruturas.SegmentoCame], lei_movimento_global: str, rpm: float, tipo_analise: str) -> Dict[str, np.ndarray]:
    # 1. Preparação dos arrays e constantes
    omega = rpm * 2 * np.pi / 60.0
    #num_pontos = 360 * 2 + 1
    num_pontos = 3600 + 1
    pontos_por_grau = (num_pontos - 1) / 360.0
    
    theta_graus = np.linspace(0, 360, num_pontos, endpoint=True)
    theta_rad = np.deg2rad(theta_graus)
    
    S = np.zeros_like(theta_graus)
    V = np.zeros_like(theta_graus)
    A = np.zeros_like(theta_graus)
    J = np.zeros_like(theta_graus)

    # 2. Iteração sobre cada segmento para preencher os arrays
    for i, seg in enumerate(segmentos):
        # --- CORREÇÃO: Cálculo direto dos índices ---
        start_idx = int(round(seg.theta_inicio * pontos_por_grau))
        end_idx = int(round(seg.theta_fim * pontos_por_grau))
        
        # Garante que o último ponto (360°) seja incluído no último segmento
        if i == len(segmentos) - 1:
            end_idx = num_pontos -1

        indices = np.arange(start_idx, end_idx + 1)
        # Previne que o mesmo índice seja pego duas vezes (exceto o primeiro ponto)
        if i > 0:
            indices = indices[1:]

        if len(indices) == 0:
            continue

        theta_rad_trecho = theta_rad[indices]

        if seg.tipo == 'parada':
            S[indices] = seg.S_inicio
        
        elif seg.tipo in ['subida', 'descida']:
            funcao_calculo = FUNCOES_MOVIMENTO[lei_movimento_global]
            s_trecho, v_geo, a_geo, j_geo = funcao_calculo(theta_rad_trecho, seg)
            
            S[indices] = s_trecho

            if tipo_analise == 'cinematico':
                V[indices] = v_geo * omega
                A[indices] = a_geo * omega**2
                J[indices] = j_geo * omega**3
            else: # tipo_analise == 'geometrico'
                V[indices] = v_geo
                A[indices] = a_geo
                J[indices] = j_geo
            
    # 3. Retorno dos resultados completos
    return {
        'theta': theta_graus,
        's': S,
        'v': V,
        'a': A,
        'j': J
    }