import streamlit as st
import streamlit_folium as st_folium
import folium
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
import numpy as np
import sqlite3
import requests
import math
import cx_Oracle
import arrow

# Configurações do Oracle DB (modifique de acordo com suas configurações)
lib_dir = r"D:\oracle\instantclient_21_12"
dsn = cx_Oracle.makedsn("oracle.fiap.com.br", 1521, service_name="orcl")

def create_oracle_connection():
    cx_Oracle.init_oracle_client(lib_dir=lib_dir)
    return cx_Oracle.connect(user="rm99150", password="180101", dsn=dsn)

# Inicializar o banco de dados
def init_db():
    conn = sqlite3.connect('lixo.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL,
            longitude REAL,
            quantidade_lixo INTEGER,
            tipo_lixo TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_data(latitude, longitude, quantidade_lixo, tipo_lixo):
    conn = sqlite3.connect('lixo.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO registros (latitude, longitude, quantidade_lixo, tipo_lixo)
        VALUES (?, ?, ?, ?)
    ''', (latitude, longitude, quantidade_lixo, tipo_lixo))
    conn.commit()
    conn.close()

def get_weather_forecast(latitude, longitude, days):
    start = arrow.now().floor('day')
    end = start.shift(days=+days).ceil('day')
    
    response = requests.get(
        'https://api.stormglass.io/v2/weather/point',
        params={
            'lat': latitude,
            'lng': longitude,
            'params': ','.join(['waveHeight', 'airTemperature', 'windSpeed', 'windDirection']),
            'start': start.to('UTC').timestamp(),
            'end': end.to('UTC').timestamp()
        },
        headers={
            'Authorization': '41bc7fea-22cf-11ef-9acf-0242ac130004-41bc8166-22cf-11ef-9acf-0242ac130004'
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_latest_data():
    conn = sqlite3.connect('lixo.db')
    c = conn.cursor()
    c.execute('SELECT latitude, longitude, quantidade_lixo FROM registros ORDER BY timestamp DESC LIMIT 1')
    data = c.fetchone()
    conn.close()
    if data:
        latitude, longitude, quantidade_lixo = data
        return latitude, longitude, quantidade_lixo
    return None

# Definir o modelo
input_shape = 2  # Latitude e Longitude
num_outputs = 1  # Quantidade de lixo

model = Sequential([
    Dense(64, activation='relu', input_shape=(input_shape,)),
    Dense(64, activation='relu'),
    Dense(num_outputs, activation='linear')
])

model.compile(optimizer='adam',
              loss='mean_squared_error',
              metrics=['mae'])

def train_model_with_db_data():
    data = get_latest_data()
    if data:
        train_data = np.array([[data[0], data[1]]])
        train_labels = np.array([[data[2]]])
        train_on_new_data(model, train_data, train_labels)

def train_on_new_data(model, new_data, new_labels):
    model.fit(new_data, new_labels, epochs=1, batch_size=32, verbose=0)

def request_user_location():
    # Função para pedir permissão de localização e obter coordenadas do usuário
    st.markdown("""
        <script>
        function getLocation() {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const latitude = position.coords.latitude;
                    const longitude = position.coords.longitude;
                    document.getElementById("user-coordinates").innerText = `${latitude},${longitude}`;
                }
            );
        }
        </script>
        <button onclick="getLocation()">Permitir localização</button>
        <p id="user-coordinates"></p>
    """, unsafe_allow_html=True)
    coords = st.experimental_get_query_params().get("user-coordinates", [None])[0]
    return coords.split(",") if coords else (None, None)

def main():
    init_db()

    st.title("Registro de Lixo nas Praias")

    st.header("Selecione o local no mapa")

    # Solicitar permissão de localização do usuário
    user_lat, user_lon = request_user_location()
    if user_lat and user_lon:
        map_center = [float(user_lat), float(user_lon)]
    else:
        map_center = [-14.2350, -51.9253]  # Centro do mapa no Brasil como fallback

    # Usar st.session_state para manter o estado do último clique no mapa
    if 'last_clicked' not in st.session_state:
        st.session_state['last_clicked'] = None

    if 'map_center' not in st.session_state:
        st.session_state['map_center'] = map_center

    # Usar st.session_state para manter o estado da previsão
    if 'prediction' not in st.session_state:
        st.session_state['prediction'] = None

    # Configurar o mapa com a localização padrão
    m = folium.Map(location=st.session_state['map_center'], zoom_start=10)
    
    # Adicionar evento de clique no mapa
    folium.LatLngPopup().add_to(m)

    # Exibir o mapa no Streamlit
    map_data = st_folium.st_folium(m, width=700, height=500)

    if map_data and map_data['last_clicked'] is not None:
        st.session_state['last_clicked'] = map_data['last_clicked']
    
    if st.session_state['last_clicked']:
        latitude = st.session_state['last_clicked']['lat']
        longitude = st.session_state['last_clicked']['lng']
        
        st.write(f"Latitude: {latitude}")
        st.write(f"Longitude: {longitude}")
        
        # Interface para o usuário inserir a quantidade de lixo
        quantidade_lixo = st.number_input("Quantidade de Lixo")
        tipo_lixo = st.text_input("Tipo de Lixo")
        
        if st.button("Registrar"):
            insert_data(latitude, longitude, quantidade_lixo, tipo_lixo)
            st.success("Registro de lixo atualizado com sucesso!")
            train_model_with_db_data()  # Treinar o modelo com os dados do banco de dados
    
    # Interface para o usuário selecionar a previsão para tantos dias
    days = st.slider("Dias para previsão", min_value=1, max_value=7, value=1)
    
    if st.button("Previsão"):
        latest_data = get_latest_data()
        if latest_data:
            lat, lon, lixo = latest_data
            weather_data = get_weather_forecast(lat, lon, days)
            if weather_data:
                wind_speed = weather_data['hours'][0]['windSpeed']['sg']
                wind_direction = weather_data['hours'][0]['windDirection']['sg']
                
                # Prever a nova posição do lixo com base na direção do vento
                new_latitude = lat + (math.sin(math.radians(wind_direction)) * wind_speed * 0.1)
                new_longitude = lon + (math.cos(math.radians(wind_direction)) * wind_speed * 0.1)
                
                st.write(f"Localização: ({lat}, {lon}) - Lixo registrado: {lixo} - Velocidade do vento: {wind_speed} m/s - Direção do vento: {wind_direction}°")
                st.write(f"Previsão de nova localização do lixo para {days} dia(s): ({new_latitude}, {new_longitude})")
                
                # Atualizar a previsão no estado
                st.session_state['prediction'] = {
                    'new_latitude': new_latitude,
                    'new_longitude': new_longitude,
                    'wind_speed': wind_speed,
                    'wind_direction': wind_direction,
                    'lixo': lixo,
                    'days': days
                }

                # Atualizar o mapa com a nova localização prevista
                m_prediction = folium.Map(location=[new_latitude, new_longitude], zoom_start=10)
                folium.Marker([new_latitude, new_longitude], popup="Nova posição do lixo").add_to(m_prediction)
                st_folium.st_folium(m_prediction, width=700, height=500)
            else:
                st.error("Não foi possível obter dados climáticos para a previsão.")
        else:
            st.error("Não há dados para fazer a previsão. Por favor, registre um novo local no mapa")

    # Exibir o mapa da previsão, se disponível
    if st.session_state['prediction']:
        pred = st.session_state['prediction']
        st.write(f"Previsão de nova localização do lixo para {pred['days']} dia(s): ({pred['new_latitude']}, {pred['new_longitude']})")
        m_prediction = folium.Map(location=[pred['new_latitude'], pred['new_longitude']], zoom_start=10)
        folium.Marker([pred['new_latitude'], pred['new_longitude']], popup="Nova posição do lixo").add_to(m_prediction)
        st_folium.st_folium(m_prediction, width=700, height=500)

if __name__ == "__main__":
    main()
