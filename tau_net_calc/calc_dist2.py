import geopandas as gpd
from shapely.geometry import Point
from rtree import index
from itertools import combinations


points_layer = gpd.read_file(r'C:\Users\geosimlab\Documents\Igor\qgis_prj\haifa\stops_israel.shp')
points_copy = points_layer.copy()
points_copy = points_copy.to_crs('EPSG:2039')

print(points_copy.head())

"""
close_pairs = []


idx = index.Index()
for i, point in enumerate(points_copy.geometry):
    idx.insert(i, point.bounds)


total_combinations = len(points_copy) * (len(points_copy) - 1) // 2
current_combination = 0


for i, point in enumerate(points_copy.geometry):
    nearest_neighbors = idx.intersection(point.buffer(400).bounds)
    for j in nearest_neighbors:
        if i < j:
            current_combination += 1
            print(f'Processing combination {current_combination} of {total_combinations}', end='\r')

            stop_id1 = points_copy.iloc[i]['stop_id']
            stop_id2 = points_copy.iloc[j]['stop_id']
            distance = point.distance(points_copy.geometry[j])
            if distance < 400:
                close_pairs.append((stop_id1, stop_id2, round(distance)))


with open(r'c:\temp\close_pairs.txt', 'w') as file:
    file.write(f'from_stop_id,to_stop_id,min_transfer_time\n')
    for pair in close_pairs:
        stop_id1 = pair[0]
        stop_id2 = pair[1]
        distance = pair[2]
        file.write(f'{stop_id1},{stop_id2},{distance}\n')
        file.write(f'{stop_id2},{stop_id1},{distance}\n')
"""