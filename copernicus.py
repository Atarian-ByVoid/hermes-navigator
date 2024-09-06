import logging
import os
import cdsapi
import pygrib
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from flask import Flask, request, send_file, jsonify
from pymongo import MongoClient
from py_eureka_client import eureka_client
import threading
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import matplotlib
matplotlib.use('Agg')

app = Flask(__name__)

EUREKA_SERVER = 'http://localhost:8761/eureka/'
SERVICE_NAME = 'hermes-navigator'
SERVICE_PORT = 5000
INSTANCE_IP = '127.0.0.1'

MONGO_URI = "mongodb://admin:admin123@localhost:27017/?authSource=admin"
client = MongoClient(MONGO_URI)
db = client['mongo_container']
logs_collection = db['copernicus']

def log_request(user, document, request_data):
    log_data = {
        "user": user,
        "document": document,
        "request_data": request_data,
        "timestamp": datetime.utcnow()
    }
    
    logs_collection.insert_one(log_data)
    logging.info(f"Usuário: {user}, Documento: {document}, Dados: {request_data}")

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

@app.route('/temperature-map', methods=['POST'])
def generate_temperature_map():
    try:
        data = request.get_json()
        year = data.get('year', '2008')
        month = data.get('month', '01')
        day = data.get('day', '01')
        time = data.get('time', '12:00')
        pressure_level = data.get('pressure_level', '1000')

        user = data.get('user', 'unknown_user')
        document = data.get('document', 'unknown_document')

        log_request(user, document, {
            "year": year,
            "month": month,
            "day": day,
            "time": time,
            "pressure_level": pressure_level
        })

        c = cdsapi.Client()
        grib_file = "temperature-map/temperature_map.grib"
        os.makedirs(os.path.dirname(grib_file), exist_ok=True)

        c.retrieve(
            "reanalysis-era5-pressure-levels",
            {
                "variable": "temperature",
                "pressure_level": pressure_level,
                "product_type": "reanalysis",
                "year": year,
                "month": month,
                "day": day,
                "time": time,
                "format": "grib"
            },
            grib_file
        )

        grbs = pygrib.open(grib_file)
        grb = grbs.select(name='Temperature')[0]

        temperature_data = grb.values
        lats, lons = grb.latlons()

        plt.figure(figsize=(10, 6))
        plt.contourf(lons, lats, temperature_data, cmap='coolwarm')
        plt.title(f'Temperatura no Nível de Pressão de {pressure_level} hPa ({year}/{month}/{day} {time})')
        plt.colorbar(label='Temperatura (K)')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')

        buf = BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)

        file_path = "temperature-map/temperature_map.png"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(buf.getvalue())

        os.remove(grib_file)

        return send_file(file_path, mimetype='image/png', as_attachment=True, download_name='temperature_map.png'), 200

    except Exception as e:
        logging.error(f"Erro ao gerar o mapa de temperatura: {str(e)}")
        return jsonify({"error": "Erro ao gerar o mapa de temperatura"}), 500

if __name__ == '__main__':
    app.run(host=INSTANCE_IP, port=SERVICE_PORT)
