from py_eureka_client import eureka_client

eureka_client.init(
    app_name='hermes-navigator', 
    instance_ip='127.0.0.1', 
    instance_port=5000, 
    eureka_server='http://localhost:8761/eureka/'  
)

try:
    import time
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    pass
finally:
    eureka_client.stop()
