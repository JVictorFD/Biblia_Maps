import streamlit as st
import folium
from folium.plugins import MarkerCluster
import streamlit.components.v1 as components
import json
import os
import sqlite3
import hashlib
from datetime import datetime

st.set_page_config(
    page_title="Bíblia Maps",
    page_icon="🌍",
    layout="wide"
)

# --- INICIALIZAÇÃO DO BANCO DE DADOS (USUÁRIOS E DEVOCIONAL) ---
def inicializar_banco():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_db = os.path.join(diretorio_atual, "biblia_maps_usuarios.db")
    conexao = sqlite3.connect(caminho_db)
    cursor = conexao.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS diario_devocional (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            evento_id TEXT,
            nome_evento TEXT,
            anotacao TEXT,
            data_hora TEXT
        )
    """)
    conexao.commit()
    return conexao

conexao_db = inicializar_banco()

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# Injeção de CSS Base
st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 0rem;
            padding-right: 0rem;
        }
        
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
        
        .itinerario-box {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 8px;
            border-left: 3px solid #e74c3c;
            margin-bottom: 10px;
        }
        
        .diario-box-side {
            background-color: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #f39c12;
            margin-bottom: 10px;
            color: #2c3e50;
        }
        
        /* Estilização para o Modo Leitura do Devocional */
        .leitura-devocional-card {
            background-color: #fdfbf7;
            padding: 25px;
            border-radius: 10px;
            border-left: 6px solid #d35400;
            margin-bottom: 20px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        }
        .leitura-devocional-card h3 {
            color: #2C3E50;
            margin-top: 0;
            margin-bottom: 5px;
            font-family: 'Georgia', serif;
        }
        .leitura-devocional-card p.data {
            color: #7f8c8d;
            font-size: 13px;
            margin-top: 0;
            margin-bottom: 15px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        .leitura-devocional-card p.texto {
            font-size: 16px;
            color: #333;
            line-height: 1.7;
            white-space: pre-wrap;
        }
    </style>
""", unsafe_allow_html=True)

# Gerenciamento de Estados na Sessão
if 'modo_andarilho_ativo' not in st.session_state:
    st.session_state.modo_andarilho_ativo = False
if 'modo_leitura_diario' not in st.session_state:
    st.session_state.modo_leitura_diario = False
if 'coordenadas_foco' not in st.session_state:
    st.session_state.coordenadas_foco = [31.7, 35.2]
if 'zoom_foco' not in st.session_state:
    st.session_state.zoom_foco = 6
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'termo_pesquisa_rapida' not in st.session_state:
    st.session_state.termo_pesquisa_rapida = ""

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

testamentos_unicos = ["Todos"] + sorted(list(set(e.get("testamento", "") for e in eventos if e.get("testamento"))))
epocas_unicas = ["Todas"] + sorted(list(set(e.get("epoca", "") for e in eventos if e.get("epoca"))))

personagens_brutos = []
for e in eventos:
    if "personagens" in e:
        p_lista = [p.strip() for p in e["personagens"].split(",")]
        personagens_brutos.extend(p_lista)
