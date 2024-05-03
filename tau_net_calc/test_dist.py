import csv
import pyproj
import geopandas as gpd
from shapely.geometry import Point
from rtree import index
from itertools import combinations

# Создаем объекты CRS и Transformer до начала цикла
wgs84 = pyproj.CRS('EPSG:4326')  # WGS 84
web_mercator = pyproj.CRS('EPSG:2039')  # Web Mercator
transformer = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)

# Открываем файл и читаем его содержимое
with open(r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\full gtfs\stops.txt', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    header = next(reader, None)  # Пропускаем заголовок и сохраняем его
    
    # Создаем пустой список для хранения точек
    points = []
    
    for row in reader:

                stop_id = int(row[0])
                latitude = float(row[4])  # Широта
                longitude = float(row[5])  # Долгота
                # Преобразуем координаты из градусов в метры
                            
                x_meter, y_meter = transformer.transform(longitude, latitude)
                points.append((stop_id, Point(x_meter, y_meter)))  # Добавляем объект Point в список
        

# Создаем геопандасовский DataFrame из списка точек
points_copy = gpd.GeoDataFrame(points, columns=['stop_id', 'geometry'], crs=web_mercator)

# Создаем пустой индекс R-tree
idx = index.Index()
for i, geom in enumerate(points_copy.geometry):
    idx.insert(i, geom.bounds)

# Создаем пустой список для ближайших пар
close_pairs = []

# Получаем общее количество комбинаций точек для отображения процесса
total_combinations = len(points_copy) * (len(points_copy) - 1) // 2
current_combination = 0

# Находим ближайшие пары точек
for i, geom in enumerate(points_copy.geometry):
    nearest_neighbors = idx.intersection(geom.buffer(400).bounds)
    for j in nearest_neighbors:
        if i < j:
            current_combination += 1
            print(f'Processing combination {current_combination} of {total_combinations}', end='\r')

            stop_id1 = points_copy.iloc[i]['stop_id']
            stop_id2 = points_copy.iloc[j]['stop_id']
            distance = geom.distance(points_copy.geometry[j])
            if distance < 400:
                close_pairs.append((stop_id1, stop_id2, round(distance)))

# Сохраняем найденные пары в файл
with open(r'c:\temp\close_pairs.txt', 'w') as file:
    file.write(f'from_stop_id,to_stop_id,min_transfer_time\n')
    for pair in close_pairs:
        stop_id1 = pair[0]
        stop_id2 = pair[1]
        distance = pair[2]
        file.write(f'{stop_id1},{stop_id2},{distance}\n')
        file.write(f'{stop_id2},{stop_id1},{distance}\n')
