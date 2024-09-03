####
#   !!!CLASS EXPERIMENTAL!!!
#   NO USED NOW
####


from datetime import datetime
from qgis.core import QgsWkbTypes
                      

from PyQt5.QtWidgets import QApplication
import networkx as nx
from scipy.spatial import KDTree

class footpath_on_road_b_b:
    def __init__(self, 
                 parent, 
                 road_layer, 
                 layer_origins,
                 speed 
                 ):
        
        self.layer_origins = layer_origins
        self.road_layer = road_layer
        self.speed = speed
        self.parent = parent
        self.count = 0
        self.already_display_break = False

        self.dict_building_to_node = {}
        
        self.distances_dict = {}  # Словарь для хранения результатов
    
    
    def create_dict_node_to_buildings(self):
        comment = 'vertex : nearest buildings'
        features = self.layer_origins.getFeatures()  # объекты из self.layer_origins
        self.kd_tree_buildings = KDTree([(feature.geometry().asPoint().x(), feature.geometry().asPoint().y()) for feature in features])

        len_graph_nodes_coords = len(self.graph_nodes_coords)
        
        nearby_features = {node: [] for node in self.graph.nodes}

        for i, node in enumerate(self.graph_nodes_coords, start = 1):
            if i % 10000 == 0:
                self.parent.setMessage(f'Calculating network distances for node №{i} from {len_graph_nodes_coords}')
                QApplication.processEvents()

            # Находим ближайшие объекты для данного узла на расстоянии до 30 метров
            indices = self.kd_tree_buildings.query_ball_point(node, r = 400)
            nearest_features = [features[index]['osm_id'] for index in indices]
            nearby_features[node] = nearest_features

            


        return nearby_features
        
    def create_dict_building_to_node (self) :
             
        features = self.layer_origins.getFeatures()
        features_list = features
        count = self.layer_origins.featureCount()
        comment = '(building : {nearest vertex, dist})'
       
        i = 0

        for feature  in features_list:
            i += 1
            if i%10000 == 0:
                self.parent.setMessage(f'Building the shortest paths by foot for node №{i} from {count}')
                QApplication.processEvents()
                if self.verify_break():
                    return 0

            
            geometry = feature.geometry()

            if geometry.type() == QgsWkbTypes.PointGeometry:
                points = geometry.asPoint()
            elif geometry.type() == QgsWkbTypes.PolygonGeometry:
               points = geometry.centroid().asPoint()
            
            pFeature = points[0]
            source = feature['osm_id']
                                
            idVertex, dist = self.find_nearest_node(pFeature)
            self.dict_building_to_node[source] = [(idVertex, dist)]
    
    
    def find_immediate_buildings(self, osm_id):

        if self.verify_break():
                    return 0
                        
        QApplication.processEvents()
        
        self.source = osm_id

        idStart, _ = self.dict_building_to_node.get(self.source)[0]
                                
        lengths, _ = nx.single_source_dijkstra(self.graph, 
                                                   idStart,
                                                   cutoff = 350,
                                                   weight = 'length'
                                                   )
        end_nodes_nearest = list(lengths.keys())
          
        for node in end_nodes_nearest: # cicle of all founded node of graph
            nearest_buildings = self.dict_vertex_buildings.get(node) # find list nearest buildings to coords node
            distance = round(lengths[node])
          
            if nearest_buildings:
                for building in nearest_buildings:
                    if building in self.distances_dict:
                        if distance < self.distances_dict[building]:
                            self.distances_dict[building] = distance/self.speed
                    else:
                        self.distances_dict[building] = distance/self.speed
               
            
                  
                
    def build_graph(self, roads):
        self.graph = nx.Graph()

        i = 0
        count = roads.featureCount()
        for feature in roads.getFeatures():
            i += 1
            if i%10000 == 0:
               self.parent.setMessage(f'Constructing road graph, adding link №{i} from {count}')
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
        self.kd_tree_graph = KDTree(node_positions)
        # Создаем список координат узлов графа
        self.graph_nodes_coords = [(node[0], node[1]) for node in self.graph.nodes]
        self.len_graph_nodes_coords = len(self.graph_nodes_coords)
    

    def find_nearest_node(self, geometry):
        """
        nearest_point_coords = (geometry.x(), geometry.y())
        dist, nearest_node_idx = self.kd_tree_graph.query(nearest_point_coords)
        nearest_node = self.nodes[nearest_node_idx]
        return nearest_node, dist
        """
        nearest_point_coords = (geometry.x(), geometry.y())
        dist, nearest_node_idx = self.kd_tree_graph.query(nearest_point_coords)
        nearest_node = self.nodes[nearest_node_idx]
        return nearest_node, dist 
   

    def calc (self, osm_id):
        self.find_immediate_buildings(osm_id)
        return self.distances_dict
            
    def init(self):
        QApplication.processEvents()
        self.parent.setMessage(f'Constructing the road graph ...')
        self.build_graph(self.road_layer)
        QApplication.processEvents()
        if self.verify_break():
            return 0 
                
        self.create_dict_building_to_node ()
        if self.verify_break():
            return 0 
        
        self.dict_vertex_buildings = self.create_dict_node_to_buildings()
        if self.verify_break():
            return 0
        
        #self.find_shortest_paths(osm_id = 238343907)
               
        QApplication.processEvents()
        
    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("The shortest paths construction is interrupted")
            if not self.already_display_break:
                self.parent.textLog.append (f'<a><b><font color="red">The shortest paths construction is interrupted</b></a>')
                self.already_display_break = True
            self.parent.progressBar.setValue(0)  
            return True
      return False