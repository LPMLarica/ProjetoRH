import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Desempenhos", page_icon="⭐", layout="wide")

if "colaboradores" not in st.session_state:
    st.session_state.colaboradores = []

st.sidebar.title("Gerenciar Colaboradores")

def normalizar_nome(nome):
    return str(nome).strip().lower()

uploaded_certificados = st.sidebar.file_uploader("Planilha de Certificados", type=["xlsx"], key="certificados")

certificados_por_nome = {}
cursos_certificados_por_nome = {}

if uploaded_certificados:
    try:
        df_cert = pd.read_excel(uploaded_certificados)
        df_cert["Nome"] = df_cert["Nome"].apply(normalizar_nome)
        df_cert["Curso"] = df_cert["Curso"].astype(str).str.strip()

        certificados_por_nome = df_cert.groupby("Nome")["Curso"].count().to_dict()
        cursos_certificados_por_nome = df_cert.groupby("Nome")["Curso"].apply(list).to_dict()

        df_grouped = df_cert.groupby("Nome").agg(
            Certificados=("Curso", "count"),
            Posicao=("Posição Organizacional", "first")
        ).reset_index()

        st.session_state.colaboradores = []
        for _, row in df_grouped.iterrows():
            nome_normalizado = normalizar_nome(row["Nome"])
            aproveitamento = min(100, row["Certificados"] * 10)
            st.session_state.colaboradores.append({
                "Nome": nome_normalizado,
                "Certificados": row["Certificados"],
                "Aproveitamento (%)": aproveitamento,
                "Posição Organizacional": row["Posicao"]
            })

        st.success("Certificados importados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao ler a planilha de certificados: {e}")

st.sidebar.markdown("### Planilha de Tarefas da equipe")
uploaded_status = st.sidebar.file_uploader("Cursos com status", type=["xlsx"], key="status")

cursos_finalizado = set()
finalizado_por_nome = {}
cursos_nomes_por_nome = {}
iniciados_por_nome = {}
cursos_iniciados_nomes_por_nome = {}

if uploaded_status:
    try:
        df_status = pd.read_excel(uploaded_status)
        df_status["Nome do usuário da equipe"] = df_status["Nome do usuário da equipe"].apply(normalizar_nome)
        df_status = df_status.rename(columns={"Nome do usuário da equipe": "Nome"})
        if not {"Nome", "Curso", "Status do Curso"}.issubset(df_status.columns):
            st.sidebar.error("A planilha deve conter as colunas: Nome, Curso, Status do Curso.")
        else:
            df_status["Status do Curso"] = df_status["Status do Curso"].str.lower().str.strip()
            df_finalizado = df_status[df_status["Status do Curso"] == "finalizado"]
            df_iniciado = df_status[df_status["Status do Curso"] == "iniciado"]
            iniciados_por_nome = df_iniciado.groupby("Nome")["Curso"].nunique().to_dict()
            cursos_iniciados_nomes_por_nome = df_iniciado.groupby("Nome")["Curso"].apply(list).to_dict()
            cursos_finalizado = set(zip(df_finalizado["Nome"], df_finalizado["Curso"]))
            finalizado_por_nome = df_finalizado.groupby("Nome")["Curso"].nunique().to_dict()
            cursos_nomes_por_nome = df_finalizado.groupby("Nome")["Curso"].apply(list).to_dict()

            st.sidebar.success("Cursos finalizados processados com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao processar status dos cursos: {e}")

st.sidebar.markdown("### Planilha de Tempo de Estudo")
uploaded_tempo = st.sidebar.file_uploader("Tempo de estudo por colaborador", type=["xlsx"], key="tempo")

tempo_por_nome = {}

if uploaded_tempo:
    try:
        df_tempo = pd.read_excel(uploaded_tempo)
        df_tempo["Nome"] = df_tempo["Nome"].apply(normalizar_nome)
        if not {"Nome", "Tempo de Estudo no Período"}.issubset(df_tempo.columns):
            st.sidebar.error("A planilha deve conter: Nome, Tempo de Estudo no Período.")
        else:
            tempo_por_nome = df_tempo.groupby("Nome")["Tempo de Estudo no Período"].sum().to_dict()
            st.sidebar.success("Tempo de estudo importado com sucesso!")
    except Exception as e:
        st.sidebar.error(f"Erro ao processar tempo de estudo: {e}")

