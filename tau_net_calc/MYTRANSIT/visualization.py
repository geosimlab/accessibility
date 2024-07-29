import os
import math
import numpy as np

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QColor

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsVectorLayerJoinInfo,
    QgsVectorFileWriter,
    QgsSymbol,
    QgsGraduatedSymbolRenderer,
    QgsRendererRange
    )

class visualization:
    def __init__(self, 
                 parent,
                 path_protokol = "", 
                 layer_buildings_name = "",
                 mode = 1
                 ):
        
        if mode == 1: 
            self.fieldname_in_protocol = "Source_ID"
            self.interval = 5000
            self.targetField = 'Total'
        else: 
            self.fieldname_in_protocol = "Destination_ID"
            self.interval = 300
            self.targetField = 'Duration'

        
        self.parent = parent
        self.path_protokol = os.path.normpath(path_protokol)
        self.file_name = os.path.splitext(os.path.basename(path_protokol))[0]
        self.path_protokol = self.path_protokol.replace("\\", "/")
        
        self.layer_buildings_name = layer_buildings_name
        self.layer_buildings = QgsProject.instance().mapLayersByName(self.layer_buildings_name)[0]
        
        uri = f"file:///{self.path_protokol}?type=csv&maxFields=10000&detectTypes=yes&geomType=none&subsetIndex=no&watchFile=no" 
        self.protocol_layer = QgsVectorLayer(uri, f"protocol_{self.file_name}", "delimitedtext")
        QgsProject.instance().addMapLayer(self.protocol_layer)

        # filter on first value Origin_ID
        if mode == 2:
            first_feature = next(self.protocol_layer.getFeatures())
            origin_id_value = first_feature['Origin_ID']
            expression = f'"Origin_ID" = {origin_id_value}'
            self.protocol_layer.setSubsetString(expression)


        self.max_value = None
        data_provider = self.protocol_layer.dataProvider()
        for feature in data_provider.getFeatures():
            value = feature[self.targetField]
            if value is not None:
                if self.max_value is None or value > self.max_value:
                    self.max_value = value

    
    def make_join(self):
        ids_of_joins_in_layer = [join.joinLayerId() for join in self.layer_buildings.vectorJoins()]
        for id in ids_of_joins_in_layer:
            self.layer_buildings.removeJoin(id)
        
        try:
            join_info = QgsVectorLayerJoinInfo()
            join_info.setJoinLayer(self.protocol_layer)
            join_info.setJoinFieldName(self.fieldname_in_protocol)
            join_info.setTargetFieldName('osm_id')
            join_info.setUsingMemoryCache(True)
            join_info.setPrefix('')
            join_info.setJoinFieldNamesSubset([self.targetField])

            self.layer_buildings.addJoin(join_info)
            self.layer_buildings.triggerRepaint()

        except Exception as e:
            self.parent.setMessage(f"Error: {e}")


    def save_layer_as(self, layer, output_path):
        QgsVectorFileWriter.writeAsVectorFormat(layer, output_path, "utf-8", layer.crs(), "ESRI Shapefile")

    def create_temp_layer(self):
        temp_layer_path = os.path.join(os.path.dirname(self.layer_buildings.source()), f"{self.layer_buildings_name}_join_{self.file_name}.shp")
        self.save_layer_as(self.layer_buildings, temp_layer_path)
        temp_layer = QgsVectorLayer(temp_layer_path, f"{self.layer_buildings_name}_join_{self.file_name}", "ogr")
    
        filter_expression = f'"{self.targetField}" is not null'
        temp_layer.setSubsetString(filter_expression)    
        QgsProject.instance().addMapLayer(temp_layer)
        return temp_layer
    
    def style_layer(self, layer):
        
        opacity = 1
        rangeList = []
        min_value = 0
        num_ranges = math.ceil((self.max_value - min_value) / self.interval)
        
        colors = [QColor('#FFFF00'), QColor('#00FF00'), QColor('#4c00ff')]
        color_steps = np.linspace(0, 1, num_ranges + 1)
        
        for i in range(num_ranges):
            lower_bound = min_value + i * self.interval
            upper_bound = min_value + (i + 1) * self.interval
            label = f"{lower_bound} - {upper_bound}"
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            color = QColor()
            color.setNamedColor(self.interpolate_color(colors, color_steps[i]))
            symbol.setColor(color)
            symbol.setOpacity(opacity)
            renderer_range = QgsRendererRange(lower_bound, upper_bound, symbol, label)
            rangeList.append(renderer_range)
        
        groupRenderer = QgsGraduatedSymbolRenderer('', rangeList)
        groupRenderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
        groupRenderer.setClassAttribute(self.targetField)
        layer.setRenderer(groupRenderer)
        layer.triggerRepaint()

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
    
    def run (self):
        self.parent.setMessage(f'Visualization. Making join...')
        QApplication.processEvents()
        self.make_join()

        self.parent.setMessage(f'Visualization. Saving tmp layer...')
        QApplication.processEvents()
        temp_layer = self.create_temp_layer()

        self.parent.setMessage(f'Visualization. Symbology layer...')
        QApplication.processEvents()
        self.style_layer(temp_layer)