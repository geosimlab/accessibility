from datetime import datetime
import csv
import pyproj

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsPointXY
import geopandas as gpd
import networkx as nx
from scipy.spatial import KDTree





class footpath_on_road:
    def __init__(self, parent, road_layer, layer_origins, path_to_protocol):
        
        self.path_to_protocol = path_to_protocol
        self.road_layer = road_layer
        self.layer_origins = layer_origins
        self.parent = parent
        self.count = 0
        self.already_display_break = False

        self.dict_feature_to_node = {}
        self.dict_feature_min_dist_to_finishstop = {}
        self.node_pairs = []


    def create_stops_gpd(self):
        wgs84 = pyproj.CRS('EPSG:4326')  # WGS 84
        web_mercator = pyproj.CRS('EPSG:2039')  # Web Mercator
        transformer = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)

        points = []
           
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
    
    def create_dict_node_to_feature (self) :
        """
        comment = 'vertex : nearest stops'

        features = list(self.stops.itertuples(index=False))
        features_coords = [(feature.geometry) for feature in features]
        count = len(self.graph.nodes)

        kdtree = KDTree(features_coords)
        
        nearby_features = {node: [] for node in self.graph.nodes}

        for i, node in enumerate(self.graph.nodes, start=1):
            i += 1
            if i % 1000 == 0:
                
                self.parent.setMessage(f'Peparing GTFS. Creating dict ({comment}). Calc node №{i} from {count}')
                QApplication.processEvents()

            node_point = Point(node)
            #indices = kdtree.query_ball_point((node_point.x, node_point.y), 500)
            #nearby_features[node] = [features[idx].stop_id for idx in indices]
            distance, index = kdtree.query((node_point.x, node_point.y))
            nearby_features[node] = features[index].stop_id

        return nearby_features
        """
        comment = 'vertex : nearest stops'
        features = list(self.stops.itertuples(index=False))
        len_features = len(features)
        # Создаем список координат узлов графа
        graph_nodes_coords = [(node[0], node[1]) for node in self.graph.nodes]
        kdtree = KDTree(graph_nodes_coords)
    
        nearby_features = {node: [] for node in self.graph.nodes}

        for i, feature in enumerate(features, start=1):
            if i % 1000 == 0:
                self.parent.setMessage(f'Preparing GTFS. Calc footpath on road. Creating dict ({comment}). Calc feature №{i} from {len_features}')
                QApplication.processEvents()

            
            feature_point = feature.geometry
                        
            # Находим ближайший узел для данной остановки
            _, index = kdtree.query((feature_point.x(), feature_point.y()))
            nearest_node = graph_nodes_coords[index]
            nearby_features[nearest_node] = feature.stop_id

        return nearby_features
        
    def create_dict_feature_to_node (self, mode) :

        

        if mode == 1: # buildings to stops
            features = self.layer_origins.getFeatures()
            features_list = list(features)
            count = len(features_list)
            comment = 'building : {nearest vertex, dist}'
        
        if mode == 2: # stops to stops
            features = self.stops.itertuples(index=False)
            features_list = list(features)
            count = len(features_list)
            comment = 'stop : {nearest vertex, dist}'

        i = 0

        for feature  in features_list:
            i += 1
            if i%10000 == 0:
                self.parent.setMessage(f'Preparing GTFS. Calc footpath on road. Creating dict ({comment}). Calc point №{i} from {count}')
                QApplication.processEvents()
                if self.verify_break():
                    return 0

            if mode == 1:
                geometry = feature.geometry()
                points = [geometry.asPoint()]
                pFeature = points[0]
                source = feature['osm_id']
            else:
                pFeature = feature.geometry
                source = feature.stop_id
                    
            idVertex, dist = self.find_nearest_node(pFeature)

            self.dict_feature_to_node[source] = [(idVertex, dist)]

        
        
    
    def create_dict_feature_min_dist_to_finishstop (self, mode) :

        

        if mode == 1: # buildings to stops
            features = self.layer_origins.getFeatures()
            features_list = list(features)
            count = len(features_list)
            comment = 'building : {min dist from vertex to finish stop}'
        
        if mode == 2: # stops to stops
            features = self.stops.itertuples(index=False)
            features_list = list(features)
            count = len(features_list)
            comment = 'stop : {min dist from vertex to finish stop}'

        i = 0

        for feature  in features_list:
            i += 1
            if i%10000 == 0:
                self.parent.setMessage(f'Preparing GTFS. Calc min dist to finishstop. Creating dict ({comment}). Calc point №{i} from {count}')
                QApplication.processEvents()
                if self.verify_break():
                    return 0

            if mode == 1:
                source = feature['osm_id']
            else:
                source = feature.stop_id
                    
            # get finish stops for this source
            dist_min = float('inf')
            to_stop_ids = self.dict_b_s.get(source)
            
            if to_stop_ids:
                for to_stop_id, _ in to_stop_ids:
                    
                    info_stop  = self.dict_feature_to_node.get(to_stop_id)
                    if info_stop:
                        _, dist = info_stop [0]
                        if dist < dist_min:
                            dist_min = dist
                self.dict_feature_min_dist_to_finishstop [source] = dist_min

        #total_dist = sum(self.dict_feature_min_dist_to_finishstop.values())

        # Количество элементов в словаре
        #count = len(self.dict_feature_min_dist_to_finishstop)

        # Вычисляем среднее значение
        #average_dist = total_dist / count
        #print (f'average_dist {average_dist}')        
            
       
    def find_shortest_paths(self, mode):

        if self.verify_break():
                    return 0
        
        

        if mode == 1: # buildings to stops
            features = self.layer_origins.getFeatures()
            features_list = list(features)
            count = len(features_list)
        
        if mode == 2: # stops to stops
            features = self.stops.itertuples(index=False)
            features_list = list(features)
            count = len(features_list)

        self.parent.progressBar.setMaximum(count)
        
        
        self.parent.progressBar.setMaximum(count)
        self.parent.progressBar.setValue(1)
        
        i =  0
        
                
        for feature  in features_list:
            QApplication.processEvents()
            
            i += 1
            if i%100 == 0:
                self.parent.setMessage(f'Preparing GTFS. Calc footpath on road. Calc point №{i} from {count}')
                self.parent.progressBar.setValue(i+3)
                QApplication.processEvents()
                if self.verify_break():
                    return 0

            #if i == 2000:
            #    break
                        
                       
            
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
                    idStart, dist = self.dict_feature_to_node.get(self.source)[0]
                    
                else:
                    self.pStart = feature.geometry
                    idStart, dist = self.dict_feature_to_node.get(self.source)[0]
                
            else:
                continue

            #num_nodes = self.graph.number_of_nodes()
            #num_edges = self.graph.number_of_edges()
            #print(f"Количество вершин: {num_nodes}")
            #print(f"Количество рёбер: {num_edges}")

            dist_finish = self.dict_feature_min_dist_to_finishstop.get(self.source)
            cutoff_value = 500 - dist - dist_finish
            
            lengths, _ = nx.single_source_dijkstra(self.graph, idStart, cutoff = cutoff_value, weight = 'length')
            end_nodes_nearest = list(lengths.keys())

            for node in end_nodes_nearest:
                nearest_stops = self.dict_vertex_stops.get(node)
                distance = round(lengths[node])
                
                for stop in filtered_stops.itertuples(index=False):
                    
                    if stop.stop_id in nearest_stops:
                        if distance <= 400:        
                            self.node_pairs.append((self.source, stop.stop_id, distance))
                        break
      
        
    
    def build_graph(self, roads):
        self.graph = nx.Graph()

        i = 0
        count = roads.featureCount()
        for feature in roads.getFeatures():
            i += 1
            if i%10000 == 0:
               self.parent.setMessage(f'Preparing GTFS. Making graph of road. Add link №{i} from {count}')
               QApplication.processEvents()
               if self.verify_break():
                    return 0 
            line = feature.geometry().asPolyline()
            len = feature['length']

            start_point = (line[0].x(), line[0].y())
            end_point = (line[-1].x(), line[-1].y())

            self.graph.add_node(start_point)
            self.graph.add_node(end_point)
            self.graph.add_edge(start_point, end_point, length=len)
                
        self.build_index_graph ()
    
    def build_index_graph(self):
        self.nodes = list(self.graph.nodes)
        node_positions = [(x, y) for x, y in self.nodes]
        self.kd_tree = KDTree(node_positions)

    
    
        
        
            
    # use it!! 
    def find_nearest_node(self, geometry):
       
        nearest_point_coords = (geometry.x(), geometry.y())
        dist, nearest_node_idx = self.kd_tree.query(nearest_point_coords)
        nearest_node = self.nodes[nearest_node_idx]
        return nearest_node, dist
   
    
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
                
                count_dict = count_dict + 1
                if count_dict%100 == 0:
                    QApplication.processEvents()
                if from_stop_id not in self.dict_b_s:
                        self.dict_b_s[from_stop_id] = []
                self.dict_b_s[from_stop_id].append((to_stop_id, dist))
        

    def run(self):
        
        self.parent.textLog.append(f'<a>Starting calculating footpath on road</a>')
        
        self.create_head_files()

        self.parent.setMessage('Preparing GTFS. Calc footpath on road. Loadings stops.txt  ...')
        QApplication.processEvents()
        self.stops = self.create_stops_gpd()
        self.stops['stop_id'] = self.stops['stop_id'].astype(str)

        
        self.parent.setMessage('Preparing GTFS. Calc footpath on road. Making dictionary (building: {stops})  ...')
        self.create_dict_b_s()

        QApplication.processEvents()
        self.parent.setMessage(f'Preparing GTFS. Calc footpath on road. Making graph ...')
        self.build_graph(self.road_layer)
        QApplication.processEvents()
        if self.verify_break():
                    return 0 
                
        self.create_dict_feature_to_node (mode = 1)
        self.create_dict_feature_to_node (mode = 2)    
        if self.verify_break():
                    return 0 
        self.dict_vertex_stops = self.create_dict_node_to_feature()
        if self.verify_break():
                    return 0
        
        self.create_dict_feature_min_dist_to_finishstop(mode = 1)
        self.create_dict_feature_min_dist_to_finishstop(mode = 2)
        if self.verify_break():
                    return 0
        
        self.find_shortest_paths(mode = 1)
        computation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.parent.textLog.append(f'<a>Find shortest path 1 on time{computation_time}</a>')
        
        self.find_shortest_paths(mode = 2)
        computation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.parent.textLog.append(f'<a>Find shortest path 2 on time{computation_time}</a>')
        
        with open(self.f, 'a') as file:
            if self.node_pairs:
                for id_source, id_destination, dist in self.node_pairs:
                    file.write(f'{id_source},{id_destination},{dist}\n')
                    file.write(f'{id_destination},{id_source},{dist}\n')
            
            
        self.parent.setMessage(f'Preparing GTFS. Calc footpath on road. Calculating footpath on road done')
        QApplication.processEvents()
        

        

    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("Process calculation footpath on road is break")
            if not self.already_display_break:
                self.parent.textLog.append (f'<a><b><font color="red">Process calculation footpath on road is break</font> </b></a>')
                self.already_display_break = True
            self.parent.progressBar.setValue(0)  
            return True
      return False   

    