import streamlit as st
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
    st.session_state.zoom_foco = 6000000 
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
    st.write("Explore geograficamente os eventos históricos em 3D.")
    
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
                for reg in registros_diario[:3]:
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
            st.info("Seu Devocional Guiado está vazio. Escolha um local no mapa 3D e salve suas reflexões!")

    st.markdown("---")
    st.header("Aparência do Globo 3D")
    tema_sepia = st.toggle("Ativar Tema Pergaminho (Sépia)", value=False)
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
    st.session_state.zoom_foco = 300000 
elif filtro_personagem == "Todos" and filtro_testamento == "Todos" and filtro_epoca == "Todas" and not termo_busca:
    st.session_state.coordenadas_foco = [31.7, 35.2]
    st.session_state.zoom_foco = 6000000 

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
    st.caption("v1.18.1 - Patch da Web Speech API (Bypass DOMPurify)")

# --- CONTEÚDO PRINCIPAL ---

if st.session_state.modo_leitura_diario:
    col_titulo, col_btn = st.columns([4, 1])
    with col_titulo:
        st.header(f"📖 Caderno Devocional de {st.session_state.username}")
    with col_btn:
        st.write("") 
        if st.button("⬅️ Voltar ao Globo 3D"):
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
            
            if st.button(f"🌍 Ver '{evento_reg}' no Globo", key=f"ler_mapa_btn_{id_reg}"):
                st.session_state.termo_pesquisa_rapida = evento_reg
                st.session_state.modo_leitura_diario = False
                st.rerun()
            st.write("") 

