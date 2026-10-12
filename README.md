<img width="959" height="537" alt="image" src="https://github.com/user-attachments/assets/dc2986bb-effa-45d8-a834-38f9d3b28c96" />

# 🌍 Bíblia Maps - Globo Interativo & Devocional Guiado

Uma aplicação web imersiva que transforma o estudo bíblico e histórico em uma experiência geoespacial em 3D. Explore as rotas dos patriarcas, a geografia das batalhas antigas e o avanço da igreja primitiva diretamente no globo terrestre, enquanto constrói um caderno de orações pessoal.

---

## ✨ Funcionalidades Principais

*   🌍 **Globo 3D Interativo (CesiumJS):** Transição fluida de uma visão espacial orbital para o terreno plano focado na topografia do Oriente Médio, Mediterrâneo e Europa. O relevo e as elevações físicas são renderizados nativamente.
*   📜 **Modo Imersivo (Andarilho):** Clique em um evento e a tela se transforma: o mapa é substituído por cenários focados na história, acompanhados de referências bíblicas, versículos completos e contexto histórico formatados em um visual elegante de papiro.
*   🚶‍♂️ **Rastreio de Rotas (Itinerário Dinâmico):** Pesquise por um personagem (como "Paulo" ou "Jesus") e o mapa desenhará automaticamente uma rota histórica em vermelho conectando todos os locais por onde ele passou, ajustando a câmera para enquadrar toda a jornada.
*   🔍 **Pesquisa Lógica Avançada (`+`):** Motor de busca que varre livros, nomes, capítulos e personagens ao mesmo tempo. Ex: `Davi+Golias` ou `Moisés+Mar` para encontrar um evento específico combinando palavras.
*   🔐 **Painel SaaS (Contas e Autenticação):** Sistema isolado em SQLite permitindo que múltiplos usuários criem contas.
*   📖 **Devocional Guiado em Tela Cheia:** Durante a exploração, clique e salve um local ("Adicionar aos Favoritos") escrevendo a sua reflexão ou oração daquele dia. Posteriormente, abra seu caderno em tela cheia para leitura ou clique no botão para que o mapa volte exatamente àquela coordenada.
*   🎨 **Filtros e Aparência:** 
    *   **Tema Pergaminho (Sépia):** Aplica um filtro *vintage* (via CSS no canvas 3D) resgatando o visual de mapas de navegação antigos.
    *   **Delineado do Mapa Atual:** Sobreposição transparente das fronteiras e nomenclaturas de países modernos sobre as antigas rotas para contextualização geopolítica.

---

## 🛠️ Tecnologias Utilizadas

*   **Frontend & Servidor Web:** Streamlit
*   **Motor Espacial 3D:** CesiumJS (Injetado via `components.html`)
*   **Geografia Base:** Esri World Physical Map
*   **Banco de Dados (Auth e Diário):** SQLite3 (Nativo) e hashlib para segurança
*   **Estrutura de Dados Geoespaciais:** JSON (Customizado)

---

## 🚀 Como rodar localmente (Para Desenvolvedores)

Siga os passos abaixo para rodar o aplicativo na sua própria máquina.

### Pré-requisitos
*   Ter o Python 3.9+ instalado.
*   *Nota:* O motor 3D roda 100% no navegador (JavaScript). Portanto, o Python processa apenas a interface e o banco de dados.

### Passo a Passo

1. **Clone o repositório e entre na pasta:**
   ```bash
   git clone [https://github.com/SEU_USUARIO/BibliaMaps.git](https://github.com/SEU_USUARIO/BibliaMaps.git)
   cd BibliaMaps



2. **Crie e ative um ambiente virtual:**

    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3. **Instale as dependências (que são incrivelmente curtas!):**

    ```bash
    pip install -r requirements.txt
    ```
4. **Inicie o servidor local:**
    ```bash
    python -m streamlit run app.py
    ```