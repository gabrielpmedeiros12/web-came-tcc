# =============================================================
# MÓDULO: visualizacao_web.py (VERSÃO WEB - STREAMLIT v2.0)
# =============================================================
# RESPONSABILIDADE:
# - Gerar visualizações adaptadas para o Streamlit
# - Retornar figuras matplotlib para exibição na web
# - Gerar animações em formato GIF para o Streamlit
# - Gerar relatórios PDF completos
# =============================================================

import matplotlib
matplotlib.use("Agg")  # Backend não-interativo para web

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib.patches import Circle
from matplotlib.backends.backend_pdf import PdfPages
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io 
import tempfile 
import os
import numpy as np
from typing import Dict, List
import pandas as pd
import sys
import estruturas
import streamlit as st
from datetime import datetime

# --- NOVA FUNÇÃO (não altera nenhuma lógica existente) ---
def _limpar_zero(valor, tol=1e-6):
    return 0.0 if abs(valor) < tol else valor


def _salvar_texto_em_pdf(pdf_pages, texto, titulo):
    """Função auxiliar para criar uma página de texto no PDF."""
    # Usando a classe Figure diretamente (Thread-safe)
    fig = Figure(figsize=(8.27, 11.69))  # Tamanho A4
    fig.suptitle(titulo, fontsize=16, weight='bold')
    fig.text(0.05, 0.90, texto, ha='left', va='top', wrap=True, fontsize=10, fontfamily='monospace')
    if pdf_pages:
        pdf_pages.savefig(fig)
    # plt.close(fig) não é mais necessário, pois o garbage collector do Python limpa a Figure

def gerar_tabela_resultados(resultados: Dict[str, np.ndarray], segmentos: List[estruturas.SegmentoCame], lei_movimento: str, rpm: float, tipo_analise: str) -> pd.DataFrame:
    """
    Gera um DataFrame pandas com os resultados para exibição no Streamlit.
    """
    if resultados is None:
        return None
    
    if tipo_analise == 'cinematico':
        header_v, header_a, header_j = "Veloc. (mm/s)", "Acel. (mm/s²)", "Jerk (mm/s³)"
    else:  # geometrico
        header_v, header_a, header_j = "Veloc. (mm/rad)", "Acel. (mm/rad²)", "Jerk (mm/rad³)"
    
    angulos_interesse = sorted(list(set([seg.theta_inicio for seg in segmentos] + [segmentos[-1].theta_fim])))
    theta_total, s_total, v_total, a_total, j_total = resultados['theta'], resultados['s'], resultados['v'], resultados['a'], resultados['j']
    
    data = []
    for angulo in angulos_interesse:
        idx = np.argmin(np.abs(theta_total - angulo))
        s_val, v_val, a_val, j_val = s_total[idx], v_total[idx], a_total[idx], j_total[idx]

        # --- CORREÇÃO DO -0.00 ---
        s_val = _limpar_zero(s_val)
        v_val = _limpar_zero(v_val)
        a_val = _limpar_zero(a_val)
        j_val = _limpar_zero(j_val)

        data.append({
            'Ângulo (°)': f"{angulo:.2f}",
            'Desloc. (mm)': f"{s_val:.2f}",
            header_v: f"{v_val:.2f}",
            header_a: f"{a_val:.2f}",
            header_j: f"{j_val:.2f}"
        })
    
    return pd.DataFrame(data)


