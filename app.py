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

# Injeção de CSS Base (Layout, Tela Cheia, Bordas e Legendas Flutuantes)
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        
        /* Arredondamento da borda aplicado a qualquer iframe renderizado */
        iframe {
            border-radius: 8px;
        }
        
        .andarilho-container {
            position: relative;
            width: 100%;
            height: 80vh;
            background-color: #0d1117;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 16px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .andarilho-container img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            position: absolute;
            top: 0;
            left: 0;
            opacity: 0.85; 
        }
        
        .creditos-legenda {
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 85%;
            max-width: 900px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 10px;
            padding: 20px 30px;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            box-shadow: 0 4px 20px rgba(0,0,0,0.7);
            z-index: 10;
        }
        
        .creditos-legenda h2 {
            margin: 0 0 8px 0;
            font-size: 22px;
            color: #fbbf24;
            border-bottom: 1px solid rgba(251, 191, 36, 0.3);
            padding-bottom: 4px;
        }
        
        .creditos-legenda p.sub {
            margin: 0 0 12px 0;
            font-size: 14px;
            color: #94a3b8;
            font-style: italic;
        }
        
        .creditos-legenda blockquote {
            margin: 8px 0;
            padding-left: 12px;
            border-left: 3px solid #fbbf24;
            color: #e2e8f0;
            font-size: 14px;
        }
        
        .creditos-legenda p.explicacao {
            margin: 8px 0 0 0;
            font-size: 13px;
            color: #cbd5e1;
            line-height: 1.4;
        }
    </style>
