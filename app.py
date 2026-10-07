import streamlit as st
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components
import json
import os

st.set_page_config(
    page_title="Bíblia Maps",
    page_icon="🌍",
    layout="wide"
)

# Injeção de CSS para o mapa, a tela cheia e cantos arredondados da imagem imersiva
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        /* Efeito de papiro antigo aplicado apenas ao mapa */
        iframe[title="folium_map"] {
            filter: sepia(0.65) hue-rotate(-15deg) contrast(1.15) brightness(0.95);
            border-radius: 8px;
        }
        /* Estilização da imagem imersiva 2D */
        img {
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
    </style>
""", unsafe_allow_html=True)

# Lógica de estados da página (Mapa vs. Imersivo)
if 'modo_andarilho_ativo' not in st.session_state:
    st.session_state.modo_andarilho_ativo = False

@st.cache_data
def carregar_dados():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, "dados", "eventos_biblicos.json")
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return []

eventos = carregar_dados()

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📜 Bíblia Maps")
    st.write("Explore os eventos históricos da Bíblia de forma interativa.")
    
    st.header("Filtros")
    filtro_testamento = st.selectbox(
        "Selecione o Período Histórico:",
        ["Todos", "Antigo Testamento", "Novo Testamento"]
    )
    
    st.markdown("---")
    
    st.subheader("Modo Imersivo")
    if not st.session_state.modo_andarilho_ativo:
        # Botão para ativar a janela imersiva temporária
        if st.button("🚶‍♂️ Ativar Modo Andarilho (Jesus)", use_container_width=True, type="primary"):
            st.session_state.modo_andarilho_ativo = True
            st.rerun()
    else:
        # Botão para voltar
        if st.button("🌍 Voltar ao Mapa Global", use_container_width=True):
            st.session_state.modo_andarilho_ativo = False
            st.rerun()
            
    st.markdown("---")
    st.caption("v1.4.0 - Janela Imersiva 2D")

# --- CONTEÚDO PRINCIPAL ---
if not st.session_state.modo_andarilho_ativo:
    # Renderiza o MAPA GLOBAL
    eventos_filtrados = eventos
    if filtro_testamento != "Todos":
        eventos_filtrados = [e for e in eventos if e["testamento"] == filtro_testamento]

    mapa_biblico = folium.Map(
        location=[31.7, 35.2], 
        zoom_start=6, 
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    )

    cluster_eventos = MarkerCluster().add_to(mapa_biblico)

    for evento in eventos_filtrados:
        coord = evento["coordenadas"]
        cor_marcador = "darkred" if evento["testamento"] == "Antigo Testamento" else "cadetblue"
        
        html_popup = f"""
        <div style="font-family: Arial, sans-serif; width: 260px;">
            <h4 style="margin-bottom: 5px; color: #2C3E50; border-bottom: 1px solid #eee; padding-bottom: 5px;">{evento['evento']}</h4>
            <p style="margin: 4px 0; font-size: 13px;"><b>Local:</b> {evento['subregiao']}</p>
            <p style="margin: 4px 0; font-size: 13px;"><b>Envolvidos:</b> {evento['personagens']}</p>
            <p style="margin: 4px 0; font-size: 13px;"><b>Livro:</b> <i>{evento['referencia']}</i></p>
            <div style="margin-top: 10px; background-color: #f8f9fa; padding: 5px; border-radius: 4px;">
                <p style="margin: 0; font-size: 11px; color: #7f8c8d;"><b>Geografia Atual:</b> {evento['local_atual']}</p>
            </div>
        </div>
        """
        
        folium.Marker(
            location=coord,
            popup=folium.Popup(html_popup, max_width=300),
            tooltip=evento['evento'],
            icon=folium.Icon(color=cor_marcador, icon=evento.get('icone', 'info-sign'))
        ).add_to(cluster_eventos)

    # html nativo
    components.html(mapa_biblico._repr_html_().replace("<iframe ", "<iframe title='folium_map' "), height=750)

else:
    # Renderiza o MODO ANDARILHO 2D (Visão Imersiva)
    st.subheader("🚶‍♂️ Modo Andarilho: O Nascimento de Jesus")
    
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Busca pela imagem nomeada por você, seja .jpg ou .png
    caminho_imagem = os.path.join(diretorio_atual, "dados", "Jesus_nascimento.jpg")
    if not os.path.exists(caminho_imagem):
        caminho_imagem = os.path.join(diretorio_atual, "dados", "Jesus_nascimento.png")
    
    try:
        # Exibe a imagem ocupando a largura da tela
        st.image(caminho_imagem, use_container_width=True)
        
        # Texto narrativo imersivo
        st.markdown("""
        ---
        ### A Manjedoura em Belém, Século I
        
        > *"E deu à luz a seu filho primogênito, e envolveu-o em panos, e deitou-o numa manjedoura, porque não havia lugar para eles na estalagem."* — **Lucas 2:7**
        
        A noite está fria na pequena cidade da Judeia. O silêncio só é quebrado pelo som suave dos animais e pelo vento que sopra nas colinas. Diante de você, sob a luz trêmula e quente de uma lamparina a óleo, o evento que dividirá a história da humanidade acaba de acontecer. A simplicidade de uma gruta de pedra contrasta com a grandeza do momento.
        """)
        
    except Exception as e:
        st.error(f"Erro ao carregar imagem: Verifique se o arquivo 'Jesus_nascimento' está dentro da pasta 'dados'.")