import os
import math
import numpy as np
from datetime import datetime

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorLayerJoinInfo,
    QgsSymbol,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange,
    QgsMapLayerStyle,
    )

class visualization:
    def __init__(self, 
             parent,
             layer_buildings_name = "",
             mode = "",
             fieldname_layer = "",
             mode_compare = False
             ):
        
        self.mode = mode
        self.mode_compare = mode_compare

        if self.mode == 1: # MAP
            self.fieldname_in_protocol = "Origin_ID"
            self.targetField_base = 'Total'
        else: # AREA
            self.fieldname_in_protocol = "Destination_ID"
            self.targetField_base = 'Duration'

        self.fieldname_layer = fieldname_layer
        self.parent = parent
                
        self.layer_buildings_name = layer_buildings_name
        self.layer_buildings = QgsProject.instance().mapLayersByName(self.layer_buildings_name)[0]

        self.count_diapazone = 0

        #ids_of_joins_in_layer = [join.joinLayerId() for join in self.layer_buildings.vectorJoins()]
        #for id in ids_of_joins_in_layer:
        #    self.layer_buildings.removeJoin(id)

        #style_manager = self.layer_buildings.styleManager()
        #for style_item in style_manager.styles():
        #    style_manager.removeStyle(style_item)    
        
    def make_join(self):
        
        join_info = QgsVectorLayerJoinInfo()
        join_info.setJoinLayer(self.protocol_layer)
        join_info.setJoinFieldName(self.fieldname_in_protocol)
        join_info.setTargetFieldName(self.fieldname_layer)
        join_info.setUsingMemoryCache(True)
        join_info.setPrefix(f'{self.file_name}_')
        join_info.setJoinFieldNamesSubset([self.targetField_base])

        self.layer_clone.addJoin(join_info)
        self.layer_clone.triggerRepaint()

        field_name = f'{self.file_name}_{self.targetField_base}' 
        
        return field_name    
   
    def style_layer(self):
        # Определяем начальные параметры
        layer = self.layer_clone
        opacity = 1
        rangeList = []
        
        print (f'self.max_value {self.max_value}')
        print (f'self.min_value {self.min_value}')
        print (f'self.interval {self.interval}')

        num_ranges = math.ceil((self.max_value - self.min_value) / self.interval)
      
        # Определяем цвета и градации
        colors = [QColor('#FFFF00'), QColor('#00FF00'), QColor('#4c00ff')]
        color_steps = np.linspace(0, 1, num_ranges + 1)
        
        # Генерация диапазонов для рендеринга
        for i in range(num_ranges):
            lower_bound = self.min_value + i * self.interval
            upper_bound = self.min_value + (i + 1) * self.interval
            label = f"{round(lower_bound, 2)} - {round(upper_bound, 2)}"
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())

            fill_color = QColor()
            fill_color.setNamedColor(self.interpolate_color(colors, color_steps[i]))

            symbol.setColor(fill_color)
            symbol.setOpacity(opacity)
            symbol.symbolLayer(0).setStrokeColor(fill_color)

            renderer_range = QgsRendererRange(lower_bound, upper_bound, symbol, label)
            rangeList.append(renderer_range)
    
        # Создаем и настраиваем рендерер
        groupRenderer = QgsGraduatedSymbolRenderer('', rangeList)
        groupRenderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
        groupRenderer.setClassAttribute(self.targetField)
        
        
        # Применяем рендерер к слою
        layer.setRenderer(groupRenderer)
        layer.triggerRepaint()  # Обновляем отображение слоя

        """
        style_manager = layer.styleManager()

        new_style = QgsMapLayerStyle()
        new_style.readFromLayer(layer)
        style_manager.addStyle(self.file_name, new_style)
        layer.triggerRepaint()
        """
        

    def interpolate_color(self, colors, ratio):
        if ratio <= 0.5:
            t = ratio * 2
            start_color = colors[0]
            end_color = colors[1]
        else:
            t = (ratio - 0.5) * 2
            start_color = colors[1]
            end_color = colors[2]
    
        start_rgb = start_color.getRgb()
        end_rgb = end_color.getRgb()
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
        return QColor(r, g, b).name()
    
        
    def add_thematic_map (self, path_protokol, aliase):

                
        
        self.path_protokol = os.path.normpath(path_protokol)
        self.file_name = os.path.splitext(os.path.basename(path_protokol))[0]
        self.path_protokol = self.path_protokol.replace("\\", "/")

        uri = f"file:///{self.path_protokol}?type=csv&maxFields=10000&detectTypes=yes&geomType=none&subsetIndex=no&watchFile=no" 
        
        self.protocol_layer = QgsVectorLayer(uri, aliase, "delimitedtext")

        if self.protocol_layer.featureCount() == 0:
            self.parent.textLog.append(f'<a><b><font color="red">Protocol is empty. Visualization not performed.</font> </b></a>') 
            return
        

        if self.protocol_layer.featureCount() > 0:
            QgsProject.instance().addMapLayer(self.protocol_layer)

            # filter on first value Origin_ID
            if self.mode == 2: # AREA
                first_feature = next(self.protocol_layer.getFeatures())
                origin_id_value = first_feature['Origin_ID']
                expression = f'"Origin_ID" = {origin_id_value}'
                self.protocol_layer.setSubsetString(expression)


            self.max_value = 0
            self.min_value = float('inf')
            data_provider = self.protocol_layer.dataProvider()
            for feature in data_provider.getFeatures():
                value = feature[self.targetField_base]
                if value is not None:
                    if self.max_value == 0 or value > self.max_value:
                        self.max_value = value

                    if self.min_value is None or value < self.min_value:
                        self.min_value = value

            #self.min_value = 0                
            if self.mode == 1: # MAP    
                self.interval = 5000

            if self.mode == 2: # AREA    
                self.interval = 300

            if self.mode_compare:        
                self.interval = self.max_value / 10

            if self.count_diapazone > 0:
                self.interval = self.max_value / self.count_diapazone

        self.layer_clone = self.layer_buildings.clone()
        self.layer_clone.setName(aliase)
        QgsProject.instance().addMapLayer(self.layer_clone)


        self.parent.setMessage(f'Joining ...')
        QApplication.processEvents()
        self.targetField = self.make_join()

        self.parent.setMessage(f'Symbology ...')
        QApplication.processEvents()
        self.style_layer()

    def set_count_diapazone (self, value):
        self.count_diapazone = value

    def run (self):
        pass