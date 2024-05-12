import networkx as nx
import geopandas as gpd
from shapely.geometry import LineString
import pyproj
import csv
import datetime

from scipy.spatial import cKDTree


wgs84 = pyproj.CRS('EPSG:4326')  # WGS 84
web_mercator = pyproj.CRS('EPSG:3857')  # Web Mercator
transformer = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)

# Функция для вычисления длины ребра на основе его геометрии
def calculate_edge_length(edge):
    line = LineString(edge)
    return line.length

# Функция для построения графа из геометрии дорог
def build_graph(roads):
    graph = nx.Graph()
    for line in roads.geometry:
        edge_length = calculate_edge_length(line.coords)
        start_node = line.coords[0]
        end_node = line.coords[-1]
        graph.add_edge(start_node, end_node, length=edge_length)
    return graph

def find_nearest_node(graph, geometry):
    nearest_point = geometry.representative_point()  # Получаем центр геометрии
    nearest_node = None
    _, nearest_node_idx = tree.query(nearest_point.coords[0])

    nearest_node = graph_nodes[nearest_node_idx]
    
    return nearest_node

def find_node_pairs(graph, buildings, stops, Dist):
    node_pairs = []
    total_iterations = len(buildings) * len(stops)
    i = 1
    for _, building in buildings.iterrows():
        node_b = find_nearest_node(graph, building.geometry)

        building_osm_id = building['osm_id']

        #to_stop_ids = dict_b_s.get(building_osm_id, set())  
        #print (f'to_stop_ids {to_stop_ids}')
        #filtered_stops = stops[stops['stop_id'].isin(to_stop_ids)]

        to_stop_tuples = dict_b_s.get(building_osm_id, [])  # Получаем список кортежей для текущего building_osm_id
        to_stop_ids = [stop_id for stop_id, _ in to_stop_tuples]  # Извлекаем только to_stop_id
        #print (f'to_stop_ids {to_stop_ids}')
        filtered_stops = stops[stops['stop_id'].isin(to_stop_ids)]
                
        for _, stop in filtered_stops.iterrows():
                i += 1
                #if i>20000:
                #    return node_pairs
            
                print(f'Processing {i} out of {total_iterations}', end='\r')
                node_s = find_nearest_node(graph, stop.geometry)
            
                try:
                    dist = nx.shortest_path_length(graph, source=node_b, target=node_s, weight='length')
                except:
                    continue
                
                if True: #dist <= Dist:
                    
                    stop_id = stop['stop_id']

                    tuples_list = dict_b_s[building_osm_id]
                    for to_stop_id_val, dist_val in tuples_list:
                        if to_stop_id_val == stop_id:
                            dist_air = int(dist_val)
                            break

                    if dist > dist_air*2:

                        node_pairs.append((node_b, building_osm_id, node_s, stop_id, round(dist)))
    
    return node_pairs

# Загрузка данных
roads = gpd.read_file(r"C:\Users\geosimlab\Documents\Igor\qgis_prj\foot road TLV\TLV_ROAD_HEB\OSM_ROADS_EXTENDED.shp").to_crs(web_mercator)
print('Roads loaded')
buildings = gpd.read_file(r"C:\Users\geosimlab\Documents\Igor\qgis_prj\foot road TLV\TLV_centroids\TLV_centroids.shp").to_crs(web_mercator)
print('Buildings loaded')
stops = gpd.read_file(r"C:\Users\geosimlab\Documents\Igor\qgis_prj\foot road TLV\TLV_stops\stops.shp").to_crs(web_mercator)
print('Stops loaded')
Dist = 400  # Предполагаемое максимальное расстояние между узлами

# Creating dict {[buildings] : {stops}} on base pre-preparing file with distance
dict_b_s = {}
count_dict = 0
with open(r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\!!!\b s TLV on AIR.txt', 'r') as file:
    reader = csv.reader(file)
    next(reader)
    for row in reader:
        from_stop_id, to_stop_id, dist = row
        if int(dist) >= 150 and int(dist) <= 200:
            count_dict =count_dict + 1
            if from_stop_id not in dict_b_s:
                dict_b_s[from_stop_id] = []
            dict_b_s[from_stop_id].append((to_stop_id, dist))
print(f'Dict created. Count item {count_dict}')


# Создание графа из геометрии дорог
graph = build_graph(roads)
graph_nodes = list(graph.nodes)
node_coords = [node for node in graph_nodes]  # Получаем координаты узлов
# Строим пространственный индекс
tree = cKDTree(node_coords)

print('Graph builded')

print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# Поиск пар узлов
node_pairs = find_node_pairs(graph, buildings, stops, Dist)
print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# Вывод результатов
with open(r'c:\temp\close_pairs_road.txt', 'w') as file:
    file.write(f'from_stop_id,to_stop_id,min_transfer_time\n')
    for node_b, building_osm_id, node_s, stop_id, dist in node_pairs:
        file.write(f'{building_osm_id},{stop_id},{dist}\n')
        