elif not st.session_state.modo_andarilho_ativo:
    
    st.info("🔊 Patch de Áudio aplicado! Teste clicar nos pop-ups do mapa ou no Modo Andarilho para ouvir a narração.")

    if not eventos_filtrados:
        st.warning("Nenhum evento encontrado com os filtros ou termos de pesquisa aplicados.")

    filtro_css = "filter: sepia(0.65) hue-rotate(-15deg) contrast(1.15) brightness(0.95);" if tema_sepia else "filter: none;"
    
    javascript_delineado = ""
    if tema_delineado:
        javascript_delineado = """
        viewer.imageryLayers.addImageryProvider(new Cesium.ArcGisMapServerImageryProvider({
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer'
        }));
        """

    javascript_markers = ""
    for evento in eventos_filtrados:
        lat, lon = evento["coordenadas"]
        nome_js = evento.get('evento', '').replace('"', '')
        subregiao_js = evento.get('subregiao', '').replace('"', '')
        
        # O HTML limpo APENAS COM ID, sem 'onclick' quebrando no DOMPurify
        html_popup = f"""
        <div style="font-family: Arial, sans-serif; padding: 5px;">
            <p style="margin: 4px 0; font-size: 13px; color: white;"><b>Local:</b> {subregiao_js}</p>
            <p style="margin: 4px 0; font-size: 13px; color: white;"><b>Envolvidos:</b> {evento.get('personagens', '')}</p>
            <p style="margin: 4px 0; font-size: 13px; color: white;"><b>Referência:</b> <i>{evento.get('referencia', '')}</i></p>
            <div style="margin-top: 12px; margin-bottom: 12px; background-color: #fcfbf7; padding: 10px; border-left: 4px solid #d35400;">
                <button id="btn-audio-cesium" style="float: right; background: none; border: none; cursor: pointer; font-size: 16px;" title="Ouvir Narração">🔊</button>
                <p class="texto-versiculo-ler" style="margin: 0; font-size: 13px; font-style: italic; color: #444;">{evento.get('versiculo', 'Texto indisponível.')}</p>
            </div>
            <p style="margin: 0; font-size: 11px; color: #ccc;"><b>Geografia Atual:</b> {evento.get('local_atual', '')}</p>
        </div>
        """
        
        javascript_markers += f"""
        viewer.entities.add({{
            name: "{nome_js}",
            position: Cesium.Cartesian3.fromDegrees({lon}, {lat}),
            point: {{ 
                pixelSize: 12, 
                color: Cesium.Color.fromCssColorString('#8B0000'), 
                outlineColor: Cesium.Color.WHITE, 
                outlineWidth: 2 
            }},
            label: {{ 
                text: "{subregiao_js}", 
                font: '12pt serif', 
                style: Cesium.LabelStyle.FILL_AND_OUTLINE, 
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 4, 
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM, 
                pixelOffset: new Cesium.Cartesian2(0, -15) 
            }},
            description: `{html_popup}`
        }});
        """

    javascript_polyline = ""
    if seguir_caminhada and len(eventos_filtrados) > 1:
        js_coords = []
        for e in eventos_filtrados:
            js_coords.extend([e["coordenadas"][1], e["coordenadas"][0]]) 
        js_coords_str = ", ".join(map(str, js_coords))
        
        javascript_polyline = f"""
        viewer.entities.add({{
            polyline: {{
                positions: Cesium.Cartesian3.fromDegreesArray([{js_coords_str}]),
                width: 3,
                material: new Cesium.PolylineDashMaterialProperty({{
                    color: Cesium.Color.fromCssColorString('#e74c3c'),
                    dashLength: 10.0
                }})
            }}
        }});
        """

    lat_foco, lon_foco = st.session_state.coordenadas_foco
    alt_foco = st.session_state.zoom_foco
    
    if seguir_caminhada and len(eventos_filtrados) > 1:
        javascript_camera = "viewer.zoomTo(viewer.entities).then(function(){ viewer.camera.zoomOut(1000000); });"
    else:
        javascript_camera = f"""
        viewer.camera.flyTo({{
            destination: Cesium.Cartesian3.fromDegrees({lon_foco}, {lat_foco}, {alt_foco})
        }});
        """

    html_cesium = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.104.0/Cesium.js"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/cesium/1.104.0/Widgets/widgets.css" rel="stylesheet">
        <style>
            html, body, #cesiumContainer {{
                width: 100%; height: 100%; margin: 0; padding: 0; overflow: hidden;
                border-radius: 8px;
            }}
            .cesium-viewer canvas {{
                {filtro_css}
            }}
            .cesium-viewer-toolbar, .cesium-viewer-animationContainer, 
            .cesium-viewer-timelineContainer, .cesium-viewer-bottom,
            .cesium-widget-credits {{
                display: none !important;
            }}
            .cesium-infoBox {{
                background: rgba(15, 23, 42, 0.95) !important;
                border: 1px solid #fbbf24 !important;
                border-radius: 8px;
            }}
            .cesium-infoBox-title {{
                background-color: #0d1117 !important;
                color: #fbbf24 !important;
            }}
        </style>
    </head>
    <body>
        <div id="cesiumContainer"></div>
        <script>
            Cesium.Ion.defaultAccessToken = '';

            const viewer = new Cesium.Viewer('cesiumContainer', {{
                imageryProvider: new Cesium.ArcGisMapServerImageryProvider({{
                    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer'
                }}),
                baseLayerPicker: false,
                geocoder: false,
                homeButton: false,
                sceneModePicker: false,
                navigationHelpButton: false,
                animation: false,
                timeline: false,
                fullscreenButton: false,
                infoBox: true
            }});

            {javascript_delineado}
            {javascript_markers}
            {javascript_polyline}
            {javascript_camera}

            // O SCRIPT MESTRE: Monitora os cliques do pop-up por fora do DOMPurify
            viewer.selectedEntityChanged.addEventListener(function(entity) {{
                if (entity && viewer.infoBox) {{
                    // Espera meio segundo para garantir que a janela e o iframe interno foram montados na tela
                    setTimeout(function() {{
                        try {{
                            var iframeDoc = viewer.infoBox.frame.contentDocument || viewer.infoBox.frame.contentWindow.document;
                            if (iframeDoc) {{
                                var btn = iframeDoc.getElementById('btn-audio-cesium');
                                if (btn) {{
                                    // Amarra o evento JavaScript dinamicamente, blindando contra os filtros do Cesium
                                    btn.onclick = function() {{
                                        var textoLocal = iframeDoc.querySelector('.texto-versiculo-ler').innerText;
                                        var msg = new SpeechSynthesisUtterance(textoLocal);
                                        msg.lang = 'pt-BR';
                                        msg.rate = 1.0;
                                        
                                        // Usa o synth do parent iframe para impedir que o navegador bloqueie audios em sandboxes
                                        var synth = window.speechSynthesis;
                                        if (window.parent && window.parent.speechSynthesis) {{
                                            synth = window.parent.speechSynthesis;
                                        }}
                                        synth.cancel();
                                        synth.speak(msg);
                                    }};
                                }}
                            }}
                        }} catch(err) {{
                            console.log('Falha ao injetar audio no Cesium: ', err);
                        }}
                    }}, 400);
                }}
            }});
        </script>
    </body>
    </html>
    """

    components.html(html_cesium, height=750)

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

        # O botão do Modo Andarilho também foi refatorado para ler direto do DOM via DOM Traversal
        html_modo_andarilho = f"""
        <div class="andarilho-container">
            {tag_imagem}
            <div class="creditos-legenda">
                <button onclick="
                    try {{
                        var texto = this.parentElement.querySelector('blockquote').innerText;
                        var msg = new SpeechSynthesisUtterance(texto);
                        msg.lang = 'pt-BR';
                        var synth = window.speechSynthesis;
                        if(window.parent && window.parent.speechSynthesis) {{ synth = window.parent.speechSynthesis; }}
                        synth.cancel();
                        synth.speak(msg);
                    }} catch(e) {{ console.log(e); }}
                " style="float: right; background: rgba(0,0,0,0.5); border: 1px solid #fbbf24; border-radius: 50%; padding: 8px; cursor: pointer; font-size: 18px; color: white;" title="Ouvir Versículo">🔊</button>
                <h2>📍 {nome_evento}</h2>
                <p class="sub"><b>Região:</b> {subregiao}</p>
                <blockquote>{texto_versiculo}</blockquote>
                <p class="explicacao">{texto_explicacao}</p>
            </div>
        </div>
        """
        components.html(html_modo_andarilho, height=750)