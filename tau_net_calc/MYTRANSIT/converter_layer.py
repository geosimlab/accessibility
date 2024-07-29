from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    )
from PyQt5.QtWidgets import QApplication


class MultiLineStringToLineStringConverter:
    def __init__(self, parent, layer):
        self.layer = layer
        self.parent = parent
        self.temp_layer = None
        self.already_display_break = False

    def create_temp_layer(self):

        crs = self.layer.crs().toWkt()
        self.temp_layer = QgsVectorLayer(f"LineString?crs={crs}", "Temporary Layer", "memory")
        provider = self.temp_layer.dataProvider()
        

        self.temp_layer_fields = self.layer.fields()
        provider.addAttributes(self.temp_layer_fields)
        self.temp_layer.updateFields()

    def convert_features(self):

        provider = self.temp_layer.dataProvider()
        i = 0
        len = self.layer.featureCount()
        for feature in self.layer.getFeatures():
            i += 1
            if i%1000 == 0:
                self.parent.setMessage(f'Converting layer road multiline to line (link №{i} from {len})...')
                QApplication.processEvents()
                if self.verify_break():
                    return 0 
            geom = feature.geometry()
            if geom.isMultipart():
                multiline = geom.asMultiPolyline()
                if multiline:

                    start_point = multiline[0][0]
                    end_point = multiline[-1][-1]
                    linestring = QgsGeometry.fromPolylineXY([start_point, end_point])
                    

                    new_feature = QgsFeature()
                    new_feature.setGeometry(linestring)
                    new_feature.setAttributes(feature.attributes())
                    

                    provider.addFeature(new_feature)


        self.temp_layer.updateExtents()

    def add_temp_layer_to_project(self):

        QgsProject.instance().addMapLayer(self.temp_layer, False)

    def remove_temp_layer(self):
        if self.temp_layer:
            QgsProject.instance().removeMapLayer(self.temp_layer.id())
            self.temp_layer = None

    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("Process converting layer of road is break")
            if not self.already_display_break:
                self.parent.textLog.append (f'<a><b><font color="red">Process converting layer of road is break</font> </b></a>')
                self.already_display_break = True
            self.parent.progressBar.setValue(0)  
            return True
      return False
        
    def execute(self):

        self.create_temp_layer()
        self.convert_features()
        if self.verify_break():
            return 0 
        self.add_temp_layer_to_project()

        return self.temp_layer


