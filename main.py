import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(layout="wide")

if "colaboradores" not in st.session_state:
    st.session_state.colaboradores = []

with st.sidebar:
    st.title("Gerenciar Colaboradores")

    uploaded_file = st.file_uploader("Importar planilha Excel (CEFiS)", type=["xlsx"])
    if uploaded_file:
        try:

            df_excel = pd.read_excel(uploaded_file)
            
            df_grouped = df_excel.groupby("Nome").agg(
                Certificados=("Nome", "count"),
                Posicao=("Posição Organizacional", "first")
            ).reset_index()

            st.session_state.colaboradores = []

            for _, row in df_grouped.iterrows():
                aproveitamento = min(100, row["Certificados"] * 10)
                st.session_state.colaboradores.append({
                    "Nome": row["Nome"],
                    "Certificados": row["Certificados"],
                    "Aproveitamento (%)": aproveitamento,
                    "Posição Organizacional": row["Posicao"]
                })
            st.success("Dados da planilha importados com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

    nome = st.text_input("Nome")
    certificados = st.number_input("Certificados", min_value=0, step=1)

    if st.button("Adicionar Colaborador"):
        aproveitamento = min(100, certificados * 10)
        st.session_state.colaboradores.append({
            "Nome": nome,
            "Certificados": certificados,
            "Aproveitamento (%)": aproveitamento
        })

    st.markdown("---")
    st.subheader("Excluir Colaborador")
    nomes_existentes = [c['Nome'] for c in st.session_state.colaboradores]
    nome_excluir = st.selectbox("Selecionar para excluir", options=nomes_existentes if nomes_existentes else ["Nenhum"])
    if nome_excluir != "Nenhum" and st.button("Excluir"):
        st.session_state.colaboradores = [c for c in st.session_state.colaboradores if c['Nome'] != nome_excluir]
        st.success(f"Colaborador {nome_excluir} excluído.")

st.title("Dashboard de Desempenho")

if st.session_state.colaboradores:
    df = pd.DataFrame(st.session_state.colaboradores)
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
            hover_data=[ "Certificados", "Ranking"]
        )
        bar_fig.update_layout(yaxis_range=[0, 100])
        st.plotly_chart(bar_fig, use_container_width=True)

    with col2:
        st.markdown("### Gráfico de Pizza (Participação no Desempenho)")
        pie_fig = px.pie(
            df,
            names="Nome",
            values="Aproveitamento (%)",
            title="Distribuição de Aproveitamento por Colaborador",
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(pie_fig, use_container_width=True)

    st.subheader("Tabela de Dados e Ranking")
    st.dataframe(df, use_container_width=True)