def plotar_svaj_web(resultados: Dict[str, np.ndarray], lei_movimento: str, tipo_analise: str, segmentos: List[estruturas.SegmentoCame] = None):
    """
    Gera os gráficos SVAJ interativos usando Plotly para exibição no Streamlit.
    """
    if resultados is None:
        return None
    
    theta = resultados['theta']
    s, v, a, j = resultados['s'], resultados['v'], resultados['a'], resultados['j']
    
    # Textos adaptativos
    if tipo_analise == 'cinematico':
        titulo_principal = f'Diagramas SVAJ para o Movimento: {lei_movimento.upper()}'
        label_v, label_a, label_j = "V (mm/s)", "A (mm/s²)", "J (mm/s³)"
    else:
        titulo_principal = f'Diagramas para o Movimento: {lei_movimento.upper()}'
        label_v, label_a, label_j = "V (mm/rad)", "A (mm/rad²)", "J (mm/rad³)"

    # Criação do grid 2x2 interativo
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Deslocamento (S)", "Velocidade (V)", "Aceleração (A)", "Pulso (J)"),
        shared_xaxes=True, # Garante que o zoom no eixo X aplique a todos os gráficos
        vertical_spacing=0.15
    )

    # Cores inspiradas em painéis técnicos HUD
    cor_s = '#00BFFF' # Azul ciano
    cor_v = '#00FA9A' # Verde primavera
    cor_a = '#FFA500' # Laranja
    cor_j = '#FF4500' # Laranja avermelhado

    # Adicionando as linhas (Traces)
    fig.add_trace(go.Scatter(x=theta, y=s, mode='lines', name='Desloc. (S)', line=dict(color=cor_s, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=theta, y=v, mode='lines', name='Veloc. (V)', line=dict(color=cor_v, width=2)), row=1, col=2)
    fig.add_trace(go.Scatter(x=theta, y=a, mode='lines', name='Acel. (A)', line=dict(color=cor_a, width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=theta, y=j, mode='lines', name='Pulso (J)', line=dict(color=cor_j, width=2)), row=2, col=2)

   # Configuração do Layout e Interatividade
    fig.update_layout(
        template="plotly_dark", # <-- Ativa o modo escuro nativo (fontes e grades claras)
        title_text=titulo_principal,
        title_font=dict(size=20),
        height=700, 
        hovermode="x unified", 
        showlegend=False,
        margin=dict(l=40, r=40, t=80, b=40),
        plot_bgcolor='rgba(15, 15, 25, 0.8)', # Fundo dos gráficos levemente azulado/escuro (estilo HUD)
        paper_bgcolor='rgba(0, 0, 0, 0)'      # Fundo externo transparente para mesclar com o Streamlit
    )
    
    # Customização extra para as linhas de grade ficarem sutis
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(255, 255, 255, 0.1)')

    # Customização dos eixos
    fig.update_yaxes(title_text="S (mm)", row=1, col=1)
    fig.update_yaxes(title_text=label_v, row=1, col=2)
    fig.update_yaxes(title_text=label_a, row=2, col=1)
    fig.update_yaxes(title_text=label_j, row=2, col=2)
    fig.update_xaxes(title_text="Ângulo do Came (°)", row=2, col=1)
    fig.update_xaxes(title_text="Ângulo do Came (°)", row=2, col=2)

    return fig

def plotar_svaj_pdf(resultados: Dict[str, np.ndarray], lei_movimento: str, tipo_analise: str, segmentos: List[estruturas.SegmentoCame] = None):
    """
    Gera gráficos estáticos e tradicionais (Matplotlib) exclusivos para o relatório PDF.
    Fundo branco, alto contraste, próprio para impressão e artigos ABNT.
    """
    if resultados is None:
        return None
    
    theta = resultados['theta']
    s, v, a, j = resultados['s'], resultados['v'], resultados['a'], resultados['j']
    
    if tipo_analise == 'cinematico':
        titulo_principal = f'Diagramas SVAJ para o Movimento: {lei_movimento.upper()}'
        titulo_v, titulo_a, titulo_j = "Velocidade (V)", "Aceleração (A)", "Jerk (J)"
        label_v, label_a, label_j = "Velocidade (mm/s)", "Aceleração (mm/s²)", "Jerk (mm/s³)"
    else:  
        titulo_principal = f'Diagramas para o Movimento: {lei_movimento.upper()}'
        titulo_v, titulo_a, titulo_j = "Velocidade (V)", "Aceleração(A)", "Jerk(J)"
        label_v, label_a, label_j = "V (mm/rad)", "A (mm/rad²)", "J (mm/rad³)"
    
    # Usa a Figure do Matplotlib (Thread-safe)
    fig = Figure(figsize=(10, 6))
    # Força o fundo branco explicitamente
    fig.patch.set_facecolor('white') 
    
    axs = fig.subplots(2, 2, sharex=True)
    fig.suptitle(titulo_principal, fontsize=14, fontweight='bold', color='black')
    
    # Cores fechadas e tradicionais para papel
    axs[0, 0].plot(theta, s, color='black', linewidth=1.5)
    axs[0, 0].set_title('Deslocamento (S)', fontsize=12)
    axs[0, 0].set_ylabel('S (mm)', fontsize=10)
    axs[0, 0].grid(True, linestyle='--', alpha=0.5, color='gray')
    
    axs[0, 1].plot(theta, v, color='#003366', linewidth=1.5) # Azul escuro
    axs[0, 1].set_title(titulo_v, fontsize=12)
    axs[0, 1].set_ylabel(label_v, fontsize=10)
    axs[0, 1].grid(True, linestyle='--', alpha=0.5, color='gray')
    
    axs[1, 0].plot(theta, a, color='#800000', linewidth=1.5) # Vermelho escuro
    axs[1, 0].set_title(titulo_a, fontsize=12)
    axs[1, 0].set_xlabel('Ângulo do Came (°)', fontsize=10)
    axs[1, 0].set_ylabel(label_a, fontsize=10)
    axs[1, 0].grid(True, linestyle='--', alpha=0.5, color='gray')
    
    axs[1, 1].plot(theta, j, color='#CC5500', linewidth=1.5) # Laranja escuro
    axs[1, 1].set_title(titulo_j, fontsize=12)
    axs[1, 1].set_xlabel('Ângulo do Came (°)', fontsize=10)
    axs[1, 1].set_ylabel(label_j, fontsize=10)
    axs[1, 1].grid(True, linestyle='--', alpha=0.5, color='gray')
    
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig

def plotar_perfil_came_web(resultados: Dict[str, np.ndarray], raio_base: float, titulo: str):
    """
    Gera o gráfico polar do perfil do came e retorna a figura matplotlib.
    """
    if resultados is None:
        return None
    
    theta_rad = np.deg2rad(resultados['theta'])
    deslocamento = resultados['s']
    raio_perfil = raio_base + deslocamento
    
    # Usando a classe Figure (Thread-safe)
    fig = Figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection='polar')
    
    ax.plot(theta_rad, raio_perfil, label='Perfil do Came', color='black', linewidth=2)
    ax.plot(theta_rad, np.full_like(theta_rad, raio_base), label='Raio base (Rb)', color='gray', linestyle='--', linewidth=1.5)
    ax.set_title(titulo, fontsize=16, pad=20, fontweight='bold')
    ax.set_rlabel_position(90)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')
    
    return fig

@st.cache_data(show_spinner=False)
# o codido original gerar_animacao_gif está sakvo no notion 
def gerar_animacao_gif(resultados: Dict[str, np.ndarray], raio_base: float, raio_rolete: float, lei_movimento: str, filename: str = "animacao_came.gif"):
    if resultados is None:
        return None
    
    theta_deg = resultados['theta']
    theta_rad = np.deg2rad(theta_deg)
    deslocamento = resultados['s']
    
    angulo_base_corrigido = theta_rad + np.pi / 2
    
    raio_fisico = raio_base + deslocamento
    perfil_x_static = raio_fisico * np.cos(angulo_base_corrigido)
    perfil_y_static = raio_fisico * np.sin(angulo_base_corrigido)
    
    raio_pitch = raio_base + raio_rolete + deslocamento
    pitch_x_static = raio_pitch * np.cos(angulo_base_corrigido)
    pitch_y_static = raio_pitch * np.sin(angulo_base_corrigido)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.set_aspect('equal')
    limite_max = np.max(raio_pitch) + raio_rolete * 1.5
    ax.set_xlim(-limite_max, limite_max)
    ax.set_ylim(-limite_max, limite_max)
    ax.grid(True, alpha=0.3)
    
    perfil_came_plot, = ax.plot([], [], 'b-', linewidth=2, label='Perfil do Came')
    pitch_curve_plot, = ax.plot([], [], 'r--', linewidth=1, label='Curva primitiva')
    rolete = Circle((0, 0), raio_rolete, facecolor='green', edgecolor='black', label='Seguidor', alpha=0.7)
    ax.add_patch(rolete)
    ponto_central, = ax.plot(0, 0, 'k+', markersize=10)
    texto_angulo = ax.text(0.05, 0.95, '', transform=ax.transAxes, verticalalignment='top', fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.legend(loc='upper right')
    
    def init():
        perfil_came_plot.set_data([], [])
        pitch_curve_plot.set_data([], [])
        rolete.center = (0, raio_base + raio_rolete)
        texto_angulo.set_text('')
        return perfil_came_plot, pitch_curve_plot, rolete, texto_angulo
    
    def update(frame):
        angulo_rotacao = -theta_rad[frame]
        matriz_rotacao = np.array([[np.cos(angulo_rotacao), -np.sin(angulo_rotacao)],
                                   [np.sin(angulo_rotacao), np.cos(angulo_rotacao)]])
        
        pontos_fisico = np.vstack((perfil_x_static, perfil_y_static))
        pontos_rot_fisico = matriz_rotacao @ pontos_fisico
        perfil_came_plot.set_data(pontos_rot_fisico[0, :], pontos_rot_fisico[1, :])
        
        pontos_pitch = np.vstack((pitch_x_static, pitch_y_static))
        pontos_rot_pitch = matriz_rotacao @ pontos_pitch
        pitch_curve_plot.set_data(pontos_rot_pitch[0, :], pontos_rot_pitch[1, :])
        
        posicao_y_rolete = raio_base + raio_rolete + deslocamento[frame]
        rolete.center = (0, posicao_y_rolete)
        
        texto_angulo.set_text(f'Ângulo: {theta_deg[frame]:.1f}°')
        
        return perfil_came_plot, pitch_curve_plot, rolete, texto_angulo
    
    frames_indices = np.linspace(0, len(theta_deg) - 1, 180, dtype=int)
    
    ani = animation.FuncAnimation(fig, update, frames=frames_indices,
                                  init_func=init, blit=True, interval=50)
    
    # Cria um caminho temporário seguro que o sistema operacional gerencia
    with tempfile.NamedTemporaryFile(suffix=".gif", delete=False) as tmpfile:
        caminho_temporario = tmpfile.name
    
    try:
        # 1. Matplotlib salva no disco temporário (satisfazendo a exigência da biblioteca)
        ani.save(caminho_temporario, writer='pillow', fps=20, dpi=80)
        plt.close(fig)
        
        # 2. Lemos os bytes do arquivo físico direto para a memória RAM
        with open(caminho_temporario, "rb") as f:
            gif_bytes = f.read()
            
    finally:
        # 3. Deletamos o arquivo físico IMEDIATAMENTE após a leitura (Garantindo Zero Vazamento)
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)
    
    # Retornamos apenas os bytes puros em memória para o Streamlit renderizar
    return gif_bytes

def gerar_relatorio_pdf(
    segmentos: List[estruturas.SegmentoCame],
    tipo_analise: str,
    rpm: float,
    raio_base: float,
    raio_rolete: float,
    leis_movimento: List[str],
    resultados_por_lei: Dict[str, Dict[str, np.ndarray]],
):
    """
    Gera um relatório PDF completo com todos os resultados da análise.
    """
    buffer_pdf = io.BytesIO()
    pdf_pages = PdfPages(buffer_pdf)
    
    # Tradução da variável interna para o termo da literatura
    nome_analise_pdf = "Em função do tempo" if tipo_analise == 'cinematico' else "Em função do ângulo"
    
    # Página de rosto
    texto_rosto = f"RELATÓRIO DE ANÁLISE DE CAME\nGerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n"
    texto_rosto += "--- PARÂMETROS GLOBAIS ---\n"
    texto_rosto += f"Tipo de Análise: {nome_analise_pdf}\n" # <-- Correção aplicada aqui
    
    if tipo_analise == 'cinematico':
        texto_rosto += f"RPM: {rpm}\n"
    texto_rosto += f"Raio Base: {raio_base} mm\n"
    texto_rosto += f"Raio do Rolete: {raio_rolete} mm\n\n"
    texto_rosto += "--- GEOMETRIA DOS TRECHOS ---\n"
    for i, seg in enumerate(segmentos):
        texto_rosto += f"Trecho {i+1}: {seg.tipo} de {seg.theta_inicio}° a {seg.theta_fim}° | H={seg.H} mm | S_inicio={seg.S_inicio} mm\n"
    _salvar_texto_em_pdf(pdf_pages, texto_rosto, "Dados de Entrada")
    
    # Para cada lei de movimento
    for lei in leis_movimento:
        resultados = resultados_por_lei[lei]
        
        # Tabela de resultados
        if tipo_analise == 'cinematico':
            titulo_tabela = f"Tabela de resultados para Método: {lei.upper()} a {rpm:.1f} RPM"
            header_v, header_a, header_j = "Veloc. (mm/s)", "Acel. (mm/s²)", "Jerk (mm/s³)"
        else:
            titulo_tabela = f"Tabela de resultados em função do ângulo para Método: {lei.upper()}"
            header_v, header_a, header_j = "S' (mm/rad)", "S'' (mm/rad²)", "S''' (mm/rad³)"
        
        texto_tabela = f"{'Ângulo (°)':<12} {'Desloc. (mm)':<19} {header_v:<20} {header_a:<22} {header_j:<18}\n"
        texto_tabela += "-" * 90 + "\n"
        angulos_interesse = sorted(list(set([seg.theta_inicio for seg in segmentos] + [segmentos[-1].theta_fim])))
        theta_total, s_total, v_total, a_total, j_total = resultados['theta'], resultados['s'], resultados['v'], resultados['a'], resultados['j']
        for angulo in angulos_interesse:
            idx = np.argmin(np.abs(theta_total - angulo))
            s_val, v_val, a_val, j_val = s_total[idx], v_total[idx], a_total[idx], j_total[idx]
            texto_tabela += f"{angulo:<12.2f} {s_val:<19.2f} {v_val:<20.2f} {a_val:<22.2f} {j_val:<18.2f}\n"
        _salvar_texto_em_pdf(pdf_pages, texto_tabela, titulo_tabela)
        
        # Gráficos SVAJ (Usando a versão exclusiva e estática para o PDF)
        fig_svaj = plotar_svaj_pdf(resultados, lei, tipo_analise, segmentos)
        if fig_svaj:
            pdf_pages.savefig(fig_svaj)
            
    # Perfil do came (usando a última lei de movimento)
    ultima_lei = leis_movimento[-1]
    fig_perfil = plotar_perfil_came_web(resultados_por_lei[ultima_lei], raio_base, "Perfil Geométrico do Came")
    if fig_perfil:
        pdf_pages.savefig(fig_perfil)
    
    pdf_pages.close()
    buffer_pdf.seek(0)
    
    return buffer_pdf
    