personagens_unicos = ["Todos"] + sorted(list(set(personagens_brutos)))

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("📜 Bíblia Maps")
    st.write("Explore geograficamente os eventos históricos.")
    
    st.markdown("---")
    if not st.session_state.logged_in:
        st.subheader("🔐 Acesso ao Devocional Guiado")
        tab_login, tab_cad = st.tabs(["Entrar", "Criar Conta"])
        
        with tab_login:
            user_login = st.text_input("Usuário", key="login_user")
            pass_login = st.text_input("Senha", type="password", key="login_pass")
            if st.button("Acessar", use_container_width=True):
                if user_login and pass_login:
                    cursor = conexao_db.cursor()
                    cursor.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (user_login, hash_senha(pass_login)))
                    if cursor.fetchone():
                        st.session_state.logged_in = True
                        st.session_state.username = user_login
                        st.success("Acesso liberado!")
                        st.rerun()
                    else:
                        st.error("Credenciais incorretas.")
                        
        with tab_cad:
            user_cad = st.text_input("Novo Usuário", key="cad_user")
            pass_cad = st.text_input("Nova Senha", type="password", key="cad_pass")
            if st.button("Cadastrar", use_container_width=True):
                if user_cad and pass_cad:
                    cursor = conexao_db.cursor()
                    try:
                        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", (user_cad, hash_senha(pass_cad)))
                        conexao_db.commit()
                        st.success("Conta criada! Você já pode entrar.")
                    except sqlite3.IntegrityError:
                        st.error("Nome de usuário já existe.")
    else:
        st.subheader(f"📖 Devocional de {st.session_state.username}")
        
        # Botão Principal para abrir o modo de leitura de tela cheia
        if st.button("📖 Abrir Caderno de Reflexões", use_container_width=True, type="primary"):
            st.session_state.modo_leitura_diario = True
            st.session_state.modo_andarilho_ativo = False
            st.rerun()
            
        if st.button("Sair (Logout)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.termo_pesquisa_rapida = ""
            st.session_state.modo_leitura_diario = False
            st.rerun()
            
        cursor = conexao_db.cursor()
        cursor.execute("SELECT id, evento_id, nome_evento, anotacao, data_hora FROM diario_devocional WHERE username=? ORDER BY id DESC", (st.session_state.username,))
        registros_diario = cursor.fetchall()
        
        if registros_diario:
            with st.expander("⭐ Últimos Favoritos Salvos", expanded=False):
                for reg in registros_diario[:3]: # Mostra apenas os 3 mais recentes na barra lateral
                    st.markdown(f"""
                    <div class="diario-box-side">
                        <b>📍 {reg[2]}</b><br>
                        <i><small>{reg[4]}</small></i>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"🗺️ Ir para: {reg[2]}", key=f"side_btn_{reg[0]}"):
                        st.session_state.termo_pesquisa_rapida = reg[2]
                        st.session_state.modo_leitura_diario = False
                        st.rerun()
        else:
            st.info("Seu Devocional Guiado está vazio. Escolha um local no mapa e salve suas reflexões!")

    st.markdown("---")
    st.header("Aparência")
    tema_sepia = st.toggle("Ativar Tema Pergaminho (Sépia)", value=True)
    tema_delineado = st.toggle("Ativar Delineado do Mapa Atual", value=False)
    
    st.markdown("---")
    st.header("Pesquisa Avançada")
    valor_busca = st.session_state.termo_pesquisa_rapida if st.session_state.termo_pesquisa_rapida else ""
    termo_busca = st.text_input(
        "Buscar nomes, capítulos ou combine com '+':",
        value=valor_busca,
        placeholder="Ex: João, Lucas 2, Pedro+Jesus"
    )
    if st.session_state.termo_pesquisa_rapida and termo_busca != st.session_state.termo_pesquisa_rapida:
        st.session_state.termo_pesquisa_rapida = "" 
    
    st.markdown("---")
    st.header("Filtros Categóricos")
    filtro_testamento = st.selectbox("Período (Testamento):", testamentos_unicos)
    filtro_epoca = st.selectbox("Época / Fase:", epocas_unicas)
    filtro_personagem = st.selectbox("Personagem Específico:", personagens_unicos)

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

# --- BARRA LATERAL (AÇÃO E ITINERÁRIO) ---
seguir_caminhada = False
with st.sidebar:
    if filtro_personagem != "Todos" and len(eventos_filtrados) > 1:
        st.markdown("---")
        st.subheader("🗺️ Rota Histórica")
        
        seguir_caminhada = st.toggle(f"🚶‍♂️ Seguir caminhada de {filtro_personagem}", value=False)
        
        if seguir_caminhada:
            st.info(f"Itinerário mapeado ({len(eventos_filtrados)} locais):")
            for i, ev in enumerate(eventos_filtrados):
                st.markdown(f"<div class='itinerario-box'><b>{i+1}. {ev.get('subregiao', 'Local')}</b><br><small>{ev.get('evento', '')}</small></div>", unsafe_allow_html=True)
                
    if st.session_state.logged_in and not st.session_state.modo_leitura_diario:
        st.markdown("---")
        st.subheader("⭐ Salvar no Devocional")
        if eventos_filtrados:
            opcoes_eventos = {e.get('evento'): e for e in eventos_filtrados}
            evento_selecionado_nome = st.selectbox("Selecione o local para salvar:", list(opcoes_eventos.keys()))
            evento_focado = opcoes_eventos[evento_selecionado_nome]
            
            anotacao = st.text_area("Sua reflexão ou oração sobre este lugar:", placeholder=f"O que Deus falou com você em {evento_focado.get('evento')}?")
            if st.button("Salvar Reflexão", type="primary", use_container_width=True):
                if anotacao:
                    cursor = conexao_db.cursor()
                    data_atual = datetime.now().strftime('%d/%m/%Y %H:%M')
                    cursor.execute("""
                        INSERT INTO diario_devocional (username, evento_id, nome_evento, anotacao, data_hora)
                        VALUES (?, ?, ?, ?, ?)
                    """, (st.session_state.username, evento_focado.get('id', evento_focado.get('evento')), evento_focado.get('evento'), anotacao, data_atual))
                    conexao_db.commit()
                    st.success(f"{evento_focado.get('evento')} salvo nos favoritos!")
                else:
                    st.warning("Escreva algo antes de salvar.")
        else:
            st.info("Nenhum evento disponível para salvar com a busca atual.")

    st.markdown("---")
    st.subheader("Modo Imersivo")
    if not st.session_state.modo_andarilho_ativo:
        if st.button("🚶‍♂️ Ativar Modo Andarilho (Cena)", use_container_width=True, type="primary"):
            st.session_state.modo_andarilho_ativo = True
            st.session_state.modo_leitura_diario = False
            st.rerun()
    else:
        if st.button("🌍 Voltar ao Mapa Global", use_container_width=True):
            st.session_state.modo_andarilho_ativo = False
            st.rerun()
            
    st.markdown("---")
    st.caption("v1.16.0 - Leitura em Tela Cheia do Diário")

# --- CONTEÚDO PRINCIPAL ---

# 1. RENDERIZA MODO DE LEITURA DO DEVOCIONAL (TELA CHEIA)
if st.session_state.modo_leitura_diario:
    col_titulo, col_btn = st.columns([4, 1])
    with col_titulo:
        st.header(f"📖 Caderno Devocional de {st.session_state.username}")
    with col_btn:
        st.write("") # Espaçamento
        if st.button("⬅️ Voltar ao Mapa"):
            st.session_state.modo_leitura_diario = False
            st.rerun()
            
    st.markdown("---")
    
    cursor = conexao_db.cursor()
    cursor.execute("SELECT id, data_hora, nome_evento, anotacao FROM diario_devocional WHERE username=? ORDER BY id DESC", (st.session_state.username,))
    todos_registros = cursor.fetchall()
    
    if not todos_registros:
        st.info("Você ainda não salvou nenhuma reflexão. Retorne ao mapa, selecione um local sagrado e comece a escrever o seu diário!")
    else:
        for reg in todos_registros:
            id_reg, data_reg, evento_reg, texto_reg = reg
            st.markdown(f"""
                <div class="leitura-devocional-card">
                    <h3>📍 {evento_reg}</h3>
                    <p class="data">Salvo em: {data_reg}</p>
                    <p class="texto">"{texto_reg}"</p>
                </div>
            """, unsafe_allow_html=True)
            
            # Botão interativo para pular da leitura direto para o mapa
            if st.button(f"🌍 Ver '{evento_reg}' no Mapa", key=f"ler_mapa_btn_{id_reg}"):
                st.session_state.termo_pesquisa_rapida = evento_reg
                st.session_state.modo_leitura_diario = False
                st.rerun()
            st.write("") # Espaço entre os blocos

# 2. RENDERIZA MAPA GLOBAL (SE MODO ANDARILHO E MODO DIÁRIO ESTIVEREM DESLIGADOS)
elif not st.session_state.modo_andarilho_ativo:
    if not eventos_filtrados:
        st.warning("Nenhum evento encontrado com os filtros ou termos de pesquisa aplicados.")

    mapa_biblico = folium.Map(
        location=st.session_state.coordenadas_foco, 
        zoom_start=st.session_state.zoom_foco, 
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Esri"
    )

    if tema_delineado:
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Fronteiras Atuais",
            overlay=True,
            control=False
        ).add_to(mapa_biblico)

    if seguir_caminhada and len(eventos_filtrados) > 1:
        coords_rota = [evento["coordenadas"] for evento in eventos_filtrados]
        folium.PolyLine(
            coords_rota,
            color="#e74c3c",
            weight=3,
            opacity=0.8,
            dash_array="10",
            tooltip=f"Jornada de {filtro_personagem}"
        ).add_to(mapa_biblico)
        mapa_biblico.fit_bounds(coords_rota)

    cluster_eventos = MarkerCluster().add_to(mapa_biblico)

    for evento in eventos_filtrados:
        coord = evento["coordenadas"]
        cor_marcador = "darkred" if evento.get("testamento") == "Antigo Testamento" else "cadetblue"
        
        html_popup = f"""
        <div style="font-family: Arial, sans-serif; width: 320px;">
            <h4 style="margin-bottom: 5px; color: #2C3E50; border-bottom: 1px solid #eee; padding-bottom: 5px;">{evento.get('evento', '')}</h4>
            <p style="margin: 4px 0; font-size: 13px;"><b>Local:</b> {evento.get('subregiao', '')}</p>
            <p style="margin: 4px 0; font-size: 13px;"><b>Envolvidos:</b> {evento.get('personagens', '')}</p>
            <p style="margin: 4px 0; font-size: 13px;"><b>Referência:</b> <i>{evento.get('referencia', '')}</i></p>
            <div style="margin-top: 12px; margin-bottom: 12px; background-color: #fcfbf7; padding: 10px; border-left: 4px solid #d35400; border-radius: 2px;">
                <p style="margin: 0; font-size: 13px; font-style: italic; color: #444; line-height: 1.5;">{evento.get('versiculo', 'Texto bíblico não disponível.')}</p>
            </div>
            <div style="margin-top: 10px; background-color: #f8f9fa; padding: 5px; border-radius: 4px;">
                <p style="margin: 0; font-size: 11px; color: #7f8c8d;"><b>Geografia Atual:</b> {evento.get('local_atual', '')}</p>
            </div>
        </div>
        """
        
        folium.Marker(
            location=coord,
            popup=folium.Popup(html_popup, max_width=350),
            tooltip=evento.get('evento', 'Local'),
            icon=folium.Icon(color=cor_marcador, icon=evento.get('icone', 'info-sign'))
        ).add_to(cluster_eventos)

    html_mapa = mapa_biblico._repr_html_()
    
    if tema_sepia:
        estilo_interno = "<style> html { filter: sepia(0.65) hue-rotate(-15deg) contrast(1.15) brightness(0.95); } </style>"
        html_mapa = estilo_interno + html_mapa

    components.html(html_mapa, height=750)

# 3. RENDERIZA MODO ANDARILHO 2D
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