""", unsafe_allow_html=True)

# Gerenciamento de Estados na Sessão
if 'modo_andarilho_ativo' not in st.session_state:
    st.session_state.modo_andarilho_ativo = False
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

# Extração dinâmica de listas para os filtros de seleção
testamentos_unicos = ["Todos"] + sorted(list(set(e.get("testamento", "") for e in eventos if e.get("testamento"))))
epocas_unicas = ["Todas"] + sorted(list(set(e.get("epoca", "") for e in eventos if e.get("epoca"))))

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
    
    st.header("Aparência")
    tema_sepia = st.toggle("Ativar Tema Pergaminho (Sépia)", value=True)
    
    st.markdown("---")
    
    st.header("Pesquisa Avançada")
    termo_busca = st.text_input(
        "Buscar nomes, capítulos ou combine com '+':",
        placeholder="Ex: João, Lucas 2, Pedro+Jesus"
    )
    
    st.markdown("---")
    
    st.header("Filtros Categóricos")
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
    st.caption("v1.9.2 - Correção Interna do Filtro Visual")

# --- LÓGICA DE FILTRAGEM MULTICRITÉRIOS ---
eventos_filtrados = []
for e in eventos:
    match_testamento = (filtro_testamento == "Todos" or e.get("testamento") == filtro_testamento)
    match_epoca = (filtro_epoca == "Todas" or e.get("epoca") == filtro_epoca)
    
    match_personagem = True
    if filtro_personagem != "Todos":
        pers_evento = [p.strip() for p in e.get("personagens", "").split(",")]
        match_personagem = (filtro_personagem in pers_evento)
        
    match_busca = True
    if termo_busca:
        termos_solicitados = [t.strip().lower() for t in termo_busca.split('+') if t.strip()]
        if termos_solicitados:
            texto_completo_evento = " ".join([str(v) for v in e.values()]).lower()
            match_busca = all(termo in texto_completo_evento for termo in termos_solicitados)
        
    if match_testamento and match_epoca and match_personagem and match_busca:
        eventos_filtrados.append(e)

if len(eventos_filtrados) == 1:
    st.session_state.coordenadas_foco = eventos_filtrados[0]["coordenadas"]
    st.session_state.zoom_foco = 10
elif filtro_personagem == "Todos" and filtro_testamento == "Todos" and filtro_epoca == "Todas" and not termo_busca:
    st.session_state.coordenadas_foco = [31.7, 35.2]
    st.session_state.zoom_foco = 6

# --- CONTEÚDO PRINCIPAL ---
if not st.session_state.modo_andarilho_ativo:
    if not eventos_filtrados:
        st.warning("Nenhum evento encontrado com os filtros ou termos de pesquisa aplicados.")

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
        
        html_popup = f"""
        <div style="font-family: Arial, sans-serif; width: 260px;">
            <h4 style="margin-bottom: 5px; color: #2C3E50; border-bottom: 1px solid #eee; padding-bottom: 5px;">{evento.get('evento', '')}</h4>
            <p style="margin: 4px 0; font-size: 13px;"><b>Local:</b> {evento.get('subregiao', '')}</p>
            <p style="margin: 4px 0; font-size: 13px;"><b>Envolvidos:</b> {evento.get('personagens', '')}</p>
            <p style="margin: 4px 0; font-size: 13px;"><b>Livro:</b> <i>{evento.get('referencia', '')}</i></p>
            <div style="margin-top: 10px; background-color: #f8f9fa; padding: 5px; border-radius: 4px;">
                <p style="margin: 0; font-size: 11px; color: #7f8c8d;"><b>Geografia Atual:</b> {evento.get('local_atual', '')}</p>
            </div>
        </div>
        """
        
        folium.Marker(
            location=coord,
            popup=folium.Popup(html_popup, max_width=300),
            tooltip=evento.get('evento', 'Local'),
            icon=folium.Icon(color=cor_marcador, icon=evento.get('icone', 'info-sign'))
        ).add_to(cluster_eventos)

    # Extrai o HTML puro do Folium
    html_mapa = mapa_biblico._repr_html_()
    
    # Injeta o CSS diretamente DENTRO do iframe do mapa se o tema Sépia estiver ligado
    if tema_sepia:
        estilo_interno = "<style> html { filter: sepia(0.65) hue-rotate(-15deg) contrast(1.15) brightness(0.95); } </style>"
        html_mapa = estilo_interno + html_mapa

    components.html(html_mapa, height=750)

else:
    if not eventos_filtrados:
        st.warning("Nenhum evento corresponde à busca atual. Limpe a barra de pesquisa para retornar ao modo andarilho padrão.")
        html_modo_andarilho = f"""
        <div class="andarilho-container">
            <div class="creditos-legenda" style="text-align: center;">
                <h2>📍 Local não encontrado</h2>
                <p class="explicacao">Ajuste os filtros ou a busca lateral para explorar os cenários bíblicos.</p>
            </div>
        </div>
        """
        components.html(html_modo_andarilho, height=750)
    else:
        evento_ativo = eventos_filtrados[0]
        
        nome_evento = evento_ativo.get("evento", "Cena Bíblica")
        subregiao = evento_ativo.get("subregiao", "")
        arquivo_img = evento_ativo.get("imagem_cena", "")
        texto_versiculo = evento_ativo.get("versiculo", "Texto bíblico indisponível no momento.")
        texto_explicacao = evento_ativo.get("explicacao", "Contextualização histórica em desenvolvimento para este local.")
        
        diretorio_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_imagem = os.path.join(diretorio_atual, "dados", arquivo_img) if arquivo_img else ""
        
        tem_imagem = caminho_imagem and os.path.exists(caminho_imagem)
        
        tag_imagem = ""
        if tem_imagem:
            import base64
            with open(caminho_imagem, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            tag_imagem = f'<img src="data:image/jpeg;base64,{img_base64}" alt="{nome_evento}">'

        html_modo_andarilho = f"""
        <div class="andarilho-container">
            {tag_imagem}
            <div class="creditos-legenda">
                <h2>📍 {nome_evento}</h2>
                <p class="sub"><b>Região:</b> {subregiao}</p>
                <blockquote>{texto_versiculo}</blockquote>
                <p class="explicacao">{texto_explicacao}</p>
            </div>
        </div>
        """
        components.html(html_modo_andarilho, height=750)