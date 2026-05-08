
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Steel Production MECE Dashboard", layout="wide")

@st.cache_data
def load_all_data():
    # Пути можно заменить на прямые ссылки с GitHub Raw если нужно
    s = pd.read_excel('smelting_v2.xlsx')
    r = pd.read_excel('rolling_v2.xlsx')
    c = pd.read_excel('cutting_v2.xlsx')
    sh = pd.read_excel('shipping_v2.xlsx')
    return s, r, c, sh

df_s, df_r, df_c, df_sh = load_all_data()

st.title("🏗 Сквозная аналитика производства (MECE)")
st.info("Данные синхронизированы: каждая тонна учтена при переходе между этапами.")

# --- РАСЧЕТЫ MECE ---
total_smelt = df_s['Масса, тн'].sum()
prime_slabs_total = df_s[df_s['Признак годности'] == 'Годные']['Масса, тн'].sum()
to_rolling = df_s[df_s['Прокатка'] == 'ЦГП']['Масса, тн'].sum()

rolled_prime = df_r[df_r['Признак годности'] == 'годные']['Масса, тн'].sum()
to_cutting = df_r[df_r['Порезка'] == 'порезано']['Масса, тн'].sum()

cut_prime = df_c[df_c['Признак годности'] == 'годные']['Масса, тн'].sum()
shipped_final = df_sh[df_sh['Получатель'] == 'Отгрузка клиенту']['Масса, тн'].sum()

# --- KPI Метрики ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Выплавка всего", f"{total_smelt} тн")
m2.metric("В прокат", f"{to_rolling} тн", f"{to_rolling/total_smelt:.1%}")
m3.metric("На порезку", f"{to_cutting} тн", f"{to_cutting/to_rolling:.1%}")
m4.metric("Клиенту", f"{shipped_final} тн", f"{shipped_final/total_smelt:.1%}")

# --- SANKEY DIAGRAM ---
st.subheader("🌊 Карта потоков металла")

# Узлы
label = [
    "Всего Выплавка",       # 0
    "Переходные/Обрезь",    # 1
    "Склад (Слябы)",        # 2
    "ЦГП (Прокатка)",       # 3
    "Потери проката",       # 4
    "Некондиция",           # 5
    "Склад (Рулоны)",       # 6
    "Порезка",              # 7
    "Потери резки",         # 8
    "Годные листы",         # 9
    "Склад (Листы)",        # 10
    "ОТГРУЖЕНО КЛИЕНТУ"     # 11
]

# Связи (MECE)
source = [0, 0, 0, 3, 3, 3, 3, 7, 7, 9, 9]
target = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
value = [
    df_s[df_s['Признак годности'] == 'Переходные и обрезь']['Масса, тн'].sum(),
    df_s[df_s['Прокатка'] == 'Склад']['Масса, тн'].sum(),
    to_rolling,
    df_r[df_r['Признак годности'] == 'потери при прокатке']['Масса, тн'].sum(),
    df_r[df_r['Признак годности'] == 'некондиция']['Масса, тн'].sum(),
    df_r[df_r['Порезка'] == 'Склад']['Масса, тн'].sum(),
    to_cutting,
    df_c[df_c['Признак годности'] == 'потери при резке']['Масса, тн'].sum(),
    cut_prime,
    df_sh[df_sh['Получатель'] == 'Склад']['Масса, тн'].sum(),
    shipped_final
]

fig = go.Figure(data=[go.Sankey(
    node = dict(pad = 15, thickness = 20, line = dict(color = "black", width = 0.5), label = label, color = "darkblue"),
    link = dict(source = source, target = target, value = value)
)])
st.plotly_chart(fig, use_container_width=True)

# --- ДЕТАЛЬНЫЕ ТАБЛИЦЫ ---
with st.expander("🔍 Посмотреть детализацию по базам данных"):
    tab1, tab2, tab3, tab4 = st.tabs(["Выплавка", "Прокатка", "Порезка", "Отгрузка"])
    tab1.dataframe(df_s)
    tab2.dataframe(df_r)
    tab3.dataframe(df_cut)
    tab4.dataframe(df_sh)
