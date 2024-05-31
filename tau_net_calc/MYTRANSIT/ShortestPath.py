import os
from datetime import datetime
import zipfile

from qgis.analysis import QgsGraphAnalyzer, QgsGraphBuilder, QgsVectorLayerDirector, QgsNetworkSpeedStrategy, QgsNetworkDistanceStrategy
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QVariant
from qgis.core import QgsVectorFileWriter, QgsFeatureRequest, QgsGeometry, QgsSpatialIndex, QgsCoordinateReferenceSystem, QgsFeature

class ShortestPathUtils:
    def __init__(self, parent, road_layer, idx_field_speed, layer_origins, points_to_tie, speed, strategy_id, path_to_protocol, max_time_minutes, time_step_minutes, protocol_type, use_aggregate, field_aggregate):
        
        self.points_to_tie = points_to_tie
        self.strategy_id = int(strategy_id)
        self.path_to_protocol = path_to_protocol
        self.max_time_minutes = max_time_minutes 
        self.time_step_minutes = time_step_minutes
        self.speed = speed
        self.road_layer = road_layer
        self.idx_field_speed = idx_field_speed
        self.layer_origins = layer_origins
        self.protocol_type = protocol_type
        self.curr_DateTime = self.getDateTime()
        self.parent = parent
        self.use_aggregate = use_aggregate
        self.field_aggregate = field_aggregate
    
    
    def create_dict_vertex_nearest_buildings(self):
        # Создаем пространственный индекс для вершин графа
        vertex_index = QgsSpatialIndex()
        vertex_to_id = {}

        for vertex_id in range(self.graph.vertexCount()):
            vertex = self.graph.vertex(vertex_id)
            vertex_point = vertex.point()
            vertex_feature = QgsFeature()
            vertex_feature.setGeometry(QgsGeometry.fromPointXY(vertex_point))
            vertex_feature.setId(vertex_id)
            vertex_index.insertFeature(vertex_feature)
            vertex_to_id[vertex_point] = vertex_id

        self.dict_vertex_nearest_buildings = {}

        Field = self.field_aggregate
        if self.layer_origins.fields().indexOf(Field) == -1:
                self.parent.textLog.append(f'<a><b><font color="red"> WARNING: field "{Field}" no exist in layer, aggregate no run</font> </b></a>')    
                self.use_aggregate = False

        if self.use_aggregate:
            for feature in self.layer_origins.getFeatures():
                if not (isinstance(feature[Field], int) or (isinstance(feature[Field], str) and feature[Field].isdigit())):
                    self.parent.textLog.append(f'<a><b><font color="red"> WARNING: type of field "{Field}" to aggregate  is no digital, aggregate no run</font> </b></a>')
                    self.use_aggregate = False
                break

        for feature in self.layer_origins.getFeatures():
            building_point = feature.geometry().asPoint()
            building_osm_id = feature['osm_id']

            if self.use_aggregate:
                building_aggregate = feature[self.field_aggregate]
            else:
                building_aggregate = 0

            # Найти ближайшую вершину
            nearest_vertex_ids = vertex_index.nearestNeighbor(building_point, 1)
            nearest_vertex_id = nearest_vertex_ids[0]

            if nearest_vertex_id in self.dict_vertex_nearest_buildings:
                self.dict_vertex_nearest_buildings[nearest_vertex_id].add((building_osm_id, building_aggregate))
            else:
                self.dict_vertex_nearest_buildings[nearest_vertex_id] = {(building_osm_id, building_aggregate)}


    
    def find_vertex_nearest(self, point):
        
        nearest_ids = self.index_road.nearestNeighbor(point, 1)
        nearest_id = nearest_ids[0]
        nearest_feature = next(self.road_layer.getFeatures(QgsFeatureRequest().setFilterFid(nearest_id)))
        line_geom = nearest_feature.geometry()
        closest_point = line_geom.closestVertex(point)[0]
        idStart = self.graph.findVertex(closest_point)
                
        return idStart
        
    def find_shortest_paths(self):

        count = len(self.points_to_tie) 
        self.parent.progressBar.setMaximum(count+3)
        self.parent.progressBar.setValue(0)

        #crs_src = QgsCoordinateReferenceSystem("EPSG:4326")  # WGS84
        #crs_dest = QgsCoordinateReferenceSystem("EPSG:2039")  # UTM Zone 36N
        #self.transform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())

        self.director = QgsVectorLayerDirector(self.road_layer, -1, '', '', '', QgsVectorLayerDirector.DirectionBoth)

        defaultValue = int(self.speed)
        toMetricFactor = 1  # for speed m/sec
        
        field = self.road_layer.fields().at(self.idx_field_speed)
        field_type = field.type()
        if not (field_type in [QVariant.Int, QVariant.Double, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong]):
            self.idx_field_speed = -1


        if self.strategy_id == 1:
            strategy = QgsNetworkSpeedStrategy(self.idx_field_speed, defaultValue, toMetricFactor)
        else:
            strategy = QgsNetworkDistanceStrategy()

        self.director.addStrategy(strategy)
        self.builder = QgsGraphBuilder(self.road_layer.crs())
        QApplication.processEvents()
        self.parent.setMessage(f'Making graph ...')
        QApplication.processEvents()
        self.director.makeGraph(self.builder, [])
        self.graph = self.builder.graph()
        self.parent.progressBar.setValue(1)

        # Создание пространственного индекса для поиска ближайших вершин
        self.parent.setMessage(f'Creating index road...')
        QApplication.processEvents()
        crs_meter = QgsCoordinateReferenceSystem("EPSG:2039")
        self.road_layer.setCrs(crs_meter)
        self.index_road = QgsSpatialIndex()
        for feature in self.road_layer.getFeatures():
            self.index_road.insertFeature(feature)
        self.parent.progressBar.setValue(2)    

        self.parent.setMessage(f'Creating index buildings...')
        QApplication.processEvents()
        crs_meter = QgsCoordinateReferenceSystem("EPSG:2039")
        self.layer_origins.setCrs(crs_meter)
        self.index_buildings = QgsSpatialIndex()
        for feature in self.layer_origins.getFeatures():
            self.index_buildings.insertFeature(feature)
        
        self.parent.progressBar.setValue(3)

        i =  0
                
        self.create_dict_vertex_nearest_buildings()
        self.create_head_files()
        
        for source, Points in self.points_to_tie:
            QApplication.processEvents()
            if self.verify_break():
                return 0
            i += 1
            self.parent.progressBar.setValue(i+3)
            self.parent.setMessage(f'Calc point №{i} from {count}')
            QApplication.processEvents()

            self.source = source
            self.pStart = Points[0]
                      

            # Transform the point
            #pStart = self.transform.transform(pStart)
           
            idStart = self.find_vertex_nearest(self.pStart)
            
            (self.tree, self.costs) = QgsGraphAnalyzer.dijkstra(self.graph,  idStart, 0)
            
            if self.protocol_type == 1:
                self.makeProtocolArea()
            else: 
                self.makeProtocolMap()
    
    def makeProtocolArea(self):
        
        with open(self.f, 'a') as filetowrite: 
            for edgeId  in self.tree:
                if edgeId == -1:
                    continue
                try:
                    if self.costs[edgeId] == float('inf'):
                        continue
                    buildings = self.dict_vertex_nearest_buildings[edgeId]
                except:
                    continue
                cost = round(self.costs[edgeId]/60,2)
                if cost <= self.max_time_minutes:
                    for building, _ in buildings:
                        filetowrite.write(f'{self.source},{building},{cost}\n')  
    
    def makeProtocolMap(self):
        massiv = []
        
        counts = {x: 0 for x in range(0, len(self.grades))} #counters for grades
        agrregates = {x: 0 for x in range(0, len(self.grades))} #counters for agrregates

        
        for edgeId  in self.tree:
                if edgeId == -1:
                    continue
                try:
                    if self.costs[edgeId] == float('inf'):
                        continue
                    buildings = self.dict_vertex_nearest_buildings[edgeId]
                except:
                    continue
                cost = round(self.costs[edgeId]/60,2)
                if cost <= self.max_time_minutes:
                    for building, agg in buildings:
                        massiv.append((self.source, building, agg, cost))
        
        for item in massiv:
            num = item[3]
            agg = item[2]
            for i in range(0, len(self.grades)) :
                grad = self.grades[i]
                if num >= grad[0] and num < grad[1]:
                    counts[i] = counts[i] + 1

                    if self.use_aggregate:
                        agrregates[i] = agrregates[i] + int(agg)
                    break 
        row = f'{self.source}'
        
        with open(self.f, 'a') as filetowrite:
            for i in range(0,len(self.grades)) :  
                row = f'{row},{counts[i]}'
                if self.use_aggregate:
                    row = f'{row},{agrregates[i]}'   
            filetowrite.write(row + "\n")        

    def prepare_grades(self): 
        intervals_number= round(self.max_time_minutes/self.time_step_minutes)
        grades = []
        header = 'source,'
        time_step_min = self.time_step_minutes
        low_bound_min = 0
        top_bound_min = time_step_min
        for i in range(0,intervals_number):
            header += f'{low_bound_min}min-{top_bound_min}min,'
            if self.use_aggregate:
                header += f'sum({self.field_aggregate}),'
            grades.append([low_bound_min,top_bound_min])
            low_bound_min = low_bound_min + time_step_min
            top_bound_min = top_bound_min + time_step_min
        header += '\n' 
        #increase by one the last top bound
        #last_top = grades[intervals_number-1][1] + 1
        #grades[intervals_number-1][1] = last_top
        return header,grades

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

        if self.protocol_type == 2:
            table_header, self.grades = self.prepare_grades()
        else:
            table_header = "source,destination,accessibility(min)\n"

        self.folder_name = f'{self.path_to_protocol}//{self.curr_DateTime}'

        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
        else:
            return 0
        
        self.f = f'{self.folder_name}//access_{self.curr_DateTime}.csv'
        with open(self.f, 'w') as self.filetowrite:
            self.filetowrite.write(table_header)  

    def run(self):

        begin_computation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  
        self.parent.textLog.append(f'<a>Algorithm started at {begin_computation_time}</a>')
        self.parent.textLog.append(f'<a>Starting calculating</a>')
        
                 

        self.find_shortest_paths()

        self.parent.setMessage(f'Calculating done')
        QApplication.processEvents()
        time_after_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.parent.textLog.append(f'<a>Time after computation {time_after_computation}</a>')  

        self.write_info()

        self.parent.textLog.append(f'<a href="file:///{self.folder_name}" target="_blank" >Output in folder</a>')

    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("Process raptor is break")
            self.parent.textLog.append (f'<a><b><font color="red">Process raptor is break</font> </b></a>')
            if self.folder_name !="":
              self.write_info()  
            self.parent.progressBar.setValue(0)  
            return True
      return False   

    def write_info (self):
        text = self.parent.textLog.toPlainText()
        filelog_name = f'{self.folder_name}//log_{self.curr_DateTime}.txt'
        with open(filelog_name, "w") as file:
            file.write(text)
        """
        zip_filename1 = f'{self.folder_name}//layer_road{self.curr_DateTime}.zip'
        filename1 = f'{self.folder_name}//layer_road_{self.curr_DateTime}.geojson'
        self.save_layer_to_zip(self.road_layer, zip_filename1, filename1)

        zip_filename1 = f'{self.folder_name}//layer_origins{self.curr_DateTime}.zip'
        filename1 = f'{self.folder_name}//layer_origins{self.curr_DateTime}.geojson'
        self.save_layer_to_zip(self.layer_origins, zip_filename1, filename1)
        """

    def save_layer_to_zip(self, layer, zip_filename, filename):
        try:
            
            temp_file = "temp_layer_file.geojson"
            QgsVectorFileWriter.writeAsVectorFormat(layer, temp_file, "utf-8", layer.crs(), "GeoJSON")
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                zipf.write(temp_file, os.path.basename(filename))
                os.remove(temp_file)   
        except:
            return 0