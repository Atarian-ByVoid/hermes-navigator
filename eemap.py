# import geemap
# import ee

# ee.Initialize()

# Map = geemap.Map(center=[0, 0], zoom=2)

# dataset = ee.ImageCollection('MODIS/006/MOD11A2').filterDate('2020-01-01', '2020-12-31')
# temp_day = dataset.select('LST_Day_1km')

# temp_mean = temp_day.mean().multiply(0.02).subtract(273.15)

# Map.addLayer(temp_mean, {'min': 20, 'max': 40, 'palette': ['blue', 'green', 'red']}, 'Mean Temp')

# Map.to_html("mapa_interativo.html")


# API GOOGLE EARTH - DISABLED