nome = st.sidebar.text_input("Nome")
certificados = st.sidebar.number_input("Certificados", min_value=0, step=1)

if st.sidebar.button("Adicionar Colaborador"):
    nome_normalizado = normalizar_nome(nome)
    aproveitamento = min(100, certificados * 10)
    st.session_state.colaboradores.append({
        "Nome": nome_normalizado,
        "Certificados": certificados,
        "Aproveitamento (%)": aproveitamento
    })

st.sidebar.markdown("---")
st.sidebar.subheader("Excluir Colaborador")
nomes_existentes = [c['Nome'] for c in st.session_state.colaboradores]
nome_excluir = st.sidebar.selectbox("Selecionar para excluir", options=nomes_existentes if nomes_existentes else ["Nenhum"])
if nome_excluir != "Nenhum" and st.sidebar.button("Excluir"):
    st.session_state.colaboradores = [c for c in st.session_state.colaboradores if c['Nome'] != nome_excluir]
    st.sidebar.success(f"Colaborador {nome_excluir} excluído.")

st.title("Dashboard de Desempenho Universidade FGF")

if st.session_state.colaboradores:
    df = pd.DataFrame(st.session_state.colaboradores)

    def combinar_cursos_concluidos(nome):
        nome = normalizar_nome(nome)
        qtd_status = finalizado_por_nome.get(nome, 0)
        qtd_certificados = certificados_por_nome.get(nome, 0)
        return qtd_status + qtd_certificados

    def combinar_nomes_cursos(nome):
        nome = normalizar_nome(nome)
        cursos_status = cursos_nomes_por_nome.get(nome, [])
        cursos_cert = cursos_certificados_por_nome.get(nome, [])
        return ", ".join(cursos_status + cursos_cert)
    
    def combinar_nomes_iniciados(nome):
        nome = normalizar_nome(nome)
        return ", ".join(cursos_iniciados_nomes_por_nome.get(nome, []))

    df["Cursos Concluídos"] = df["Nome"].apply(combinar_cursos_concluidos)
    df["Cursos Concluídos (nomes)"] = df["Nome"].apply(combinar_nomes_cursos)
    df["Tempo de Estudo (h)"] = df["Nome"].apply(lambda n: tempo_por_nome.get(normalizar_nome(n), 0.0))
    df["Cursos Iniciados"] = df["Nome"].apply(lambda n: iniciados_por_nome.get(normalizar_nome(n), 0))
    df["Cursos Iniciados (nomes)"] = df["Nome"].apply(combinar_nomes_iniciados)

    df = df.sort_values(by="Aproveitamento (%)", ascending=False).reset_index(drop=True)
    df.index += 1
    df["Ranking"] = df.index

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Gráfico de Aproveitamento")
        bar_fig = px.bar(
            df,
            x="Nome",
            y="Aproveitamento (%)",
            color=df["Ranking"].apply(lambda x: "🥇" if x == 1 else "🥈" if x == 2 else "🥉" if x == 3 else "Demais"),
            color_discrete_map={"🥇": "gold", "🥈": "lightgreen", "🥉": "mediumseagreen", "Demais": "lightblue"},
            hover_data=["Certificados", "Cursos Concluídos", "Cursos Concluídos (nomes)", "Cursos Iniciados", "Cursos Iniciados (nomes)", "Tempo de Estudo (h)", "Ranking"]
        )
        bar_fig.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(bar_fig, use_container_width=True)

    with col2:
        st.markdown("### Gráfico de Pizza")
        pie_fig = px.pie(
            df,
            names="Nome",
            values="Aproveitamento (%)",
            title="Distribuição de Aproveitamento",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(pie_fig, use_container_width=True)

    st.subheader("Tabela de Desempenho e Ranking")
    st.dataframe(df, use_container_width=True)

    if "Tempo de Estudo (h)" in df.columns:
        df["Tempo de Estudo (h)"] = pd.to_numeric(df["Tempo de Estudo (h)"], errors="coerce")
        total_horas_estudo = df["Tempo de Estudo (h)"].sum()
        st.markdown(f"**Soma Total de Horas de Estudo:** {total_horas_estudo:.2f} horas")
    else:
        st.markdown("**Soma Total de Horas de Estudo:** não disponível (coluna ausente)")
