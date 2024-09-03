import os
import csv
import webbrowser
import re
from datetime import datetime


from qgis.PyQt import QtCore
from qgis.core import (QgsProject, 
                       QgsWkbTypes, 
                       QgsPointXY, 
                       QgsVectorLayer
                      )

from common import getDateTime, get_qgis_info

from PyQt5.QtWidgets import (
                            QDialogButtonBox, 
                            QDialog, 
                            QFileDialog, 
                            QApplication, 
                            QMessageBox
                            )

from PyQt5.QtCore import (Qt, 
                          QRegExp, 
                          QEvent, 
                          QVariant
                          )

from PyQt5.QtGui import QRegExpValidator, QDesktopServices
from PyQt5 import uic
from car import car_accessibility
from converter_layer import MultiLineStringToLineStringConverter

import configparser

import configparser

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'car.ui'))

class CarAccessibility(QDialog, FORM_CLASS):
    def __init__(self, 
                 mode, 
                 protocol_type, 
                 title, 
                 ):
            super().__init__()
            self.setupUi(self)
            self.setModal(False)
            self.setWindowFlags(Qt.Window);
            self.user_home = os.path.expanduser("~")
      
            self.setWindowTitle(title)

            fix_size = 12 * self.txtSpeed.fontMetrics().width('x')
            
            self.txtSpeed.setFixedWidth(fix_size)
            self.txtMaxTimeTravel.setFixedWidth(fix_size)
            self.txtTimeInterval.setFixedWidth(fix_size)

            self.splitter.setSizes([80, 100])   
            

            self.tabWidget.setCurrentIndex(0) 
            self.config = configparser.ConfigParser()
            
            self.break_on = False
            
            self.mode = mode
            self.protocol_type = protocol_type
            self.title = title

            self.folder_name_Car = ""

            self.change_time = 1
            self.progressBar.setValue(0)
               

            self.textLog.setOpenLinks(False)
            self.textLog.anchorClicked.connect(self.openFolder)
            
            
            self.toolButton_protocol.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToProtocols))

            self.showAllLayersInCombo_Point_and_Polygon(self.cmbLayers)
            self.showAllLayersInCombo_Point_and_Polygon(self.cmbLayersDest)
            self.showAllLayersInCombo_Line(self.cmbLayersRoad)

            self.cmbLayers.installEventFilter(self)
            self.cmbLayersDest.installEventFilter(self)
            self.cmbLayersRoad.installEventFilter(self)

            self.cmbFieldsSpeed.installEventFilter(self)
            self.cmbFields.installEventFilter(self)
            self.cmbFieldsDirection.installEventFilter(self)
                    
            self.showAllLayersInCombo_Polygon(self.cmbVisLayers)
            self.cmbVisLayers.installEventFilter(self)
            
            self.btnBreakOn.clicked.connect(self.set_break_on)
            
            
            self.run_button = self.buttonBox.addButton("Run", QDialogButtonBox.ActionRole)
            self.close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            self.help_button = self.buttonBox.addButton("Help", QDialogButtonBox.HelpRole)
            
            self.run_button.clicked.connect(self.on_run_button_clicked)
            self.close_button.clicked.connect(self.on_close_button_clicked)
            self.help_button.clicked.connect(self.on_help_button_clicked)
           
                        
            # Создание экземпляра регулярного выражения для целых чисел
            regex1 = QRegExp(r"\d*")     
            int_validator1 = QRegExpValidator(regex1)
            
            # 0,1,2
            regex2 = QRegExp(r"[0-2]{1}")
            int_validator2 = QRegExpValidator(regex2)

             # floating, two digit after dot
            regex3 = QRegExp(r"^\d+(\.\d{1,2})?$")
            int_validator3 = QRegExpValidator(regex3)
            
            self.txtSpeed.setValidator(int_validator3)
            self.txtMaxTimeTravel.setValidator(int_validator3)
            self.txtTimeInterval.setValidator(int_validator3)


            self.cmbLayers_fields.installEventFilter(self)
            self.cmbLayersDest_fields.installEventFilter(self)
            self.cmbVisLayers_fields.installEventFilter(self)
            
            self.cmbLayersRoad_type_road.installEventFilter(self)
            self.cmbFieldsSpeed.installEventFilter(self)
            self.cmbFieldsDirection.installEventFilter(self)
            
            ########
            self.onLayerRoadChanged()
            self.cmbLayersRoad.currentIndexChanged.connect(self.onLayerRoadChanged)

            self.onLayerDestChanged()
            self.cmbLayersDest.currentIndexChanged.connect(self.onLayerDestChanged)
            #########

            self.fillComboBoxFields_Id (self.cmbLayers, 
                                        self.cmbLayers_fields, 
                                        "osm_id", 
                                        only_digit=True)
            
            self.cmbLayers.currentIndexChanged.connect(
                                    lambda: self.fillComboBoxFields_Id
                                                (self.cmbLayers, 
                                                 self.cmbLayers_fields, 
                                                 "osm_id", 
                                                 only_digit=True))

            
            
            self.fillComboBoxFields_Id (self.cmbVisLayers, 
                                        self.cmbVisLayers_fields, 
                                        "osm_id", 
                                        only_digit=True)
            self.cmbVisLayers.currentIndexChanged.connect(
                                    lambda: self.fillComboBoxFields_Id
                                                (self.cmbVisLayers, 
                                                 self.cmbVisLayers_fields, 
                                                 "osm_id", 
                                                 only_digit=True))
            

            if self.protocol_type == 2:
              
              self.txtTimeInterval.setVisible(False)
              self.cmbFields.setVisible(False)
              self.cbUseFields.setVisible(False)
              
              self.lblFields.setVisible(False)
              self.label_6.setVisible(False)

            self.default_aliase = f'acc_car_{getDateTime()}'  

            self.ParametrsShow()
            self.textInfo.anchorClicked.connect(self.open_file)
            self.read_road_speed_default()

            if mode == 2:
               self.label_17.setText ("Destinations")
               self.label_5.setText ("Origins")

                

    def onLayerDestChanged (self):
       
       self.fillComboBoxFields_Id (self.cmbLayersDest, 
                                        self.cmbLayersDest_fields, 
                                        "osm_id", 
                                        only_digit=True)
       
       self.fillComboBoxFields_Id (self.cmbLayersDest, 
                                        self.cmbFields, 
                                        "", 
                                        only_digit=True)
       

    
    def onLayerRoadChanged(self):
        # Обновляем поля для скорости
        self.fillComboBoxFields_Id(self.cmbLayersRoad, 
                               self.cmbFieldsSpeed, 
                               "maxspeed", 
                               only_digit=True)
    
        # Обновляем поля для направления
        self.fillComboBoxFields_Id(self.cmbLayersRoad, 
                               self.cmbFieldsDirection, 
                               "oneway", 
                               only_digit=False)
    
        # Обновляем поля для типа дороги
        self.fillComboBoxFields_Id(self.cmbLayersRoad, 
                               self.cmbLayersRoad_type_road, 
                               "fclass", 
                               only_digit=False)
    
        
        
    def fillComboBoxFields_Id(self, obj_layers, obj_layer_fields, field_name_default, only_digit=True):
      obj_layer_fields.clear()
      selected_layer_name = obj_layers.currentText()
      layer = QgsProject.instance().mapLayersByName(selected_layer_name)[0]

      fields = layer.fields()
      field_name_default_exists = False

      # Регулярное выражение для проверки наличия только цифр
      digit_pattern = re.compile(r'^\d+$')

      # Проверка полей по типам и значениям
      for field in fields:
        field_name = field.name()
        field_type = field.type()

        if field_type in (QVariant.Int, QVariant.Double, QVariant.LongLong):
            # Добавляем числовые поля
            obj_layer_fields.addItem(field_name)
            if field_name.lower() == field_name_default:
                field_name_default_exists = True
        elif field_type == QVariant.String:
            # Проверяем первое значение поля на наличие только цифр, если only_digit = True
            if only_digit:
                first_value = None
                for feature in layer.getFeatures():
                    first_value = feature[field_name]
                    break  # Останавливаемся после первого значения

                if first_value is not None and digit_pattern.match(str(first_value)):
                    obj_layer_fields.addItem(field_name)
                    if field_name.lower() == field_name_default:
                        field_name_default_exists = True
            else:
                # Если проверка отключена, просто добавляем строковые поля
                obj_layer_fields.addItem(field_name)
                if field_name.lower() == field_name_default:
                    field_name_default_exists = True

      if field_name_default_exists:
        # Перебираем все элементы комбобокса и сравниваем их с "osm_id", игнорируя регистр
        for i in range(obj_layer_fields.count()):
            if obj_layer_fields.itemText(i).lower() == field_name_default:
                obj_layer_fields.setCurrentIndex(i)
                break

            
    def open_file(self, url):
        file_path = url.toLocalFile()
        if os.path.isfile(file_path):
            os.startfile(file_path)
        self.read_road_speed_default()    

    def show_info_speed_default (self):
        
        html = f"""
        <a>Default speed values for different road types are set in the file</a><br> 
        <a href="file:///{self.file_path}" target="_blank">{self.file_path}</a>
        """
        
        html += "<table border='1' cellspacing='0' cellpadding='5'>"
        html += "<tr><th>type_road</th><th>speed_default</th></tr>"
        for type_road, speed_default in self.type_road_speed_default.items():
            html += f"<tr><td>{type_road}</td><td>{speed_default}</td></tr>"
        html += "</table>"
        self.textInfo.setHtml(html)
    
    def EnableComboBox(self, state):
      
      if state == QtCore.Qt.Checked:
        self.cmbFields.setEnabled(True)
      else:
        self.cmbFields.setEnabled(False)

    #def openExternalLink(self, url):
    #    QDesktopServices.openUrl(QUrl(url))

    def openFolder(self, url):
        QDesktopServices.openUrl(url)
        

    def set_break_on (self):
      self.break_on = True
      self.close_button.setEnabled(True)
      #self.run_button.setEnabled(True)

    def on_run_button_clicked(self):
        self.run_button.setEnabled(False)
        

        self.break_on = False
        if not (self.check_folder_and_file()):
           self.run_button.setEnabled(True)
           return 0
        if not self.cmbLayers.currentText():
          self.run_button.setEnabled(True)
          self.setMessage ("Select the layer")   
          return 0
        
        if self.cbUseFields.isChecked() and self.cmbFields.currentText() == "":
          self.run_button.setEnabled(True)
          self.setMessage ("Select the field to aggregate")   
          return 0
        

        self.saveParameters()
        self.readParameters()

        
        self.setMessage ("Starting ...")
        self.close_button.setEnabled(False)
        self.textLog.clear()
        self.tabWidget.setCurrentIndex(1) 
        self.textLog.append("<a style='font-weight:bold;'>[System]</a>")
        qgis_info = get_qgis_info()
        
        info_str = "<br>".join([f"{key}: {value}" for key, value in qgis_info.items()])
        self.textLog.append(f'<a> {info_str}</a>')
        self.textLog.append("<a style='font-weight:bold;'>[Mode]</a>")
        self.textLog.append(f'<a> Mode: {self.title}</a>')
        
        self.textLog.append("<a style='font-weight:bold;'>[Settings]</a>")
        self.textLog.append(f'<a> Scenario name: {self.aliase}</a>')
        
        self.textLog.append(f'<a> Output folder: {self.config['Settings']['pathtoprotocols_car']}</a>')

        self.textLog.append(f'<a> Layer of roads: {self.layer_road_path}</a>')

        if self.mode == 1:
           name1 = "origins"
           name2 = "destinations"
        else:   
           name2 = "origins"
           name1 = "destinations"
        self.textLog.append(f'<a> Layer of {name1}: {self.layer_origins_path}</a>')
        self.textLog.append(f'<a> Selected {name1}: {self.config['Settings']['selectedonly1_car']}</a>')
        self.textLog.append(f'<a> Layer of {name2}: {self.layer_destinations_path}</a>')
        self.textLog.append(f'<a> Selected {name2}: {self.config['Settings']['selectedonly2_car']}</a>')

        self.textLog.append("<a style='font-weight:bold;'>[Parameters of a trip]</a>")
        
        self.textLog.append(f'<a> Default speed value: {self.config['Settings']['speed_car']} km/h</a>')
        self.textLog.append(f'<a> Maximum total travel time: {self.config['Settings']['maxtimetravel_car']} min</a>')

        if self.protocol_type == 1: # MAP mode
          self.textLog.append("<a style='font-weight:bold;'>[Aggregation]</a>")  
          self.textLog.append(f'<a> Store the results at a time resolution of: {self.config['Settings']['timeinterval_car']} min</a>')

          if self.mode == 1:  
            count_features = self.count_layer_destinations
          else:   
            count_features = self.count_layer_origins
          self.textLog.append(f'<a> Count: {count_features}</a>')

          #if self.config['Settings']['field_ch_car'] != "":
          #   print_fields = self.config['Settings']['field_ch_car']
          #else:
          #   print_fields = "NONE"
          #self.textLog.append(f'<a> Aggregated fields: {print_fields}</a>')
                      
        self.textLog.append("<a style='font-weight:bold;'>[Visualization]</a>")  
        self.textLog.append(f'<a> Layer for visualization: {self.layer_visualization_path}</a>')

        self.textLog.append("<a style='font-weight:bold;'>[Processing]</a>") 

        self.prepare()
        self.close_button.setEnabled(True)
       
        #self.run_button.setEnabled(True)
        
    
    def on_close_button_clicked(self):
        #self.break_on = True
        self.reject()
        
    
    def on_help_button_clicked(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(current_dir, 'help', 'build', 'html')
        file = os.path.join(module_path, 'car_accessibility.html')
        webbrowser.open(f'file:///{file}')

    def showAllLayersInCombo_Point_and_Polygon(self, cmb):
        layers = QgsProject.instance().mapLayers().values()
        point_layers = [layer for layer in layers 
                    if isinstance(layer, QgsVectorLayer) and 
                    (layer.geometryType() == QgsWkbTypes.PointGeometry or layer.geometryType() == QgsWkbTypes.PolygonGeometry) ]
        cmb.clear()
        for layer in point_layers:
          cmb.addItem(layer.name(), [])

    def showAllLayersInCombo_Polygon(self, cmb):
      layers = QgsProject.instance().mapLayers().values()
      polygon_layers = [layer for layer in layers 
                      if isinstance(layer, QgsVectorLayer) and 
                      layer.geometryType() == QgsWkbTypes.PolygonGeometry and
                      layer.featureCount() > 1]
      cmb.clear()
      for layer in polygon_layers:
        cmb.addItem(layer.name(), [])

    def showAllLayersInCombo_Line(self, cmb):
      layers = QgsProject.instance().mapLayers().values()
      line_layers = [layer for layer in layers
                   if isinstance(layer, QgsVectorLayer) and
                   layer.geometryType() == QgsWkbTypes.LineGeometry and
                   not layer.name().startswith("Temp")]
      cmb.clear()
      for layer in line_layers:
        cmb.addItem(layer.name(), [])      

    def showAllLayersInCombo(self, cmb):
        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]    
        
        cmb.clear()  
        for name in names:
          cmb.addItem(name, [])       
        

    def showFoldersDialog(self, obj):        
      folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", obj.text())
      if folder_path:  
          obj.setText(folder_path)
      else:  
          obj.setText(obj.text())   

    def read_road_speed_default (self):
      project_directory = os.path.dirname(QgsProject.instance().fileName())
      self.file_path = os.path.join(project_directory, "taunetcalc_type_road.csv")  
      
      self.type_road_speed_default = {}

      with open(self.file_path, mode='r', newline='', encoding='utf-8') as file:
          reader = csv.DictReader(file)
          for row in reader:
              try:
                type_road = row['type_road']
                speed_default = int(row['speed_default']) 
                self.type_road_speed_default[type_road] = speed_default
              except:
                continue  

      self.show_info_speed_default()

    def readParameters(self):
      project_directory = os.path.dirname(QgsProject.instance().fileName())
      file_path = os.path.join(project_directory, 'parameters_accessibility.txt')

      self.config.read(file_path)
      if 'FieldDirection_car' not in self.config['Settings']:
        self.config['Settings']['FieldDirection_car'] = '0'

      if 'LayerRoad_type_road_car' not in self.config['Settings']:
        self.config['Settings']['LayerRoad_type_road_car'] = '0'

      if 'Layer_field_car' not in self.config['Settings']:
        self.config['Settings']['Layer_field_car'] = '0'

      if 'LayerDest_field_car' not in self.config['Settings']:
        self.config['Settings']['LayerDest_field_car'] = '0'


      if 'VisLayer_field_car' not in self.config['Settings']:
        self.config['Settings']['VisLayer_field_car'] = '0'        


    # update config file   
    def saveParameters(self):
      
      project_directory = os.path.dirname(QgsProject.instance().fileName())
      f = os.path.join(project_directory, 'parameters_accessibility.txt')

      self.config.read(f)
      
      self.config['Settings']['PathToProtocols_car'] = self.txtPathToProtocols.text()
      self.config['Settings']['Layer_car'] = self.cmbLayers.currentText()
      self.config['Settings']['Layer_field_car'] = self.cmbLayers_fields.currentText()

      self.config['Settings']['LayerDest_car'] = self.cmbLayersDest.currentText()
      self.config['Settings']['LayerDest_field_car'] = self.cmbLayersDest_fields.currentText()
      
      layer_road = QgsProject.instance().mapLayersByName(self.cmbLayersRoad.currentText())[0]
      self.idx_field_speed = layer_road.fields().indexFromName(self.cmbFieldsSpeed.currentText())
      self.config['Settings']['FieldSpeed_car'] = str(self.cmbFieldsSpeed.currentText())

      self.idx_field_direction = layer_road.fields().indexFromName(self.cmbFieldsDirection.currentText())
      self.config['Settings']['FieldDirection_car'] = str(self.cmbFieldsDirection.currentIndex())
      
      if hasattr(self, 'cbSelectedOnly1'):
        self.config['Settings']['SelectedOnly1_car'] = str(self.cbSelectedOnly1.isChecked())
      self.config['Settings']['LayerDest_car'] = self.cmbLayersDest.currentText()
      if hasattr(self, 'cbSelectedOnly2'):
        self.config['Settings']['SelectedOnly2_car'] = str(self.cbSelectedOnly2.isChecked())

      self.config['Settings']['LayerRoad_car'] = self.cmbLayersRoad.currentText()
      self.config['Settings']['LayerRoad_type_road_car'] = self.cmbLayersRoad_type_road.currentText()

      self.config['Settings']['Speed_car'] = self.txtSpeed.text()

      self.config['Settings']['Field_car'] = self.cmbFields.currentText()
      self.config['Settings']['UseField_car'] = str(self.cbUseFields.isChecked())
      self.config['Settings']['MaxTimeTravel_car'] = self.txtMaxTimeTravel.text()
      self.config['Settings']['TimeInterval_car'] = self.txtTimeInterval.text()

      self.config['Settings']['LayerVis_car'] = self.cmbVisLayers.currentText()
      self.config['Settings']['VisLayer_field_car'] = self.cmbVisLayers_fields.currentText()

      with open(f, 'w') as configfile:
          self.config.write(configfile)

      self.aliase = self.txtAliase.text() if self.txtAliase.text() != "" else self.default_aliase

      layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['Layer_car'])[0]
      self.count_layer_origins =  layer.featureCount()  
      self.layer_origins_path = layer.dataProvider().dataSourceUri().split("|")[0]

      layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['LayerDest_car'])[0]
      self.layer_destinations_path = layer.dataProvider().dataSourceUri().split("|")[0]
      self.count_layer_destinations =  layer.featureCount()

      layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['LayerViz_car'])[0]
      self.layer_visualization_path = layer.dataProvider().dataSourceUri().split("|")[0]

      layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['LayerRoad_car'])[0]
      self.layer_road_path = layer.dataProvider().dataSourceUri().split("|")[0]
       

    def ParametrsShow(self):
            
      self.readParameters()
      
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols_car'])
      self.cmbLayers.setCurrentText(self.config['Settings']['Layer_car'])

      try:
        SelectedOnly1 = self.config['Settings']['SelectedOnly1_car'].lower() == "true"  
      except:
        SelectedOnly1 = False
      self.cbSelectedOnly1.setChecked(SelectedOnly1)

      self.cmbLayersDest.setCurrentText(self.config['Settings']['LayerDest_car'])

      try:
        SelectedOnly2 = self.config['Settings']['SelectedOnly2_car'].lower() == "true"  
      except:
        SelectedOnly2 = False
      self.cbSelectedOnly2.setChecked(SelectedOnly2)  

      self.cmbLayersDest.setCurrentText(self.config['Settings']['LayerDest_car'])
      self.cmbLayersRoad.setCurrentText(self.config['Settings']['layerroad_car'])  


      self.cmbFieldsSpeed.setCurrentText(self.config['Settings']['FieldSpeed_car'])    
      self.cmbFieldsDirection.setCurrentText(self.config['Settings']['FieldDirection_car'])  
      self.txtSpeed.setText(self.config['Settings']['Speed_car'])

      use_field = self.config['Settings']['UseField_car'].lower() == "true" 
      self.cbUseFields.setChecked(use_field)
      self.cmbFields.setEnabled(use_field)
      
      self.cmbFields.setCurrentText(self.config['Settings']['Field_car'])
      self.txtMaxTimeTravel.setText( self.config['Settings']['MaxTimeTravel_car'])
      self.txtTimeInterval.setText( self.config['Settings']['TimeInterval_car'])

      layer = self.config.get('Settings', 'LayerVis_car', fallback=None)
      if isinstance(layer, str) and layer.strip():
          self.cmbVisLayers.setCurrentText(layer)


      self.cmbLayersRoad_type_road.setCurrentText(self.config['Settings']['LayerRoad_type_road_car'])
      self.cmbLayers_fields.setCurrentText(self.config['Settings']['Layer_field_car'])
      self.cmbLayersDest_fields.setCurrentText(self.config['Settings']['LayerDest_field_car'])
      self.cmbVisLayers_fields.setCurrentText(self.config['Settings']['VisLayer_field_car'])

      self.txtAliase.setText (self.default_aliase)

    def check_folder_and_file(self):
      
      
      if not os.path.exists(self.txtPathToProtocols.text()):
        self.setMessage(f"The folder '{self.txtPathToProtocols.text()}' does not exist")
        return False
            
      try:
        tmp_prefix = "write_tester";
        filename = f'{self.txtPathToProtocols.text()}//{tmp_prefix}'
        with open(filename, 'w') as f:
          f.write("test")
        os.remove(filename)
      except Exception as e:
        self.setMessage (f"An access to the folder '{self.txtPathToProtocols.text()}' is denied")
        return False
    
      return True

    def setMessage (self, message):
      self.lblMessages.setText(message)

    def check_type_layer_road (self, limit = 0):
      
      layer = self.config['Settings']['LayerRoad_car']
      layer = QgsProject.instance().mapLayersByName(layer)[0]

      try:
        features = layer.getFeatures()
      except:
        self.setMessage(f"No features in the layer '{self.cmbLayersRoad.currentText()}'")
        return 0
      
      
      for feature in features:
        feature_geometry = feature.geometry()
        feature_geometry_type = feature_geometry.type()
        break  

      
      if (feature_geometry_type != QgsWkbTypes.LineGeometry ):
        self.setMessage (f"The features in the layer '{self.cmbLayersRoad.currentText()}' must be polylines")
        return 0
      
      return 1


    def get_feature_from_layer (self, limit = 0):
      
      layer = self.config['Settings']['Layer_car']
      
      layer = QgsProject.instance().mapLayersByName(layer)[0]   
      
      ids = []
      count = 0

      try:
        features = layer.getFeatures()
      except:
        self.setMessage (f'The layer {layer} is empty')

        return 0  

      if self.cbSelectedOnly1.isChecked():
         features = layer.selectedFeatures()
         
         if len(features) == 0:
         
          msgBox = QMessageBox()
          msgBox.setIcon(QMessageBox.Information)
          msgBox.setText(f"You selected an option for layer of origins 'Selected features only' \n  but did not selected any objects in the layer '{self.config['Settings']['Layer_car']}'")
          msgBox.setWindowTitle("Information")
          msgBox.setStandardButtons(QMessageBox.Ok)
          msgBox.exec_()
          return 0
    
      feature_id_field = self.config['Settings']['Layer_field']
      
      features = layer.getFeatures()
      if self.cbSelectedOnly1.isChecked():
         features = layer.selectedFeatures()

      
      for feature in features:
        count += 1
        id = feature[feature_id_field]  
        geom = feature.geometry()

        if geom.type() == QgsWkbTypes.PointGeometry:
          point = geom.asPoint()
        elif geom.type() == QgsWkbTypes.PolygonGeometry:
          point = geom.centroid().asPoint()
                
        points_to_tie = [QgsPointXY(point.x(), point.y())]
        
        ids.append((int(id), points_to_tie)) 
        if limit != 0 and count == limit:
            break 
      
      return ids
            
    def call_car_accessibility(self):
      
      layer_road = self.config['Settings']['LayerRoad_Car']
      layer_road = QgsProject.instance().mapLayersByName(layer_road)[0]  

      layer_origins = self.config['Settings']['Layer_Car']
      layer_origins = QgsProject.instance().mapLayersByName(layer_origins)[0]  

      layer_dest = self.config['Settings']['LayerDest_Car']
      layer_dest = QgsProject.instance().mapLayersByName(layer_dest)[0]  

      path_to_protocol = self.config['Settings']['pathtoprotocols_car'] 
      #speed = float(self.config['Settings']['Speed_CAR'].replace(',', '.')) * 1000 / 3600  # from km/h to m/sec
      speed = float(self.config['Settings']['Speed_CAR'].replace(',', '.'))
      
      strategy_id = 1
      #idx_field = int(self.config['Settings']['FieldSpeed_car']) 
      #idx_field_direction = int(self.config['Settings']['FieldDirection_car']) 
      
      points_to_tie = self.points
      use_aggregate = self.config['Settings']['UseField_car'] == "True"
      field_aggregate = self.config['Settings']['Field_car']
      
      max_time_minutes = int(self.config['Settings']['MaxTimeTravel_car'])
      time_step_minutes = int(self.config['Settings']['TimeInterval_car'])

      layer_vis = self.config['Settings']['layervis_car']

      layer_road_type_road = self.config['Settings']['LayerRoad_type_road_car']
      layer_field = self.config['Settings']['Layer_field_car']
      layerdest_field = self.config['Settings']['LayerDest_field_car']
      layer_vis_field = self.config['Settings']['VisLayer_field_car']

      aliase = self.txtAliase.text() if self.txtAliase.text() != "" else self.default_aliase

      begin_computation_time = datetime.now()
      begin_computation_str = begin_computation_time.strftime('%Y-%m-%d %H:%M:%S')
      self.textLog.append(f'<a>Started: {begin_computation_str}</a>')
      
      self.setMessage('Converting multilines to lines ...')
      converter = MultiLineStringToLineStringConverter(self, layer_road)
      layer_road = converter.execute()


      if layer_road != 0:
        car = car_accessibility (self, 
                                          layer_road, 
                                          self.idx_field_speed, 
                                          self.idx_field_direction, 
                                          layer_origins,
                                          layer_dest, 
                                          points_to_tie, 
                                          speed, 
                                          strategy_id, 
                                          path_to_protocol, 
                                          max_time_minutes, 
                                          time_step_minutes, 
                                          self.mode, 
                                          self.protocol_type, 
                                          use_aggregate, 
                                          field_aggregate,
                                          self.type_road_speed_default,
                                          layer_vis,
                                          layer_road_type_road, 
                                          layerdest_field,
                                          layer_vis_field,
                                          aliase,
                                          )
        car.run(begin_computation_time)
        
      converter.remove_temp_layer()
  
    def prepare(self):  
      self.break_on = False
        
      QApplication.processEvents()
           
      sources = [] 

      self.points = self.get_feature_from_layer()
            
      if self.points == 0:
        #self.setMessage (f"No features in the layer '{self.cmbLayers.currentText()}'")
        self.run_button.setEnabled(True)
        return 0
      
      if not(self.check_type_layer_road()):
         self.run_button.setEnabled(True)
         return 0
         
         
      
      run = True
      if len(self.points) > 10:
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle("Confirm")
        msgBox.setText(
                        f"Layer contains {len(self.points)+1} feature.\n"
                        "No more than 10 objects are recommended.\n"
                        "The calculations can take a long time and require a lot of resources. Are you sure?"
                      )
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        result = msgBox.exec_()
        if result == QMessageBox.Yes:
          run = True
        else:
          run = False
                   
      if run:
         self.call_car_accessibility()
         

      if not(run):
         self.run_button.setEnabled(True)
         self.close_button.setEnabled(True)
         self.textLog.clear()
         self.tabWidget.setCurrentIndex(0) 
         self.setMessage("")

        
    def eventFilter(self, obj, event):
        
        if event.type() == QEvent.Wheel:
            # Если комбо-бокс в фокусе, игнорируем событие прокрутки колесом мыши
            if obj.hasFocus():
                event.ignore()
                return True
         
        return super().eventFilter(obj, event)

    
  
  
    