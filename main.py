import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.title('Анализ температурных данных и мониторинг текущей температуры')
st.write('Статистика по историческим данным.')
st.header("Анализ данных")
st.subheader('Загрузка данных')

upload_file = st.file_uploader("Загрузите файл", type=['csv'])

if upload_file is not None:
    df = pd.read_csv(upload_file)

    required_columns = ['timestamp', 'city', 'season', 'temperature']
    if not all(col in df.columns for col in required_columns):
        st.error("Файл должен содержать столбцы: " + ", ".join(required_columns))
        st.stop()

    st.dataframe(df)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['rolling_mean_temperature'] = df.groupby(['city', 'season'])['temperature'].transform(lambda x: x.rolling(window=30).mean())
df['rolling_mean_temperature'] = df['rolling_mean_temperature'].fillna(df['temperature'])
temp_data = df.groupby(['city', 'season'])['rolling_mean_temperature'].agg(['mean', 'std']).reset_index()
df = df.merge(temp_data, on=['city', 'season'])

df['lower'] = df['mean'] - 2 * df['std']
df['upper'] = df['mean'] + 2 * df['std']
df['anomaly'] = (df['temperature'] < df['lower']) | (df['temperature'] > df['upper'])
unique_cities = df['city'].unique().tolist()
selected_city = st.selectbox('Выберите город:', [''] + unique_cities)

if selected_city:
    filter_df = df[df['city'] == selected_city].reset_index(drop=True)

    descriptive_stats = filter_df['temperature'].describe()
    st.subheader('статистика')
    st.table(descriptive_stats)

    st.subheader(f'Данные по городу:')
    st.dataframe(filter_df)

    filter_df['year'] = pd.to_datetime(filter_df['timestamp']).dt.year

    season_colors = {
        'winter': 'blue',
        'spring': 'purple',
        'summer': 'green',
        'autumn': 'yellow'
    }

    seasons_list = filter_df['season'].unique()
    years_list = filter_df['year'].unique()

    st.subheader("Временной ряд температур")

    selected_years = st.multiselect("Год:", sorted(years_list), default=2010)

    default_season_index = list(seasons_list).index('spring')
    selected_season = st.selectbox("Сезон:", seasons_list, index=default_season_index)

    season_year_filtered_df = filter_df[(filter_df['season'] == selected_season) &
                                          (filter_df['year'].isin(selected_years))]

    fig = px.line(season_year_filtered_df, x='timestamp', y='temperature',
                  color='season',
                  color_discrete_map=season_colors,
                  title=f'Температурный ряд',
                  hover_data=['season'],
                  labels={'temperature': 'Температура', 'timestamp': 'Дата'})

    anomalies = season_year_filtered_df[season_year_filtered_df['anomaly']]
    fig.add_scatter(x=anomalies['timestamp'], y=anomalies['temperature'], mode='markers',
                    marker=dict(color='red', size=6), name='Аномалии',
                    hovertext=anomalies.apply(lambda row: f"{row['timestamp'].date()}: {row['temperature']}", axis=1))

    fig.update_layout(
        yaxis_title='Температура',
        xaxis_title='Дата',
        title=dict(x=0.5)
    )

    if len(selected_years) > 1:
        fig.update_layout(xaxis=dict(rangeslider=dict(visible=True), type='date'))
        st.write("Перемещайте ползунок")

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Профили температуры")
    st.write(selected_city)

    seasonal_stats = filter_df.groupby(['city', 'season']).agg({'temperature': ['mean', 'std']}).reset_index()
    seasonal_stats.columns = ['city', 'season', 'mean_temperature', 'std_temperature']

    # Получение текущей температуры
    st.subheader("Текущая температура")
    api_key = "API_KEY"
    if selected_city:
        response = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={selected_city}&appid={api_key}&units=metric")
        if response.status_code == 200:
            data = response.json()
            current_temp = data['main']['temp']
            st.write(f"Текущая температура в {selected_city}: {current_temp} °C")
        else:
            st.error("Не удалось получить данные.")
