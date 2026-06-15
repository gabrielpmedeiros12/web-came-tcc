# =============================================================
# MÓDULO: app.py (APLICAÇÃO WEB STREAMLIT v2.0)
# =============================================================
# RESPONSABILIDADE:
# - Criar uma interface web interativa para análise de came-seguidor
# - Coletar e validar dados do usuário através de widgets gráficos
# - Exibir resultados, gráficos e animações na página web
# - Gerar relatórios PDF completos
# =============================================================

import streamlit as st
import numpy as np
import sys
import os
# sys.path.append('/home/ubuntu/upload')

import estruturas
import motor_calculo
import config
import visualizacao_web

# Configuração da página
st.set_page_config(
    page_title="WEB CAME",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS customizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #667eea;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.75rem;
        border: none;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #764ba2;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("""
<div class="main-header">
    <h1>WEB CAME 🦉</h1>
    <p>Gabriel Pereira Medeiros - Universidade Federal do Oeste da Bahia</p>
</div>
""", unsafe_allow_html=True)

# Sidebar para parâmetros globais
st.sidebar.header("Parâmetros")

# Tipo de análise
tipo_analise = st.sidebar.selectbox(
    "Tipo de Análise",
    options=["cinematico", "geometrico"],
    format_func=lambda x: "Em função de tempo (mm/s)" if x == "cinematico" else "Em função de ângulo (mm/rad)",
    help="Escolha entre análise com RPM ou sem RPM"
)

# RPM (apenas para análise cinemática)
rpm = config.RPM_PADRAO
if tipo_analise == "cinematico":
    rpm = st.sidebar.slider(
        "RPM de Operação",
        min_value=0.0,
        max_value=3000.0,
        value=config.RPM_PADRAO,
        step=10.0,
        help="Rotações por minuto do came"
    )

# Raio base
raio_base = st.sidebar.slider(
    "Raio Base (Rb) [mm]",
    min_value=10.0,
    max_value=200.0,
    value=config.RAIO_BASE_PADRAO,
    step=5.0,
    help="Raio base do came em milímetros"
)

# Raio do rolete
raio_rolete = st.sidebar.slider(
    "Raio do Rolete Seguidor [mm]",
    min_value=1.0,
    max_value=50.0,
    value=10.0,
    step=1.0,
    help="Raio do rolete seguidor em milímetros"
)

st.sidebar.markdown("---")

# Seleção das leis de movimento
st.sidebar.header("Leis de Movimento")
leis_selecionadas = st.sidebar.multiselect(
    "Escolha as Leis de Movimento para Análise",
    options=["mhs", "cicloidal", "polinomial_345"],
    default=["mhs", "cicloidal", "polinomial_345"],
    format_func=lambda x: {
        "mhs": "Movimento Harmônico Simples (MHS)",
        "cicloidal": "Cicloidal",
        "polinomial_345": "Polinomial 3-4-5"
    }[x],
    help="Selecione uma ou mais leis de movimento para comparação"
)

st.sidebar.markdown("---")
st.sidebar.info("**Dica:** Ajuste os parâmetros e defina os trechos abaixo para visualizar os resultados.")

# Seção principal: Definição dos trechos
st.header("Definição dos Trechos do Came")

# Número de trechos
num_trechos = st.number_input(
    "Quantos trechos o came possui?",
    min_value=1,
    max_value=10,
    value=3,
    step=1,
    help="Número de segmentos (trechos) que compõem o perfil do came"
)

# Criar colunas para os trechos
st.markdown("### Configuração dos Trechos")

lista_segmentos = []
angulo_final_anterior = 0.0
posicao_final_anterior = 0.0

for i in range(num_trechos):
    with st.expander(f"**Trecho {i+1}**", expanded=(i == 0)):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tipo = st.selectbox(
                "Tipo do Trecho",
                options=["subida", "descida", "parada"],
                key=f"tipo_{i}",
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            # Cria uma chave dinâmica amarrada ao valor do ângulo.
            # Se o ângulo mudar, a chave muda, forçando o Streamlit a atualizar o visual.
            chave_dinamica = f"theta_i_{i}_{angulo_final_anterior}"
            
            st.text_input(
                "Ângulo de Início [°]",
                value=f"{angulo_final_anterior:.1f}",
                disabled=True,
                key=chave_dinamica
            )
        
        with col3:
            # 1. Verifica se o came já completou a volta (360°)
            limite_atingido = angulo_final_anterior >= 360.0
            
            # 2. Garante que o valor mínimo nunca seja maior que 360
            min_val_seguro = min(angulo_final_anterior + 1.0, 360.0)
            
            # 3. Renderiza o input de forma segura
            theta_f = st.number_input(
                "Ângulo de Fim [°]",
                min_value=360.0 if limite_atingido else min_val_seguro,
                max_value=360.0,
                value=360.0 if limite_atingido else min(angulo_final_anterior + 120.0, 360.0),
                step=1.0,
                disabled=limite_atingido, # Trava a edição se já completou os 360°
                key=f"theta_f_{i}"
            )
        
        # Elevação/Descida
        H_atual = 0.0
        if tipo == "subida":
            H_atual = st.number_input(
                "Elevação (H) [mm]",
                min_value=0.1,
                max_value=200.0,
                value=50.0,
                step=1.0,
                key=f"H_{i}",
                help="Valor positivo para elevação"
            )
            posicao_final = posicao_final_anterior + H_atual
        elif tipo == "descida":
            H_atual = st.number_input(
                "Descida (H) [mm]",
                min_value=0.1,
                max_value=200.0,
                value=50.0,
                step=1.0,
                key=f"H_{i}",
                help="Valor positivo representando a magnitude da descida"
            )
            posicao_final = posicao_final_anterior - H_atual
        else:  # parada
            st.info(f"Posição de parada: {posicao_final_anterior:.2f} mm")
            posicao_final = posicao_final_anterior
        
        # Criar segmento APENAS se houver variação angular real (evita divisão por zero)
        if theta_f > angulo_final_anterior:
            segmento = estruturas.SegmentoCame(
                tipo=tipo,
                theta_inicio=angulo_final_anterior,
                theta_fim=theta_f,
                S_inicio=posicao_final_anterior,
                H=H_atual
            )
            lista_segmentos.append(segmento)
        
        # Atualizar para o próximo trecho
        angulo_final_anterior = theta_f
        posicao_final_anterior = posicao_final

st.markdown("---")

# Validação dos dados
st.subheader("Validação dos Dados")
validacao_ok = True
mensagens_validacao = []

# Validar soma dos ângulos
if not np.isclose(angulo_final_anterior, 360.0, atol=0.1):
    validacao_ok = False
    mensagens_validacao.append(
        ("erro", f"Os trechos não somam 360°. Soma atual: {angulo_final_anterior:.2f}°")
    )
else:
    mensagens_validacao.append(
        ("ok", f"Soma dos ângulos: {angulo_final_anterior:.2f}°")
    )

# Validar retorno a zero
if not np.isclose(posicao_final_anterior, 0.0, atol=0.1):
    validacao_ok = False
    mensagens_validacao.append(
        ("erro", f"O deslocamento não retorna a zero. Posição final: {posicao_final_anterior:.2f} mm")
    )
else:
    mensagens_validacao.append(
        ("ok", "O deslocamento retorna a zero")
    )

# Validar seleção de leis de movimento
if len(leis_selecionadas) == 0:
    validacao_ok = False
    mensagens_validacao.append(
        ("erro", "Nenhuma lei de movimento foi selecionada")
    )
else:
    mensagens_validacao.append(
        ("ok", f"Leis de movimento selecionadas: {len(leis_selecionadas)}")
    )

# Exibir mensagens de validação
for tipo, msg in mensagens_validacao:
    if tipo == "erro":
        st.error(msg)
    else:
        st.success(msg)

st.markdown("---")


# --- PROTEÇÃO CONTRA (STALE STATE): watchdog ---

if st.session_state.get('processado', False):
    # Compara os parâmetros atuais da tela com os parâmetros salvos na memória
    mudou_estado = (
        st.session_state.get('raio_base') != raio_base or
        st.session_state.get('raio_rolete') != raio_rolete or
        st.session_state.get('rpm') != rpm or
        st.session_state.get('tipo_analise') != tipo_analise or
        st.session_state.get('leis_selecionadas') != leis_selecionadas or
        st.session_state.get('segmentos') != lista_segmentos
    )
    
    if mudou_estado:
        # Se qualquer coisa mudou, invalidamos os resultados antigos imediatamente
        st.session_state.processado = False
        st.warning("⚠️ Parâmetros alterados! Os resultados anteriores foram ocultados por segurança. Clique em 'Processar Análise' para recalcular.")

# Botão para processar
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    processar_btn = st.button("Processar Análise", type="primary", use_container_width=True, disabled=not validacao_ok)
with col_btn2:
    gerar_pdf_btn = st.button("Gerar Relatório PDF", type="secondary", use_container_width=True, disabled=not validacao_ok)

if processar_btn or gerar_pdf_btn:
    with st.spinner("Processando análise..."):
        try:
            # Processar para cada lei de movimento
            resultados_por_lei = {}
            for lei in leis_selecionadas:
                resultados_svaj = motor_calculo.processar_perfil_completo(
                    segmentos=lista_segmentos,
                    lei_movimento_global=lei,
                    rpm=rpm,
                    tipo_analise=tipo_analise
                )
                resultados_por_lei[lei] = resultados_svaj
            
            # Armazenar resultados no estado da sessão
            st.session_state.resultados_por_lei = resultados_por_lei
            st.session_state.segmentos = lista_segmentos
            st.session_state.leis_selecionadas = leis_selecionadas
            st.session_state.raio_base = raio_base
            st.session_state.raio_rolete = raio_rolete
            st.session_state.rpm = rpm
            st.session_state.tipo_analise = tipo_analise
            st.session_state.processado = True
            
            # Se o botão de PDF foi pressionado, gerar o PDF
            if gerar_pdf_btn:
                with st.spinner("Gerando relatório PDF..."):
                    # Recebemos o buffer em memória, sem precisar inventar nomes aleatórios
                    pdf_buffer = visualizacao_web.gerar_relatorio_pdf(
                        segmentos=lista_segmentos,
                        tipo_analise=tipo_analise,
                        rpm=rpm,
                        raio_base=raio_base,
                        raio_rolete=raio_rolete,
                        leis_movimento=leis_selecionadas,
                        resultados_por_lei=resultados_por_lei
                    )
                    st.session_state.pdf_buffer = pdf_buffer
                    st.success(f"Relatório PDF gerado com sucesso!")
            else:
                st.success("✅ Análise concluída com sucesso!")
                
        except Exception as e:
            st.error(f"Erro ao processar análise: {str(e)}")
            st.session_state.processado = False

# Exibir resultados se já processados
if 'processado' in st.session_state and st.session_state.processado:
    st.markdown("---")
    st.header("Resultados da Análise")
    
    # Download do PDF se disponível
    if 'pdf_buffer' in st.session_state:
        st.download_button(
            label="Baixar Relatório PDF",
            data=st.session_state.pdf_buffer,
            file_name="relatorio_cinematico_came.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    
    st.markdown("### Valores de Pico Absolutos")
    
    # Seletor discreto para escolher a lei do painel
    lei_hud = st.selectbox(
        "Visualizar picos para a lei de movimento:", 
        options=st.session_state.leis_selecionadas,
        format_func=lambda x: x.upper(),
        key="seletor_hud"
    )
    
    # Extração dos dados
    res_hud = st.session_state.resultados_por_lei[lei_hud]
    
    # Cálculo dos máximos absolutos
    s_max = np.max(res_hud['s'])
    v_max = np.max(np.abs(res_hud['v']))
    a_max = np.max(np.abs(res_hud['a']))
    j_max = np.max(np.abs(res_hud['j']))
    
    # Lógica de unidades adaptativa
    is_cinematico = st.session_state.tipo_analise == 'cinematico'
    unidade_v = "mm/s" if is_cinematico else "mm/rad"
    unidade_a = "mm/s²" if is_cinematico else "mm/rad²"
    unidade_j = "mm/s³" if is_cinematico else "mm/rad³"
    
    # Renderização dos Cards (Métricas)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="S_MAX (Deslocamento)", value=f"{s_max:.2f} mm")
    with col2:
        st.metric(label="|V|_MAX (Velocidade)", value=f"{v_max:.2f} {unidade_v}")
    with col3:
        st.metric(label="|A|_MAX (Aceleração)", value=f"{a_max:.2f} {unidade_a}")
    with col4:
        st.metric(label="|J|_MAX (Pulso)", value=f"{j_max:.2f} {unidade_j}")
        
    st.markdown("<br>", unsafe_allow_html=True) # Espaçamento elegante antes das abas
    
    
    # Tabs para organizar os resultados
    tabs = ["Tabelas de Resultados", "Gráficos SVAJ", "Perfil do Came", "Animação"]
    tab_objects = st.tabs(tabs)
    
    with tab_objects[0]:
        st.subheader("Tabelas de Resultados")
        for lei in st.session_state.leis_selecionadas:
            st.markdown(f"### {lei.upper()}")
            df = visualizacao_web.gerar_tabela_resultados(
                st.session_state.resultados_por_lei[lei],
                st.session_state.segmentos,
                lei,
                st.session_state.rpm,
                st.session_state.tipo_analise
            )
            if df is not None:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Nenhum resultado disponível para exibir.")
    
    with tab_objects[1]:
        st.subheader("Diagramas SVAJ")
        for lei in st.session_state.leis_selecionadas:
            st.markdown(f"### {lei.upper()}")
            fig_svaj_plotly = visualizacao_web.plotar_svaj_web(
                st.session_state.resultados_por_lei[lei],
                lei,
                st.session_state.tipo_analise,
                st.session_state.segmentos
            )
            if fig_svaj_plotly is not None:
                # Renderiza o gráfico interativo na tela
                st.plotly_chart(fig_svaj_plotly, use_container_width=True)
            else:
                st.warning("Nenhum gráfico disponível para exibir.")
    
    with tab_objects[2]:
        st.subheader("Perfil do Came")
        # Usar a última lei de movimento para o perfil
        ultima_lei = st.session_state.leis_selecionadas[-1]
        fig_perfil = visualizacao_web.plotar_perfil_came_web(
            st.session_state.resultados_por_lei[ultima_lei],
            st.session_state.raio_base,
            f"Perfil do Came - {ultima_lei.upper()}"
        )
        if fig_perfil is not None:
            col_esq, col_centro, col_dir = st.columns([1, 2, 1])
            with col_centro:
                st.pyplot(fig_perfil, use_container_width=True)
        else:
            st.warning("Nenhum perfil disponível para exibir.")
    
    with tab_objects[3]:
        st.subheader("Animação do Mecanismo Came-Seguidor")
        
        # Seletor de lei de movimento para a animação
        lei_animacao = st.selectbox(
            "Escolha a lei de movimento para a animação:",
            options=st.session_state.leis_selecionadas,
            format_func=lambda x: {
                "mhs": "Movimento Harmônico Simples (MHS)",
                "cicloidal": "Cicloidal",
                "polinomial_345": "Polinomial 3-4-5"
            }[x]
        )
        
        if st.button("Gerar Animação", key="gerar_animacao"):
            with st.spinner("Gerando animação... Isso pode levar alguns segundos."):
                try:
                    # A função agora retorna o buffer em memória diretamente
                    gif_buffer = visualizacao_web.gerar_animacao_gif(
                        st.session_state.resultados_por_lei[lei_animacao],
                        st.session_state.raio_base,
                        st.session_state.raio_rolete,
                        lei_animacao
                        # O parâmetro filename foi removido
                    )
                    
                    if gif_buffer is not None:
                        st.session_state.gif_buffer = gif_buffer
                        st.success("Animação gerada com sucesso!")
                    else:
                        st.error("Erro ao gerar animação.")
                except Exception as e:
                    st.error(f"Erro ao gerar animação: {str(e)}")
        
        # Verifica diretamente se o buffer está na memória da sessão
        if 'gif_buffer' in st.session_state:
            st.image(st.session_state.gif_buffer, caption="Animação do Mecanismo Came-Seguidor", use_container_width=True)
            
            if st.button("⏹️ Parar Animação", key="parar_animacao", use_container_width=True):
                del st.session_state.gif_buffer
                st.rerun() # Função oficial e atualizada do Streamlit
        else:
            st.info("Clique no botão acima para gerar a animação.")

# Rodapé
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem 0;">
    <p><strong>Ferramenta de Análise Cinemática de Cames</strong></p>
    <p>Desenvolvido como Trabalho de Conclusão de Curso para obtenção do
título de Bacharel em Engenharia Mecânica</p>
</div>
""", unsafe_allow_html=True)
