import os
from datetime import datetime
import zipfile
from scipy.spatial import KDTree
import numpy as np

from qgis.analysis import (QgsGraphAnalyzer, 
                           QgsGraphBuilder, 
                           QgsVectorLayerDirector, 
                           QgsNetworkSpeedStrategy, 
                           QgsNetworkDistanceStrategy
                           )

from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import QVariant

from qgis.core import (QgsVectorFileWriter, 
                       QgsFeatureRequest, 
                       QgsGeometry, 
                       QgsSpatialIndex, 
                       QgsCoordinateReferenceSystem, 
                       QgsFeature, 
                       QgsVectorLayer, 
                       QgsField,
                       QgsWkbTypes
                       )

from visualization import visualization

class car_accessibility:
    def __init__(self, 
                 parent, 
                 road_layer, 
                 idx_field_speed, 
                 idx_field_direction, 
                 layer_origins, 
                 layer_dest, 
                 points_to_tie, 
                 speed, 
                 strategy_id, 
                 path_to_protocol, 
                 max_time_minutes, 
                 time_step_minutes, 
                 mode, 
                 protocol_type, 
                 use_aggregate, 
                 field_aggregate,
                 type_road_speed_default,
                 layer_viz,
                 fieldname_type_road, 
                 layerdest_field,
                 layer_vis_field,
                 aliase
                 ):
        
        self.points_to_tie = points_to_tie
        self.strategy_id = int(strategy_id)
        self.path_to_protocol = path_to_protocol
        self.max_time_minutes = max_time_minutes 
        self.time_step_minutes = time_step_minutes
        self.speed = speed
        self.road_layer = road_layer
        self.idx_field_speed = idx_field_speed
        self.idx_field_direction = idx_field_direction
        self.layer_origins = layer_origins
        self.layer_dest = layer_dest
        self.protocol_type = protocol_type
        self.mode = mode
        self.curr_DateTime = self.getDateTime()
        self.parent = parent
        self.use_aggregate = use_aggregate
        self.field_aggregate = field_aggregate
        self.type_road_speed_default = type_road_speed_default
        self.layer_viz = layer_viz
        self.max_time_sec = self.max_time_minutes * 60

        self.fieldname_type_road = fieldname_type_road
        self.layerdest_field = layerdest_field
        self.layer_vis_field = layer_vis_field

        self.aliase = aliase
    
    
    def create_dict_vertex_nearest_buildings(self):
        # Создаем пространственный индекс для вершин графа
        #vertex_index = QgsSpatialIndex()

        # Создаем список точек вершин для KD-дерева
        vertex_points = []
        for vertex_id in range(self.graph.vertexCount()):
            vertex = self.graph.vertex(vertex_id)
            vertex_points.append((vertex.point().x(), vertex.point().y()))
        # Создаем KD-дерево
        self.kd_tree = KDTree(np.array(vertex_points))
        
        """
        c = 0
        for vertex_id in range(self.graph.vertexCount()):

            c += 1
            if c%500 == 0:
                QApplication.processEvents()

            vertex = self.graph.vertex(vertex_id)
            vertex_point = vertex.point()
            vertex_feature = QgsFeature()
            vertex_feature.setGeometry(QgsGeometry.fromPointXY(vertex_point))
            vertex_feature.setId(vertex_id)
            vertex_index.insertFeature(vertex_feature)
        """    

        self.dict_vertex_nearest_buildings = {}
        self.dict_building_agg = {}

        Field = self.field_aggregate
            
        if self.protocol_type == 1 and self.use_aggregate and self.layer_dest.fields().indexOf(Field) == -1:
                self.parent.textLog.append(f'<a><b><font color="red"> WARNING: field "{Field}" no exist in layer, aggregate no run</font> </b></a>')    
                self.use_aggregate = False

        if self.use_aggregate:
            for feature in self.layer_dest.getFeatures():
                if self.protocol_type == 1 and self.use_aggregate and (not (isinstance(feature[Field], int) or (isinstance(feature[Field], str) and feature[Field].isdigit()))):
                    self.parent.textLog.append(f'<a><b><font color="red"> WARNING: type of field "{Field}" to aggregate  is no digital, aggregate no run</font> </b></a>')
                    self.use_aggregate = False
                break

        dest_features_list = self.layer_dest.getFeatures()
        count_item = self.layer_dest.featureCount()
        c = 0
        for feature in dest_features_list:

            c += 1
            if c%5000 == 0:
                QApplication.processEvents()

                self.parent.setMessage(f'Constricting dictionary (vertex: nearest buildings). Item №{c} from {count_item}')
                
            geom = feature.geometry()

            building_point = 0
            

            if geom.type() == QgsWkbTypes.PointGeometry:
                building_point = geom.asPoint()
            elif geom.type() == QgsWkbTypes.PolygonGeometry:
                building_point = geom.centroid().asPoint()

            if building_point ==  0:
                multi_polygon = geom.asMultiPolygon()
                building_point = multi_polygon[0] 
            
            building_id = feature[self.layerdest_field]

            if self.use_aggregate:
                building_aggregate = feature[self.field_aggregate]
            else:
                building_aggregate = 0

            self.dict_building_agg[building_id] = int(building_aggregate)
                
            # Создаем круг радиусом 400 метров вокруг здания
            buffer_radius = 200
            buffer_points = self.kd_tree.query_ball_point([building_point.x(), building_point.y()], buffer_radius)

            for nearest_vertex_id in buffer_points:
                if nearest_vertex_id in self.dict_vertex_nearest_buildings:
                    self.dict_vertex_nearest_buildings[nearest_vertex_id].add(building_id)
                else:
                    self.dict_vertex_nearest_buildings[nearest_vertex_id] = {building_id}

    
    def find_vertex_nearest(self, point):
        
        nearest_ids = self.index_road.nearestNeighbor(point, 1)
        nearest_id = nearest_ids[0]
        nearest_feature = next(self.road_layer_mod.getFeatures(QgsFeatureRequest().setFilterFid(nearest_id)))
        line_geom = nearest_feature.geometry()
        closest_point = line_geom.closestVertex(point)[0]
        idStart = self.graph.findVertex(closest_point)
                
        return idStart
        
    def find_car_accessibility(self):

        count = len(self.points_to_tie) 
        self.parent.progressBar.setMaximum(count+3)
        self.parent.progressBar.setValue(0)

        #crs_src = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS84
        #crs_dest = QgsCoordinateReferenceSystem("EPSG:2039")  # UTM Zone 36N
        #self.transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
        
        if self.idx_field_direction != -1:

            valid_values = {"T","F","B"}
            
            field = self.road_layer.fields().at(self.idx_field_direction)
            """
            field_type = field.type()
            
            if not (field_type in [QVariant.Int, QVariant.Double, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong]):
                self.parent.textLog.append(f'<a><b><font color="red"> WARNING: The field with direction value"{field.name()}" must be a int type. The direction of movement field will not be included in the calculations</font> </b></a>')
                self.idx_field_direction = -1
                
            else:
            """
            for feature in self.road_layer.getFeatures():
                    field_value = feature.attribute(self.idx_field_direction)
                    if not(field_value in valid_values):
                        self.parent.textLog.append(f'<a><b><font color="red"> WARNING: The field with direction value "{field.name()}" must use values ​​(T,F,B). The direction of movement field will not be included in the calculations</font> </b></a>')
                        self.idx_field_direction = -1
                        break 
        
        field = self.road_layer.fields().at(self.idx_field_speed)
        field_type = field.type()

        if not (field_type in [QVariant.Int, QVariant.Double, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong]):
            self.parent.textLog.append(f'<a><b><font color="red"> WARNING: The field with speed value "{field.name()}" must be a digilal type. The speed of movement field will not be included in the calculations</font> </b></a>')
            self.idx_field_speed = -1
        self.change_road_layer()
        self.director = QgsVectorLayerDirector(self.road_layer_mod, 
                                               self.idx_field_direction,
                                                 '', '', '', 
                                               QgsVectorLayerDirector.DirectionBoth
                                               )

        defaultValue = int(self.speed)
        
        #toMetricFactor = 1  # for speed m/sec
        toMetricFactor = 1 / 3.6  # for speed km/h
        
        if self.strategy_id == 1:
            strategy = QgsNetworkSpeedStrategy(self.idx_field_speed, 
                                               defaultValue, 
                                               toMetricFactor
                                               )
        else:
            strategy = QgsNetworkDistanceStrategy()

        self.director.addStrategy(strategy)
        self.builder = QgsGraphBuilder(self.road_layer_mod.crs())
        QApplication.processEvents()
        self.parent.setMessage(f'Constructing graph ...')
        
        QApplication.processEvents()
        self.director.makeGraph(self.builder, [])
        self.graph = self.builder.graph()
        time1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #self.parent.textLog.append(f'<a>Time after Making graph {time1}</a>') 
        self.parent.progressBar.setValue(1)

        # Создание пространственного индекса для поиска ближайших вершин
        self.parent.setMessage(f'Building spatial index for the roads table...')
        QApplication.processEvents()
        crs_meter = QgsCoordinateReferenceSystem("EPSG:2039")
        self.road_layer_mod.setCrs(crs_meter)
        self.index_road = QgsSpatialIndex()
        c = 0
        for feature in self.road_layer_mod.getFeatures():
            c += 1
            if c%500 == 0:
                QApplication.processEvents()
            self.index_road.insertFeature(feature)
        self.parent.progressBar.setValue(2)    
        time1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #self.parent.textLog.append(f'<a>Time after creating index road {time1}</a>') 
        self.parent.setMessage(f'Building spatial index for the buildings table...')
        QApplication.processEvents()
        crs_meter = QgsCoordinateReferenceSystem("EPSG:2039")
        self.layer_origins.setCrs(crs_meter)
        self.index_buildings = QgsSpatialIndex()
        c = 0
        for feature in self.layer_origins.getFeatures():
            c += 1
            if c%500 == 0:
                QApplication.processEvents()
            self.index_buildings.insertFeature(feature)
        
        self.parent.progressBar.setValue(3)
        time1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #self.parent.textLog.append(f'<a>Time after creating index buildings {time1}</a>') 

        i =  0

        self.parent.setMessage(f'Constricting dictionary')
        QApplication.processEvents()        
        self.create_dict_vertex_nearest_buildings()
        time1 = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #self.parent.textLog.append(f'<a>Time after creating dict (vertex: nearest buildings) {time1}</a>') 
        self.create_head_files()
        
        for source, Points in self.points_to_tie:
            QApplication.processEvents()
            if self.verify_break():
                return 0
            i += 1
            self.parent.progressBar.setValue(i+3)
            self.parent.setMessage(f'Building thematic map for the feature №{i} from {count}')
            QApplication.processEvents()

            self.source = source
            self.pStart = Points[0]
                      

            # Transform the point
            #pStart = self.transform.transform(pStart)
           
            idStart = self.find_vertex_nearest(self.pStart)
            
            (self.tree, self.costs) = QgsGraphAnalyzer.dijkstra(self.graph,  idStart, 0)
            
            if self.protocol_type == 2:
                self.makeProtocolArea()
            else: 
                self.makeProtocolMap()

    def change_road_layer(self):
        self.parent.setMessage(f'Modifying roads ...')
        features = self.road_layer.getFeatures()
        new_features = []

        for feature in features:
            new_feature = QgsFeature(feature)

            if self.idx_field_direction != -1:
                current_value = new_feature.attribute(self.idx_field_direction)
        
                new_value = 2 

                if self.mode == 1: # raptor
                    if current_value == "T":
                        new_value = 1
                    elif current_value == "F":
                        new_value = 0

                if self.mode == 2: # backward raptor
                    if current_value == "T":
                        new_value = 0
                    elif current_value == "F":
                        new_value = 1


                new_feature.setAttribute(self.idx_field_direction, new_value)
    
                
            fclass_value = new_feature[self.fieldname_type_road]
            new_value = self.type_road_speed_default.get(fclass_value, int(self.speed))
            new_feature.setAttribute(self.idx_field_speed, int(new_value))
                

            new_features.append(new_feature)

               
        # Create a new QgsVectorLayer from the modified features
        layer_fields = self.road_layer.fields()
        layer_crs = self.road_layer.crs()
        self.road_layer_mod = QgsVectorLayer(f'LineString?crs={layer_crs.authid()}', 'modified_road_layer', 'memory')
        self.road_layer_mod_data_provider = self.road_layer_mod.dataProvider()

        
        self.road_layer_mod_data_provider.addAttributes(layer_fields)
        self.road_layer_mod.updateFields()

        self.road_layer_mod.deleteFeatures([]) 
        
        (success, result) = self.road_layer_mod_data_provider.addFeatures(new_features)
        
        self.road_layer_mod.updateExtents()


    def calc_min_cost (self):
        self.min_costs = {}

        # Проход по всем edgeId в дереве
        for edgeId in self.tree:
            if edgeId == -1:
                continue
            try:
                if edgeId >= len(self.costs):
                    continue
                if self.costs[edgeId] == float('inf'):
                    continue
                buildings = self.dict_vertex_nearest_buildings[edgeId]
            except KeyError:
                continue

            cost = round(self.costs[edgeId])
            if cost <= self.max_time_sec:
                for building in buildings:
                    # Определяем пару {self.source, building}
                    pair = (self.source, building)

                    # Если пара уже есть в словаре, проверяем минимальный cost
                    if pair in self.min_costs:
                        self.min_costs[pair] = min(self.min_costs[pair], cost)
                    else:
                        self.min_costs[pair] = cost

    def makeProtocolArea(self):
               
        self.calc_min_cost()
        with open(self.f, 'a') as filetowrite:
            for (source, building), min_cost in self.min_costs.items():
                if self.mode == 1:
                    filetowrite.write(f'{source},{building},{min_cost}\n')
                else:
                    filetowrite.write(f'{building},{source},{min_cost}\n')
        
    
    def makeProtocolMap(self):
        
        self.calc_min_cost()

        counts = {x: 0 for x in range(0, len(self.grades))}  # Счётчики для градаций
        aggregates = {x: 0 for x in range(0, len(self.grades))}  # Счётчики для агрегатов

        # Проход по минимальным значениям стоимости для каждой пары (source, building)
        for (source, building), cost in self.min_costs.items():
            if cost <= self.max_time_sec:
                # Ищем соответствующую градацию
                for i in range(0, len(self.grades)):
                    grad = self.grades[i]
                    if grad[0] <= cost < grad[1]:
                        counts[i] += 1

                        if self.use_aggregate:
                            aggregates[i] += self.dict_building_agg[building]
                        break  # Выходим из цикла, если найдена соответствующая градация

        row = f'{self.source}'

        
        with open(self.f, 'a') as filetowrite:
            Total = 0
            for i in range(0, len(self.grades)):
                row = f'{row},{counts[i]}'
                if not self.use_aggregate:
                    Total += counts[i]
                if self.use_aggregate:
                    row = f'{row},{aggregates[i]}'
                    Total += aggregates[i]
            filetowrite.write(f'{row},{Total}\n')           
            

    def prepare_grades(self): 
        
        time_step_sec = self.time_step_minutes * 60
        #intervals_number= round(self.max_time_minutes/self.time_step_minutes)
        intervals_number= round(self.max_time_sec / time_step_sec)
        grades = []
        header = 'Origin_ID'
        
        low_bound_sec = 0
        top_bound_sec = time_step_sec
        for i in range(0,intervals_number):
            header += f',{low_bound_sec}min-{top_bound_sec}min'
            if self.use_aggregate:
                header += f',sum({self.field_aggregate})'
            grades.append([low_bound_sec,top_bound_sec])
            low_bound_sec = low_bound_sec + time_step_sec
            top_bound_sec = top_bound_sec + time_step_sec
        header += ',Total\n' 
        #increase by one the last top bound
        #last_top = grades[intervals_number-1][1] + 1
        #grades[intervals_number-1][1] = last_top
        return header,grades

    def getDateTime(self):
        current_datetime = datetime.now()
        month = current_datetime.strftime("%b").lower()  # Преобразуем месяц в нижний регистр
        day = str(current_datetime.day).zfill(2)
        hour = str(current_datetime.hour).zfill(2)
        minute = str(current_datetime.minute).zfill(2)
        second = str(current_datetime.second).zfill(2)
        return f'{day}{month}_{hour}h{minute}m'
    
    def create_head_files(self):

        if self.protocol_type == 1:
            table_header, self.grades = self.prepare_grades()
        else:
            if self.mode == 1:
                table_header = "Origin_ID,Destination_ID,Duration\n"
            else: 
                table_header = "Destination_ID,Origin_ID,Duration\n"

        self.folder_name = f'{self.path_to_protocol}//{self.curr_DateTime}'

        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
        else:
            return 0
        
        self.f = f'{self.folder_name}//access_{self.curr_DateTime}.csv'
        with open(self.f, 'w') as self.filetowrite:
            self.filetowrite.write(table_header)  

    def run(self, begin_computation_time):
                       
        self.find_car_accessibility()
        
        
        QApplication.processEvents()
        after_computation_time = datetime.now()
        after_computation_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.parent.textLog.append(f'<a>Finished: {after_computation_str}</a>')  

        duration_computation = after_computation_time - begin_computation_time
        duration_without_microseconds = str(duration_computation).split('.')[0]
        self.parent.textLog.append(f'<a>Processing time: {duration_without_microseconds}</a>') 

        self.write_info()
        self.parent.textLog.append(f'<a href="file:///{self.folder_name}" target="_blank" >Output in folder</a>')
        self.parent.setMessage(f'Finished')
        
        return self.folder_name

    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("Car accessibility computations are interrupted")
            self.parent.textLog.append (f'<a><b><font color="red">Process calculation car accessibility is break</font> </b></a>')
            if self.folder_name !="":
              self.write_info()  
            self.parent.progressBar.setValue(0)  
            return True
      return False   

    def write_info (self):

        vis = visualization (self.parent, self.layer_viz, mode = self.protocol_type, fieldname_layer = self.layer_vis_field)
        if self.protocol_type == 1 :
            count_diapazone = round(int(self.max_time_minutes)/int((self.time_step_minutes)))
            vis.set_count_diapazone (count_diapazone)
        vis.add_thematic_map(self.f, self.aliase)
        self.parent.textLog.append(f'<a>Output:</a>')  
        self.parent.textLog.append(f'<a>{self.f}</a>')


        text = self.parent.textLog.toPlainText()
        filelog_name = f'{self.folder_name}//log_{self.curr_DateTime}.txt'
        with open(filelog_name, "w") as file:
            file.write(text)
        
        zip_filename1 = f'{self.folder_name}//layer_road{self.curr_DateTime}.zip'
        filename1 = f'{self.folder_name}//layer_road_{self.curr_DateTime}.geojson'
        self.save_layer_to_zip(self.road_layer_mod, zip_filename1, filename1)
        """    
        zip_filename1 = f'{self.folder_name}//layer_origins{self.curr_DateTime}.zip'
        filename1 = f'{self.folder_name}//layer_origins{self.curr_DateTime}.geojson'
        self.save_layer_to_zip(self.layer_origins, zip_filename1, filename1)
        """

    def save_layer_to_zip(self, layer, zip_filename, filename):
        try:
            
            temp_file = "temp_layer_file.geojson"
            QgsVectorFileWriter.writeAsVectorFormat(layer, temp_file, "utf-8", layer.crs(), "GeoJSON")
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(temp_file, os.path.basename(filename))
                os.remove(temp_file)   
        except:
            return 0