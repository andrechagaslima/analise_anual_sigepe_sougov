import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuração inicial da página
st.set_page_config(page_title="Evolução de Notas SouGov", layout="wide")
st.title("📈 Análise de Variação Mensal das Notas")

# --- SELETOR NA TELA PRINCIPAL (Removido o .sidebar) ---
st.markdown("### Configurações")
opcao_dataset = st.selectbox(
    "Selecione a base de dados para análise:",
    ("SouGov", "Sigepe")
)
st.divider()

# Define qual arquivo será lido com base na escolha
if opcao_dataset == "SouGov":
    arquivo_csv = "avaliacoes_sistema_sougov.csv"
else:
    arquivo_csv = "avaliacoes_sistema_sigepe.csv" 

# 2. Carregamento de dados
@st.cache_data
def carregar_dados(caminho_arquivo):
    df = pd.read_csv(caminho_arquivo, low_memory=False)
    
    nome_coluna_data = 'Data' 
    nome_coluna_nota = 'Nota' 
    
    df[nome_coluna_data] = pd.to_datetime(df[nome_coluna_data], errors='coerce')
    df['Mes_Ano'] = df[nome_coluna_data].dt.to_period('M').astype(str)
    df[nome_coluna_nota] = pd.to_numeric(df[nome_coluna_nota], errors='coerce')
    df = df.dropna(subset=[nome_coluna_data, nome_coluna_nota])
    
    return df, nome_coluna_nota

# Carrega os dados do arquivo selecionado
try:
    df, coluna_nota = carregar_dados(arquivo_csv)
except FileNotFoundError:
    st.error(f"⚠️ Arquivo '{arquivo_csv}' não encontrado. Verifique o nome ou o caminho.")
    st.stop()

# Média Global do arquivo selecionado
media_global = df[coluna_nota].mean()

# Meses alvo da análise
meses_alvo = [
    "2025-03", "2025-04", "2025-05", "2025-06", 
    "2025-07", "2025-08", "2025-09", "2025-10", 
    "2025-11", "2025-12", "2026-01", "2026-02"
]

df_periodo = df[df['Mes_Ano'].isin(meses_alvo)]

if df_periodo.empty:
    st.warning("Nenhum dado encontrado para os meses filtrados neste dataset.")
else:
    # 3. Agrupamento e Cálculo de Variação (MoM)
    df_agrupado = df_periodo.groupby('Mes_Ano')[coluna_nota].agg(
        Média='mean',
        Desvio_Padrão='std',
        Quantidade='count'
    ).reset_index()
    
    df_agrupado = df_agrupado.sort_values('Mes_Ano')
    
    # Variações absolutas e percentuais
    df_agrupado['Variação_Absoluta'] = df_agrupado['Média'].diff()
    df_agrupado['Variação_Percentual'] = df_agrupado['Média'].pct_change() * 100
    
    st.markdown(f"**Média Histórica Global do Dataset Selecionado:** `{media_global:.2f}`")
    st.divider()

    # 4. Exibição dos Cards (Métricas com setas)
    st.subheader(f"🗓️ Variação Mês a Mês - {opcao_dataset}")
    
    cols = st.columns(4)
    for index, row in df_agrupado.iterrows():
        col = cols[index % 4]
        
        if pd.isna(row['Variação_Absoluta']):
            delta_str = "Início do período"
        else:
            delta_str = f"{row['Variação_Absoluta']:.2f} ({row['Variação_Percentual']:.1f}%)"
            
        col.metric(
            label=f"Mês: {row['Mes_Ano']}",
            value=f"{row['Média']:.2f}",
            delta=delta_str
        )

    st.divider()

    # 5. Gráfico de Tendência (Linha) com todos os meses no eixo X
    st.subheader("📉 Evolução Temporal das Notas")
    
    fig = px.line(
        df_agrupado, 
        x='Mes_Ano', 
        y='Média', 
        markers=True,
        text=df_agrupado['Média'].apply(lambda x: f'{x:.2f}'),
        title=f"Tendência da Média Mensal - {opcao_dataset}",
        labels={'Mes_Ano': 'Mês', 'Média': 'Nota Média'}
    )
    
    # Força todos os meses aparecerem e inclina os rótulos em 45 graus
    fig.update_xaxes(type='category', tickangle=-45)
    
    fig.update_traces(textposition="top center")
    fig.add_hline(
        y=media_global, 
        line_dash="dash", 
        line_color="gray", 
        annotation_text=f"Média Global ({media_global:.2f})"
    )
    
    min_y = df_agrupado['Média'].min() * 0.95
    max_y = df_agrupado['Média'].max() * 1.05
    fig.update_layout(yaxis_range=[min_y, max_y])
    
    st.plotly_chart(fig, use_container_width=True)

    # 6. Tabela de Dados Analíticos
    st.subheader("📑 Tabela de Dados Analíticos")
    
    def colorir_variacao(val):
        if pd.isna(val): return ''
        color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
        return f'color: {color}'

    df_exibicao = df_agrupado.style.format({
        'Média': '{:.2f}',
        'Desvio_Padrão': '{:.2f}',
        'Variação_Absoluta': '{:.2f}',
        'Variação_Percentual': '{:.2f}%'
    }).applymap(colorir_variacao, subset=['Variação_Absoluta', 'Variação_Percentual'])

    st.dataframe(df_exibicao, hide_index=True, use_container_width=True)