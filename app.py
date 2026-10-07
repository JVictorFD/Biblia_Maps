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

# Injeção de CSS para ecrã inteiro e estilo papiro
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        iframe[title="folium_map"] {
            filter: sepia(0.65) hue-rotate(-15deg) contrast(1.15) brightness(0.95);
            border-radius: 8px;
        }
        img {
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
    </style>
""", unsafe_allow_html=True)

# Gerenciamento de Estados na Sessão
if 'modo_andarilho_ativo' not in st.session_state:
    st.session_state.modo_andarilho_ativo = False
if 'cena_selecionada' not in st.session_state:
    st.session_state.cena_selecionada = "Jesus_nascimento.jpg"
if 'coordenadas_foco' not in st.session_state:
    st.session_state.coordenadas_foco = [31.7, 35.2]
if 'zoom_foco' not in st.session_state:
    st.session_state.zoom_foco = 6

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

# Extração dinâmica de listas para os filtros avançados
testamentos_unicos = ["Todos"] + sorted(list(set(e.get("testamento", "") for e in eventos if e.get("testamento"))))
epocas_unicas = ["Todas"] + sorted(list(set(e.get("epoca", "") for e in eventos if e.get("epoca"))))

# Extrai e limpa lista de personagens individuais
personagens_brutos = []
for e in eventos:
    if "personagens" in e:
        p_lista = [p.strip() for p in e["personagens"].split(",")]
        personagens_brutos.extend(p_lista)
personagens_unicos = ["Todos"] + sorted(list(set(personagens_brutos)))

# --- BARRA LATERAL (FILTROS E NAVEGAÇÃO) ---
with st.sidebar:
    st.title("📜 Bíblia Maps")
    st.write("Explore os eventos históricos da Bíblia de forma interativa.")
    
    st.header("Filtros Avançados")
    filtro_testamento = st.selectbox("Período (Testamento):", testamentos_unicos)
    filtro_epoca = st.selectbox("Época / Fase:", epocas_unicas)
    filtro_personagem = st.selectbox("Personagem Específico:", personagens_unicos)
    
    st.markdown("---")
    
    st.subheader("Modo Imersivo")
    if not st.session_state.modo_andarilho_ativo:
        if st.button("🚶‍♂️ Ativar Modo Andarilho (Cena)", use_container_width=True, type="primary"):
            st.session_state.modo_andarilho_ativo = True
            st.rerun()
    else:
        if st.button("🌍 Voltar ao Mapa Global", use_container_width=True):
            st.session_state.modo_andarilho_ativo = False
            st.rerun()
            
    st.markdown("---")
    st.caption("v1.5.0 - Multi-Filtros & Modo Andarilho Dinâmico")

# --- LÓGICA DE FILTRAGEM ---
eventos_filtrados = []
for e in eventos:
    match_testamento = (filtro_testamento == "Todos" or e.get("testamento") == filtro_testamento)
    match_epoca = (filtro_epoca == "Todas" or e.get("epoca") == filtro_epoca)
    
    match_personagem = True
    if filtro_personagem != "Todos":
        pers_evento = [p.strip() for p in e.get("personagens", "").split(",")]
        match_personagem = (filtro_personagem in pers_evento)
        
    if match_testamento and match_epoca and match_personagem:
        eventos_filtrados.append(e)

# Redirecionamento automático de foco no mapa ao selecionar um personagem específico
if filtro_personagem != "Todos" and len(eventos_filtrados) == 1:
    st.session_state.coordenadas_foco = eventos_filtrados[0]["coordenadas"]
    st.session_state.zoom_foco = 10
elif filtro_personagem == "Todos" and filtro_testamento == "Todos" and filtro_epoca == "Todas":
    st.session_state.coordenadas_foco = [31.7, 35.2]
    st.session_state.zoom_foco = 6

# --- CONTEÚDO PRINCIPAL ---
if not st.session_state.modo_andarilho_ativo:
    # Renderiza o MAPA GLOBAL
    mapa_biblico = folium.Map(
        location=st.session_state.coordenadas_foco, 
        zoom_start=st.session_state.zoom_foco, 
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    )

    cluster_eventos = MarkerCluster().add_to(mapa_biblico)

    for evento in eventos_filtrados:
        coord = evento["coordenadas"]
        cor_marcador = "darkred" if evento.get("testamento") == "Antigo Testamento" else "cadetblue"
        
        # Atualiza a cena na sessão caso o usuário queira transicionar direto
        img_cena = evento.get("imagem_cena", "Jesus_nascimento.jpg")
        
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

    components.html(mapa_biblico._repr_html_().replace("<iframe ", "<iframe title='folium_map' "), height=750)

else:
    # Renderiza o MODO ANDARILHO 2D (Janela Imersiva Dinâmica)
    st.subheader("🚶‍♂️ Modo Andarilho: Cena Histórica Imersiva")
    
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    # Se houver eventos filtrados, pega a imagem do primeiro evento correspondente; caso contrário, usa o padrão
    imagem_alvo = "Jesus_nascimento.jpg"
    if eventos_filtrados:
        imagem_alvo = eventos_filtrados[0].get("imagem_cena", "Jesus_nascimento.jpg")
        
    caminho_imagem = os.path.join(diretorio_atual, "dados", imagem_alvo)
    if not os.path.exists(caminho_imagem):
        caminho_imagem = os.path.join(diretorio_atual, "dados", "Jesus_nascimento.jpg")
    
    try:
        st.image(caminho_imagem, use_container_width=True)
        
        st.markdown("""
        ---
        ### Experiência Imersiva no Local Bíblico
        
        > *"Lâmpada para os meus pés é a tua palavra, e luz para o meu caminho."* — **Salmos 119:105**
        
        A contemplação deste cenário transporta-o diretamente para o contexto da época. Utilize os filtros na barra lateral para alternar entre épocas, acontecimentos ou personagens e explorar novas janelas históricas.
        """)
    except Exception as e:
        st.error(f"Erro ao carregar a cena imersiva: {e}")