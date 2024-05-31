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
with open(r'C:/Users/geosimlab/Documents/Igor/sample_gtfs/separated double stops/stops.txt', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    next(reader, None)  # Пропускаем заголовок
    for row in reader:
        stop_id = int(row[0])
        latitude = float(row[4])  # Широта
        longitude = float(row[5])  # Долгота
        x_meter, y_meter = transformer.transform(longitude, latitude)
        points.append((stop_id, Point(x_meter, y_meter)))  

points_copy = gpd.GeoDataFrame(points, columns=['stop_id', 'geometry'], crs=web_mercator)

points_layer = gpd.read_file(r"C:/Users/geosimlab/Documents/Igor/qgis_prj/foot road TLV/TLV_centroids/TLV_centroids.shp").to_crs(web_mercator)



points_layer = points_layer.to_crs('EPSG:2039')
points_layer['centroid_calc'] = points_layer.geometry.centroid



idx_centroids = index.Index()
for i, centroid in enumerate(points_layer.centroid_calc):
    idx_centroids.insert(i, centroid.bounds)


print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# Создайте пустой список для ближайших пар
close_pairs = []

current_combination = 0
# Найди пары здание - остановка 

for i, geom in enumerate(points_copy.geometry):
    nearest_centroids = idx_centroids.intersection(geom.buffer(400).bounds)
    for j in nearest_centroids:
        current_combination = current_combination + 1
        if current_combination%100 == 0:
            print(f'Processing combination build<->stop {current_combination}', end='\r')
        stop_id1 = points_copy.iloc[i]['stop_id']
        distance = geom.distance(points_layer.iloc[j].centroid_calc)
        if distance <= 400:
            close_pairs.append((points_layer.iloc[j]['osm_id'], stop_id1, round(distance))) 

idx_stops = index.Index()
for i, geom in enumerate(points_copy.geometry):
    idx_stops.insert(i, geom.bounds)
print("idx_stops finish")

# Найди пары остановок
for i, geom in enumerate(points_copy.geometry):
    nearest_stops = idx_stops.intersection(geom.buffer(400).bounds)
    for j in nearest_stops:
        current_combination = current_combination + 1
        if current_combination%100 == 0:
            print(f'Processing combination stop<->stop {current_combination}', end='\r')
        stop_id1 = points_copy.iloc[i]['stop_id']
        distance = geom.distance(points_copy.iloc[j]['geometry'])
        if distance <= 400 and points_copy.iloc[j]['stop_id'] != stop_id1:
            close_pairs.append((points_copy.iloc[j]['stop_id'], stop_id1, round(distance))) 


            
print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


with open(r'c:/temp/footpath_AIR.txt', 'w') as file:
    file.write(f'from_stop_id,to_stop_id,min_transfer_time\n')
    for pair in close_pairs:
        id_from_points_layer = pair[0]
        stop_id1 = pair[1]
        distance = pair[2]
        file.write(f'{id_from_points_layer},{stop_id1},{distance}\n')
        file.write(f'{stop_id1},{id_from_points_layer},{distance}\n')
print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
