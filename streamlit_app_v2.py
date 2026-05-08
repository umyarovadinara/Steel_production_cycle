import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Steel Production Monitoring", layout="wide")

# --- ФУНКЦИЯ ЗАГРУЗКИ ---
# При деплое на GitHub файлы должны лежать в той же папке, что и этот скрипт
@st.cache_data
def load_data():
    try:
        s = pd.read_excel('smelting_v3.xlsx')
        r = pd.read_excel('rolling_v3.xlsx')
        c = pd.read_excel('cutting_v3.xlsx')
        sh = pd.read_excel('shipping_v3.xlsx')
        return s, r, c, sh
    except FileNotFoundError as e:
        st.error(f"Ошибка: Не найден файл {e.filename}. Убедитесь, что загрузили эксели в репозиторий.")
        st.stop()

df_s, df_r, df_c, df_sh = load_data()

# --- SIDEBAR (ПАНЕЛЬ ФИЛЬТРОВ) ---
st.sidebar.header("🔍 Фильтры данных")

# Множественный выбор марок
all_marks = sorted(df_s['Марка'].unique())
selected_marks = st.sidebar.multiselect("Выберите марки стали:", options=all_marks, default=all_marks)

# Множественный выбор плавок
all_ids = sorted(df_s['ID Плавки'].unique())
selected_ids = st.sidebar.multiselect("Выберите ID плавок:", options=all_ids, default=all_ids)

# Фильтрация всех датафреймов
df_s_f = df_s[(df_s['Марка'].isin(selected_marks)) & (df_s['ID Плавки'].isin(selected_ids))]
df_r_f = df_r[(df_r['Марка'].isin(selected_marks)) & (df_r['ID Плавки'].isin(selected_ids))]
df_c_f = df_c[(df_c['Марка'].isin(selected_marks)) & (df_c['ID Плавки'].isin(selected_ids))]
df_sh_f = df_sh[(df_sh['Марка'].isin(selected_marks)) & (df_sh['ID Плавки'].isin(selected_ids))]

st.title("🏭 Мониторинг производственного цикла высокопрочной стали")
st.markdown(f"**Выбрано марок:** {', '.join(selected_marks)} | **Плавок в анализе:** {len(selected_ids)}")

# --- 1. MECE ТАБЛИЦА (ШАХМАТКА) ---
st.subheader("📅 Сводный MECE-баланс по датам")

def get_mece_matrix(ds, dr, dc, dsh):
    # Собираем все уникальные даты из всех этапов
    combined_dates = pd.concat([ds['Дата'], dr['Дата'], dc['Дата'], dsh['Дата']])
    all_dates = sorted(pd.to_datetime(combined_dates).unique())
    date_cols = [d.strftime('%d.%m.%Y') for d in all_dates]
    
    rows = ["Выплавлено", "Переходные и обрезь", "Годных слябов", "В рулонах", "В листах", "Н/С продукция", "Отгружено"]
    matrix = pd.DataFrame(index=rows, columns=date_cols).fillna("")

    for d in all_dates:
        d_str = d.strftime('%d.%m.%Y')
        d_iso = d.strftime('%Y-%m-%d')
        
        # Выплавка
        s_day = ds[pd.to_datetime(ds['Дата']) == d]
        if not s_day.empty:
            matrix.at["Выплавлено", d_str] = s_day['Масса, тн'].sum()
            matrix.at["Переходные и обрезь", d_str] = s_day[s_day['Признак годности'] == 'Переходные и обрезь']['Масса, тн'].sum()
            matrix.at["Годных слябов", d_str] = s_day[s_day['Признак годности'] == 'Годные']['Масса, тн'].sum()
            
        # Прокатка
        r_day = dr[pd.to_datetime(dr['Дата']) == d]
        if not r_day.empty:
            matrix.at["В рулонах", d_str] = r_day[r_day['Признак годности'] == 'годные']['Масса, тн'].sum()
            matrix.at["Н/С продукция", d_str] = r_day[r_day['Признак годности'] == 'некондиция']['Масса, тн'].sum()
            
        # Порезка
        c_day = dc[pd.to_datetime(dc['Дата']) == d]
        if not c_day.empty:
            matrix.at["В листах", d_str] = c_day[c_day['Признак годности'] == 'годные']['Масса, тн'].sum()
            
        # Отгрузка
        sh_day = dsh[pd.to_datetime(dsh['Дата']) == d]
        if not sh_day.empty:
            matrix.at["Отгружено", d_str] = sh_day['Масса, тн'].sum()
            
    return matrix

st.table(get_mece_matrix(df_s_f, df_r_f, df_c_f, df_sh_f))

# --- 2. СОРТАМЕНТНЫЕ ТАБЛИЦЫ ---
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚜 Результаты прокатки")
    st.write("Сортаменты рулонов, полученные из слябов:")
    r_sort = df_r_f.groupby(['ID Плавки', 'Parent_Slab_ID', 'Coil_ID', 'Толщина, мм', 'Ширина, мм'])['Масса, тн'].sum().reset_index()
    st.dataframe(r_sort, hide_index=True, use_container_width=True)

with col2:
    st.subheader("✂️ Результаты порезки")
    st.write("Сортаменты листов (ТхШхД):")
    c_sort = df_c_f.groupby(['ID Плавки', 'Parent_Coil_ID', 'Толщина, мм', 'Ширина, мм', 'Длина, мм'])['Масса, тн'].sum().reset_index()
    st.dataframe(c_sort, hide_index=True, use_container_width=True)

# --- 3. ДЕТАЛЬНЫЕ БАЗЫ ---
with st.expander("📂 Посмотреть исходные данные (все транзакции)"):
    t1, t2, t3, t4 = st.tabs(["Выплавка", "Прокатка", "Порезка", "Отгрузка"])
    t1.write(df_s_f)
    t2.write(df_r_f)
    t3.write(df_c_f)
    t4.write(df_sh_f)
