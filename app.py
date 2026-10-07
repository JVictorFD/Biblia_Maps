import streamlit as st
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components # Substituímos o streamlit_folium pelo nativo
import json
import os

st.set_page_config(
    page_title="Bíblia Maps",
    page_icon="🌍",
    layout="wide"
)

# Injeção de CSS para o modo ecrã inteiro e o filtro Sépia/Papiro no mapa
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        /* Aplica o efeito de papel antigo e aumenta o contraste sobre o mapa */
        iframe {
            filter: sepia(0.65) hue-rotate(-15deg) contrast(1.15) brightness(0.95);
            border-radius: 8px;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretorio_atual, "dados", "eventos_biblicos.json")
    
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"Ficheiro não encontrado: {caminho_arquivo}")
        return []

eventos = carregar_dados()

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
    if st.button("🚶‍♂️ Modo Andarilho", use_container_width=True, type="primary"):
        st.success("O Modo Andarilho (Visão em 1ª pessoa) será ativado em breve. Fique atento às próximas atualizações!")
    
    st.markdown("---")
    st.caption("v1.2.3 - Native Render & Cloud Ready")

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

# Nova renderização blindada a falhas na nuvem (HTML Nativo ao invés de componente externo)
components.html(mapa_biblico._repr_html_(), height=750)