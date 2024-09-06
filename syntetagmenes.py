import logging
from flask import Flask, request, jsonify
import folium
from folium.plugins import HeatMap
import pandas as pd
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
logs_collection = db['syntetagmenes']

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

@app.route('/heatmap', methods=['POST'])
def generate_heatmap():
    data = request.get_json()

    if not data or 'user' not in data or 'document' not in data:
        return jsonify({'error': 'Dados inválidos. Enviar "user", "document", e "location_data".'}), 400
    
    user = data['user'] 
    document = data['document'] 
    location_data = data.get('location_data')  

    if not isinstance(location_data, list) or not all('latitude' in loc and 'longitude' in loc for loc in location_data):
        return jsonify({'error': 'Dados inválidos. O objeto precisa conter uma lista com latitude e longitude.'}), 400

    log_request(user, document, location_data)

    df = pd.DataFrame(location_data)
    mapa = folium.Map(location=[df['latitude'].mean(), df['longitude'].mean()], zoom_start=14)
    heat_data = [[row['latitude'], row['longitude']] for index, row in df.iterrows()]
    HeatMap(heat_data).add_to(mapa)

    mapa.save("heatmap/mapa_calor.html")

    return jsonify({"message": "Mapa de calor gerado", "file": "mapa_calor.html"}), 200

if __name__ == '__main__':
    app.run(host=INSTANCE_IP, port=SERVICE_PORT)
