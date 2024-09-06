import logging
from flask import Flask, request, jsonify
import folium
import pandas as pd
import matplotlib.pyplot as plt
import branca
from io import BytesIO
import base64
from py_eureka_client import eureka_client
import threading
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

EUREKA_SERVER = 'http://localhost:8761/eureka/'
SERVICE_NAME = 'hermes-navigator'
SERVICE_PORT = 5000
INSTANCE_IP = '127.0.0.1'

MONGO_URI = "mongodb://admin:admin123@localhost:27017/?authSource=admin"
client = MongoClient(MONGO_URI)
db = client['mongo_container']
logs_collection = db['atlas']

def log_request(user, document, data):
    log_data = {
        "user": user,
        "document": document,
        "data": data,
        "timestamp": datetime.utcnow()
    }
    
    logs_collection.insert_one(log_data)
    
    logging.info(f"Usuário: {user}, Documento: {document}, Dados: {data}")

def start_eureka():
    eureka_client.init(
        app_name=SERVICE_NAME,
        instance_ip=INSTANCE_IP,
        instance_port=SERVICE_PORT,
        eureka_server=EUREKA_SERVER,
    )

eureka_thread = threading.Thread(target=start_eureka)
eureka_thread.daemon = True
eureka_thread.start()

def gerar_grafico(cidade, populacao):
    fig, ax = plt.subplots()
    ax.bar([cidade], [populacao], color='skyblue')
    ax.set_ylabel('População')
    ax.set_title(f'População de {cidade}')
    
    buf = BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    img_html = f'<img src="data:image/png;base64,{img_base64}"/>'
    
    return img_html

@app.route('/map-population', methods=['POST'])
def generate_map():
    data = request.get_json()

    if not data or 'user' not in data or 'document' not in data:
        return jsonify({'error': 'Dados inválidos. Enviar "user", "document" e "cities_data".'}), 400
    
    user = data['user']
    document = data['document']
    cities_data = data.get('cities_data')

    if not isinstance(cities_data, list) or not all('Cidade' in city and 'Latitude' in city and 'Longitude' in city and 'População' in city for city in cities_data):
        return jsonify({'error': 'Dados inválidos. O objeto precisa conter uma lista com cidade, latitude, longitude e população.'}), 400

    log_request(user, document, cities_data)

    df = pd.DataFrame(cities_data)
    mapa = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=5)

    for index, row in df.iterrows():
        grafico_html = gerar_grafico(row['Cidade'], row['População'])
        
        popup = folium.Popup(branca.element.IFrame(html=grafico_html, width=400, height=300), max_width=500)
        
        folium.Marker([row['Latitude'], row['Longitude']], popup=popup).add_to(mapa)

    file_path = "mapa_multiplas_cidades_com_graficos.html"
    mapa.save(file_path)

    return jsonify({"message": "Mapa gerado com gráficos", "file": file_path}), 200

if __name__ == '__main__':
    app.run(host=INSTANCE_IP, port=SERVICE_PORT)
