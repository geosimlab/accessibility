import geopandas as gpd
import networkx as nx
from shapely.ops import nearest_points, split
from shapely.geometry import LineString, Point

# Загрузка данных
roads = gpd.read_file(r"C:\Users\geosimlab\Documents\Igor\qgis_prj\foot road TLV\TLV_ROAD_HEB\OSM_ROADS_EXTENDED.shp")
print('Roads loaded')
buildings = gpd.read_file(r"C:\Users\geosimlab\Documents\Igor\qgis_prj\foot road TLV\TLV_centroids\TLV_centroids.shp")
print('Buildings loaded')
stops = gpd.read_file(r"C:\Users\geosimlab\Documents\Igor\qgis_prj\foot road TLV\TLV_stops\stops.shp")
print('Stops loaded')

print('Graph road started')
# Построение графа дорог
G = nx.Graph()
for index, road in roads.iterrows():
    coords = list(road.geometry.coords)
    for i in range(len(coords) - 1):
        u, v = coords[i], coords[i + 1]
        length = road.geometry.length
        G.add_edge(u, v, length=length)

print('Graph road finished')

out = nx.single_source_dijkstra_path_length(G, 1199373028, cutoff=None)


"""
# Нахождение ближайшего узла на графе для каждого здания и остановки
#for index, building in buildings.iterrows():
for index, building in buildings.head(3).iterrows():
    print(f'Processing building {index + 1} out of {len(buildings)}')
    point = building.geometry
    nearest_edge = min(G.edges, key=lambda edge: point.distance(LineString(edge)))
    nearest_edge_line = LineString(nearest_edge)
    split_point = nearest_points(point, nearest_edge_line)[0]
    split_lines = split(nearest_edge_line, split_point)
    split_line = split_lines.geoms[0]  # Выбираем первый сегмент
    nearest_node = min(G.nodes, key=lambda node: point.distance(Point(node)))  # Ближайший узел к начальной точке линии
    
    for index, stop in stops.iterrows():
        if not G.has_node(stop.geometry):
            print(f"No node found for stop {index + 1}, skipping...")
            continue
        print(f'Calculating shortest path from building to stop {index + 1} out of {len(stops)}')
        shortest_path = nx.shortest_path(G, nearest_node, stop.geometry)
        shortest_path_length = nx.shortest_path_length(G, nearest_node, stop.geometry)
        print(f"Кратчайший путь от здания к остановке: {shortest_path}")
        print(f"Длина пути: {shortest_path_length}")
"""


