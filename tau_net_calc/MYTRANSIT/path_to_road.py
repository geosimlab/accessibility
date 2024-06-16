
from datetime import datetime
import csv
import pyproj

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsGeometry, QgsWkbTypes, QgsPointXY, QgsPoint
import geopandas as gpd
import networkx as nx
from shapely.geometry import LineString
from scipy.spatial import KDTree



class path_to_road:
    def __init__(self, parent, road_layer, layer_origins, path_to_protocol):
        
        self.path_to_protocol = path_to_protocol
        self.road_layer = road_layer
        self.layer_origins = layer_origins
        self.parent = parent


    def create_stops_gpd(self):
        wgs84 = pyproj.CRS('EPSG:4326')  # WGS 84
        web_mercator = pyproj.CRS('EPSG:2039')  # Web Mercator
        transformer = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)

        points = []
    
        #filename = self.__path_to_file + 'stops.txt'
        filename = self.path_to_protocol + 'stops.txt'
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader, None)  # Пропускаем заголовок
            for row in reader:
                stop_id = int(row[0])
                latitude = float(row[4])  # Широта
                longitude = float(row[5])  # Долгота
                x_meter, y_meter = transformer.transform(longitude, latitude)
                qgs_point = QgsPointXY(x_meter, y_meter)
                points.append((stop_id, qgs_point))  

        # Преобразование точек в GeoDataFrame
        points_copy = gpd.GeoDataFrame(points, columns=['stop_id', 'geometry'])
    
        return points_copy
        
    
       
    def find_shortest_paths(self, mode):
        

        node_pairs = []

        if mode == 1: # buildings to stops
            features = self.layer_origins.getFeatures()
            features_list = list(features)
            count = len(features_list)
        
        if mode == 2: # stops to stops
            features = self.stops.itertuples(index=False)
            features_list = list(features)
            count = len(features_list)

        
        
        self.parent.progressBar.setMaximum(count)
        self.parent.progressBar.setValue(1)
        
        i =  0
        
                
        for feature  in features_list:
            QApplication.processEvents()
            if self.verify_break():
                return 0
            i += 1

            #if i == 1000:
            #    break
                        
            self.parent.progressBar.setValue(i+3)
            self.parent.setMessage(f'Calc point №{i} from {count}')
            
            if mode == 1:
                self.source = feature['osm_id']
            else:
                self.source = feature.stop_id
            
            to_stop_tuples = self.dict_b_s.get(self.source, [])  # Получаем список кортежей для текущего building_osm_id
            
            if not to_stop_tuples:
                continue

            to_stop_ids = {stop_id for stop_id, _ in to_stop_tuples}
            filtered_stops = self.stops[self.stops['stop_id'].isin(to_stop_ids)]

            if not filtered_stops.empty:
                if mode == 1:
                    geometry = feature.geometry()
                    points = [geometry.asPoint()]
                    self.pStart = points[0]
                    idStart = self.find_nearest_node(self.pStart)
                else:
                    self.pStart = feature.geometry
                    idStart = self.find_nearest_node(self.pStart)
                
            else:
                continue

            for row in filtered_stops.itertuples(index=False):
                self.desination = row.stop_id
                self.pEnd = row.geometry    
                            
                idEnd = self.find_nearest_node(self.pEnd)

                try:
                    #distance = nx.dijkstra_path_length(self.graph, idStart, idEnd, weight='length')
                    distance = nx.shortest_path_length(self.graph, idStart, idEnd, weight='length')
                   
                except:
                    continue

                if distance <= 400:        
                    node_pairs.append((self.source, self.desination, round(distance)))
        
        return node_pairs        
                

    def calculate_edge_length(self, edge):
        line = LineString(edge)
        return line.length

    
    def build_graph(self, roads):
        self.graph = nx.Graph()

        for feature in roads.getFeatures():
            geometry = feature.geometry()

            if geometry.wkbType() == QgsWkbTypes.MultiLineString or geometry.wkbType() == QgsWkbTypes.LineString:
                if geometry.wkbType() == QgsWkbTypes.MultiLineString:
                    for line in geometry.asMultiPolyline():
                        self.add_line_to_graph(line)
                else:
                    self.add_line_to_graph(geometry.asPolyline())
        
        self.build_index_graph ()

        return self.graph 
    
    def build_index_graph(self):
        self.nodes = list(self.graph.nodes)
        node_positions = [(x, y) for x, y in self.nodes]
        self.kd_tree = KDTree(node_positions)

    def add_line_to_graph(self, line):
        num_points = len(line)
        length = QgsGeometry.fromPolyline([QgsPoint(point.x(), point.y()) for point in line]).length()  # Length of the line
        for point in line:
            self.graph.add_node((point[0], point[1]))

        for i in range(num_points - 1):
            point1 = line[i]
            point2 = line[i + 1]
            self.graph.add_edge((point1[0], point1[1]), (point2[0], point2[1]), length=length)                     

    # use it!! 
    def find_nearest_node(self, geometry):
       
        nearest_point_coords = (geometry.x(), geometry.y())
        _, nearest_node_idx = self.kd_tree.query(nearest_point_coords)
        nearest_node = self.nodes[nearest_node_idx]
        return nearest_node
   
    
    def getDateTime(self):
        current_datetime = datetime.now()
        year = current_datetime.year
        month = str(current_datetime.month).zfill(2)
        day = str(current_datetime.day).zfill(2)
        hour = str(current_datetime.hour).zfill(2)
        minute = str(current_datetime.minute).zfill(2)
        second = str(current_datetime.second).zfill(2)
        return f'{year}{month}{day}_{hour}{minute}{second}'
    
    def create_head_files(self):

        table_header = "from_stop_id,to_stop_id,min_transfer_time\n"
        self.folder_name = f'{self.path_to_protocol}'
        self.f = f'{self.folder_name}footpath_road.txt'
                
        with open(self.f, 'w') as self.filetowrite:
            self.filetowrite.write(table_header)  

    # Creating dict {[buildings] : {stops}} on base pre-preparing file with distance
    def create_dict_b_s (self):
    
        self.dict_b_s = {}
        count_dict = 0
        with open(self.path_to_protocol+'footpath_AIR.txt', 'r') as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                from_stop_id, to_stop_id, dist = row
                #if int(dist) >= 150 and int(dist) <= 200:
                count_dict = count_dict + 1
                if count_dict%1000 == 0:
                    QApplication.processEvents()
                if from_stop_id not in self.dict_b_s:
                        self.dict_b_s[from_stop_id] = []
                self.dict_b_s[from_stop_id].append((to_stop_id, dist))
        

    def run(self):
        
        self.parent.textLog.append(f'<a>Starting calculating foot path on road</a>')
        
        self.create_head_files()

        

        self.parent.setMessage('Loadings stops.txt  ...')
        QApplication.processEvents()
        self.stops = self.create_stops_gpd()
        self.stops['stop_id'] = self.stops['stop_id'].astype(str)

        self.parent.setMessage('Making dictionary buildings: {stops}  ...')
        self.create_dict_b_s()

        QApplication.processEvents()
        self.parent.setMessage(f'Making graph ...')
        self.graph = self.build_graph(self.road_layer)
        
        QApplication.processEvents()
        time1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.parent.textLog.append(f'<a>Time after Making graph {time1}</a>') 
        
        
        pairs_b_to_b = self.find_shortest_paths(mode = 1)
        pairs_s_to_b = self.find_shortest_paths(mode = 2)

        with open(self.f, 'a') as file:
            if pairs_b_to_b:
                for id_source, id_destination, dist in pairs_b_to_b:
                    file.write(f'{id_source},{id_destination},{dist}\n')
                    file.write(f'{id_destination},{id_source},{dist}\n')
            
            if pairs_s_to_b:
                for id_source, id_destination, dist in pairs_s_to_b:
                    file.write(f'{id_source},{id_destination},{dist}\n')
                    file.write(f'{id_destination},{id_source},{dist}\n')

        self.parent.setMessage(f'Calculating foot path on road done')
        QApplication.processEvents()
        

        

    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("Process calculation foot path on road is break")
            self.parent.textLog.append (f'<a><b><font color="red">Process calculation foot path on road is break</font> </b></a>')
            self.parent.progressBar.setValue(0)  
            return True
      return False   

    