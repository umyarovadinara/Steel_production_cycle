
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(page_title="Steel Production Analytics", layout="wide")

# --- ФУНКЦИЯ ГЕНЕРАЦИИ ДАННЫХ (MECE ЛОГИКА) ---
def ensure_dummy_data():
    files = {
        'smelting_v2.xlsx': {
            'Дата': ['01.05.2024']*3,
            'ID Плавки': ['M-001']*3,
            'Толщина сляба, мм': [250]*3,
            'Ширина сляба, мм': [1500]*3,
            'Масса, тн': [50, 200, 750],
            'Признак годности': ['Переходные и обрезь', 'Годные', 'Годные'],
            'Прокатка': ['-', 'Склад', 'ЦГП']
        },
        'rolling_v2.xlsx': {
            'Дата': ['02.05.2024']*4,
            'Толщина, мм': [10]*4,
            'Ширина, мм': [1500]*4,
            'Масса, тн': [20, 30, 100, 600],
            'Признак годности': ['потери при прокатке', 'некондиция', 'годные', 'годные'],
            'Порезка': ['-', '-', 'Склад', 'порезано']
        },
        'cutting_v2.xlsx': {
            'Дата': ['03.05.2024']*2,
            'Толщина, мм': [10]*2,
            'Ширина, мм': [750]*2,
            'Масса, тн': [10, 590],
            'Признак годности': ['потери при резке', 'годные']
        },
        'shipping_v2.xlsx': {
            'Дата': ['04.05.2024']*2,
            'Толщина, мм': [10]*2,
            'Ширина, мм': [750]*2,
            'Масса, тн': [40, 550],
            'Получатель': ['Склад', 'Отгрузка клиенту']
        }
    }
    for f_name, data in files.items():
        if not os.path.exists(f_name):
            pd.DataFrame(data).to_excel(f_name, index=False)

ensure_dummy_data()

# --- ЗАГРУЗКА ДАННЫХ ---
@st.cache_data
def load_data():
    s = pd.read_excel('smelting_v2.xlsx')
    r = pd.read_excel('rolling_v2.xlsx')
    c = pd.read_excel('cutting_v2.xlsx')
    sh = pd.read_excel('shipping_v2.xlsx')
    return s, r, c, sh

df_s, df_r, df_c, df_sh = load_data()

st.title("🏗 Цикл производства высокопрочной стали")
st.markdown("---")

# --- РАСЧЕТ ПОКАЗАТЕЛЕЙ (MECE) ---
total_in = df_s['Масса, тн'].sum()
to_rolling = df_s[df_s['Прокатка'] == 'ЦГП']['Масса, тн'].sum()
to_cutting = df_r[df_r['Порезка'] == 'порезано']['Масса, тн'].sum()
shipped = df_sh[df_sh['Получатель'] == 'Отгрузка клиенту']['Масса, тн'].sum()

# KPI
cols = st.columns(4)
cols[0].metric("Выплавка (Всего)", f"{total_in} тн")
cols[1].metric("Ушло в прокат", f"{to_rolling} тн")
cols[2].metric("Ушло на порезку", f"{to_cutting} тн")
cols[3].metric("Отгружено клиенту", f"{shipped} тн", f"{shipped/total_in:.1%}")

# --- SANKEY DIAGRAM ---
st.subheader("📊 Потоки и потери (Sankey Diagram)")

nodes = [
    "Выплавка (Старт)", "Переходные", "Склад (Слябы)", "ЦГП", 
    "Потери проката", "Некондиция", "Склад (Рулоны)", "Порезка", 
    "Потери резки", "Склад (Листы)", "ОТГРУЖЕНО"
]

# Логика связей
# 0 -> 1 (Переходные), 0 -> 2 (Склад слябов), 0 -> 3 (ЦГП)
# 3 -> 4 (Потери), 3 -> 5 (Некондиция), 3 -> 6 (Склад рулонов), 3 -> 7 (Порезка)
# 7 -> 8 (Потери резки), 7 -> 10 (Отгружено) через промежуточный склад 9
# Мы берем суммы из загруженных MECE экселей:

links = dict(
    source = [0, 0, 0, 3, 3, 3, 3, 7, 7, 7],
    target = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    value = [
        df_s[df_s['Признак годности'] == 'Переходные и обрезь']['Масса, тн'].sum(),
        df_s[df_s['Прокатка'] == 'Склад']['Масса, тн'].sum(),
        to_rolling,
        df_r[df_r['Признак годности'] == 'потери при прокатке']['Масса, тн'].sum(),
        df_r[df_r['Признак годности'] == 'некондиция']['Масса, тн'].sum(),
        df_r[df_r['Порезка'] == 'Склад']['Масса, тн'].sum(),
        to_cutting,
        df_c[df_c['Признак годности'] == 'потери при резке']['Масса, тн'].sum(),
        df_sh[df_sh['Получатель'] == 'Склад']['Масса, тн'].sum(),
        shipped
    ]
)

fig = go.Figure(data=[go.Sankey(
    node = dict(pad=15, thickness=20, label=nodes, color="royalblue"),
    link = links
)])
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
# Таблицы данных
with st.expander("📥 Посмотреть сырые данные (Excel)"):
    t1, t2, t3, t4 = st.tabs(["Выплавка", "Прокатка", "Порезка", "Отгрузка"])
    t1.dataframe(df_s)
    t2.dataframe(df_r)
    t3.dataframe(df_c)
    t4.dataframe(df_sh)
