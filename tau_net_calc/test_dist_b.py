import csv
import pyproj
import geopandas as gpd
from shapely.geometry import Point
from rtree import index
import datetime

wgs84 = pyproj.CRS('EPSG:4326')  # WGS 84
web_mercator = pyproj.CRS('EPSG:2039')  # Web Mercator
transformer = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)

# Загрузите данные из файла stops.txt в GeoDataFrame
points = []
with open(r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\full gtfs\stops.txt', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader, None)  # Пропускаем заголовок
    for row in reader:
        stop_id = int(row[0])
        latitude = float(row[4])  # Широта
        longitude = float(row[5])  # Долгота
        x_meter, y_meter = transformer.transform(longitude, latitude)
        points.append((stop_id, Point(x_meter, y_meter)))  

points_copy = gpd.GeoDataFrame(points, columns=['stop_id', 'geometry'], crs=web_mercator)

print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("load start")
points_layer = gpd.read_file(r'C:\Users\geosimlab\Documents\Igor\qgis_prj\israel-and-palestine-240502\gis_osm_buildings_a_free_1.shp')
print("load finished")

print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("to_crs start")
points_layer = points_layer.to_crs('EPSG:2039')
print("to_crs finish")

print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("centroid start")
points_layer['centroid_calc'] = points_layer.geometry.centroid
print("centroid finish")

print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("idx_centroids start")
idx_centroids = index.Index()
for i, centroid in enumerate(points_layer.centroid_calc):
    idx_centroids.insert(i, centroid.bounds)
print("idx_centroids finish")

print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# Создайте пустой список для ближайших пар
close_pairs = []

current_combination = 0
# Найдите ближайшие пары точек
for i, geom in enumerate(points_copy.geometry):
    nearest_centroids = idx_centroids.intersection(geom.buffer(400).bounds)
    for j in nearest_centroids:
        current_combination = current_combination + 1
        print(f'Processing combination {current_combination}', end='\r')
        stop_id1 = points_copy.iloc[i]['stop_id']
        distance = geom.distance(points_layer.iloc[j].centroid_calc) 
        close_pairs.append((points_layer.iloc[j]['osm_id'], stop_id1, round(distance))) 
print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


with open(r'c:\temp\close_pairs.txt', 'w') as file:
    file.write(f'from_stop_id,to_stop_id,min_transfer_time\n')
    for pair in close_pairs:
        id_from_points_layer = pair[0]
        stop_id1 = pair[1]
        distance = pair[2]
        file.write(f'{id_from_points_layer},{stop_id1},{distance}\n')
print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
