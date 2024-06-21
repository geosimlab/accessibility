import os
import sys
import qgis.core
from qgis.PyQt import QtCore
from qgis.core import QgsProject, QgsWkbTypes, QgsPointXY

import osgeo.gdal
import osgeo.osr

from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QFileDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QRegExp, QEvent
from PyQt5.QtGui import QRegExpValidator, QDesktopServices
from PyQt5 import uic
from ShortestPath import ShortestPathUtils
from converter_layer import MultiLineStringToLineStringConverter


import configparser



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'car.ui'))

class CarAccessibility(QDialog, FORM_CLASS):
    def __init__(self, mode, protocol_type, title):
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

            self.splitter.setSizes([10, 250])   
            

            self.tabWidget.setCurrentIndex(0) 
            self.config = configparser.ConfigParser()

            self.break_on = False
            
            self.mode = mode
            self.protocol_type = protocol_type
            self.title = title

            self.change_time = 1
            self.progressBar.setValue(0)
               

            self.textLog.setOpenLinks(False)
            self.textLog.anchorClicked.connect(self.openFolder)
            
            
            self.toolButton_protocol.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToProtocols))

            self.showAllLayersInCombo(self.cmbLayers)
            self.cmbLayers.installEventFilter(self)
            self.showAllLayersInCombo(self.cmbLayersDest)
            self.cmbLayersDest.installEventFilter(self)
            self.showAllLayersInCombo(self.cmbLayersRoad)
            self.cmbLayersRoad.installEventFilter(self)
                       
            
            self.toolButton_layer_dest_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayersDest))
            self.toolButton_layer_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayers))
            self.toolButton_layer_road_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayersRoad))
            
           
            
            self.btnBreakOn.clicked.connect(self.set_break_on)
            
            
            self.run_button = self.buttonBox.addButton("Run", QDialogButtonBox.ActionRole)
            self.close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            self.help_button = self.buttonBox.addButton("Help", QDialogButtonBox.HelpRole)
            
            self.run_button.clicked.connect(self.on_run_button_clicked)
            self.close_button.clicked.connect(self.on_close_button_clicked)
            self.help_button.clicked.connect(self.on_help_button_clicked)

            self.cbUseFields.stateChanged.connect(self.EnableComboBox)
                        
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


            self.fillComboBoxWithLayerFields()
            self.fillComboBoxWithLayerFieldsSpeed()
            self.fillComboBoxFieldsDirection()
            #self.cmbLayersDest.currentIndexChanged.connect(self.fillComboBoxWithLayerFields)
            #self.cmbLayersRoad.currentIndexChanged.connect(self.fillComboBoxWithLayerFieldsSpeed)
            self.cmbLayersRoad.currentIndexChanged.connect
            (
            lambda: (self.fillComboBoxWithLayerFieldsSpeed(), self.fillComboBoxFieldsDirection)
            )

            if self.protocol_type == 1:
              #self.txtMaxTimeTravel.setVisible(False)
              self.txtTimeInterval.setVisible(False)
              self.cmbFields.setVisible(False)
              self.cbUseFields.setVisible(False)
              self.cmbLayersDest.setVisible(False)
              self.cbSelectedOnly2.setVisible(False)
              self.toolButton_layer_dest_refresh.setVisible(False)

              self.lblFields.setVisible(False)
              self.label_6.setVisible(False)
              self.label_5.setVisible(False)



            self.ParametrsShow()
    
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
          self.setMessage ("Need choise layer")   
          return 0
        
        if self.cbUseFields.isChecked() and self.cmbFields.currentText() == "":
          self.run_button.setEnabled(True)
          self.setMessage ("Need choise field to aggregate")   
          return 0
        

        self.saveParameters()
        self.readParameters()

        
        self.setMessage ("Starting ...")
        self.close_button.setEnabled(False)
        self.textLog.clear()
        self.tabWidget.setCurrentIndex(1) 
        self.textLog.append("<a style='font-weight:bold;'>[System]</a>")
        qgis_info = self.get_qgis_info()
        
        info_str = "<br>".join([f"{key}: {value}" for key, value in qgis_info.items()])
        self.textLog.append(f'<a> {info_str}</a>')
        self.textLog.append("<a style='font-weight:bold;'>[Mode]</a>")
        self.textLog.append(f'<a> Mode: {self.title}</a>')
        config_info = self.get_config_info()
        #info_str = "<br>".join(config_info)
        info_str = "<br>".join(config_info[1:])
        self.textLog.append("<a style='font-weight:bold;'>[Settings]</a>")
        self.textLog.append(f'<a>{info_str}</a>')

        self.prepare()
        self.close_button.setEnabled(True)
       
        #self.run_button.setEnabled(True)
        
    
    def on_close_button_clicked(self):
        #self.break_on = True
        self.reject()
        
    
    def on_help_button_clicked(self):
        
        pass
   
    def showAllLayersInCombo(self, cmb):
        names = [layer.name() for layer in QgsProject.instance().mapLayers().values()]    
        #cmb = self.cmbLayers
        cmb.clear()  
        for name in names:
          cmb.addItem(name, [])       
        
        index = cmb.findText('haifa_buildings', QtCore.Qt.MatchFixedString)
        if index >= 0:
          cmb.setCurrentIndex(index)
               


    def showFoldersDialog(self, obj):        
      folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", obj.text())
      if folder_path:  
          obj.setText(folder_path)
      else:  
          obj.setText(obj.text())   

    def readParameters(self):
      self.config.read(self.user_home + "/parameters_accessibility.txt")
      if 'FieldDirection_car' not in self.config['Settings']:
        self.config['Settings']['FieldDirection_car'] = '0'
        #self.saveParameters()

    # update config file   
    def saveParameters(self):
      
      f = self.user_home + "/parameters_accessibility.txt" 
      self.config.read(f)
      
      
      self.config['Settings']['PathToProtocols_car'] = self.txtPathToProtocols.text()
      self.config['Settings']['Layer_car'] = self.cmbLayers.currentText()
      self.config['Settings']['FieldSpeed_car'] = str(self.cmbFieldsSpeed.currentIndex())
      self.config['Settings']['FieldDirection_car'] = str(self.cmbFieldsDirection.currentIndex())
      
      if hasattr(self, 'cbSelectedOnly1'):
        self.config['Settings']['SelectedOnly1_car'] = str(self.cbSelectedOnly1.isChecked())
      self.config['Settings']['LayerDest_car'] = self.cmbLayersDest.currentText()
      if hasattr(self, 'cbSelectedOnly2'):
        self.config['Settings']['SelectedOnly2_car'] = str(self.cbSelectedOnly2.isChecked())

      self.config['Settings']['LayerRoad_car'] = self.cmbLayersRoad.currentText()

      self.config['Settings']['Speed_car'] = self.txtSpeed.text()

      self.config['Settings']['Field_car'] = self.cmbFields.currentText()
      self.config['Settings']['UseField_car'] = str(self.cbUseFields.isChecked())
      self.config['Settings']['MaxTimeTravel_car'] = self.txtMaxTimeTravel.text()
      self.config['Settings']['TimeInterval_car'] = self.txtTimeInterval.text()
      

      with open(f, 'w') as configfile:
          self.config.write(configfile)
      
         

    def ParametrsShow(self):
            
      self.readParameters()
      
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols_car'])

      if isinstance(self.config['Settings']['Layer_car'], str) and self.config['Settings']['Layer_car'].strip():
        self.cmbLayers.setCurrentText(self.config['Settings']['Layer_car'])

      self.cmbFieldsSpeed.setCurrentIndex(int(self.config['Settings']['FieldSpeed_car']))  
      self.cmbFieldsDirection.setCurrentIndex(int(self.config['Settings']['FieldDirection_car']))  

      try:
        SelectedOnly1 = self.config['Settings']['SelectedOnly1_car'].lower() == "true"  
      except:
        SelectedOnly1 = False
      self.cbSelectedOnly1.setChecked(SelectedOnly1)
      
      
      if isinstance(self.config['Settings']['LayerDest_car'], str) and self.config['Settings']['LayerDest_car'].strip():  
        self.cmbLayersDest.setCurrentText(self.config['Settings']['LayerDest_car'])

      try:
        SelectedOnly2 = self.config['Settings']['SelectedOnly2_car'].lower() == "true"  
      except:
        SelectedOnly2 = False
      self.cbSelectedOnly2.setChecked(SelectedOnly2)  

      if isinstance(self.config['Settings']['LayerDest_car'], str) and self.config['Settings']['LayerDest_car'].strip():  
        self.cmbLayersDest.setCurrentText(self.config['Settings']['LayerDest_car'])

      if isinstance(self.config['Settings']['LayerRoad_car'], str) and self.config['Settings']['LayerRoad_car'].strip():  
        self.cmbLayersRoad.setCurrentText(self.config['Settings']['layerroad_car'])  

      self.cmbFieldsSpeed.setCurrentIndex(int(self.config['Settings']['fieldspeed_car']))    


      self.txtSpeed.setText(self.config['Settings']['Speed_car'])

      use_field = self.config['Settings']['UseField_car'].lower() == "true" 
      self.cbUseFields.setChecked(use_field)
      self.cmbFields.setEnabled(use_field)
      self.cmbFields.setCurrentText(self.config['Settings']['Field_car'])
      self.txtMaxTimeTravel.setText( self.config['Settings']['MaxTimeTravel_car'])
      self.txtTimeInterval.setText( self.config['Settings']['TimeInterval_car'])


    def check_folder_and_file(self):
      
      
      if not os.path.exists(self.txtPathToProtocols.text()):
        self.setMessage(f"Folder '{self.txtPathToProtocols.text()}' no exist")
        return False
            
      try:
        tmp_prefix = "write_tester";
        filename = f'{self.txtPathToProtocols.text()}//{tmp_prefix}'
        with open(filename, 'w') as f:
          f.write("test")
        os.remove(filename)
      except Exception as e:
        self.setMessage(f"Folder '{self.txtPathToProtocols.text()}' permission denied")
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
        self.setMessage(f"No features in layer '{self.cmbLayersRoad.currentText()}'")
        return 0
      
      
      for feature in features:
        feature_geometry = feature.geometry()
        feature_geometry_type = feature_geometry.type()
        break  

      
      if (feature_geometry_type != QgsWkbTypes.LineGeometry ):
        self.setMessage(f"Layer '{self.cmbLayersRoad.currentText()}' not consist line geometry")
        return 0
      
      return 1


    def get_feature_from_layer (self, limit = 0):
      
      layer = self.config['Settings']['Layer_car']
      
      layer = QgsProject.instance().mapLayersByName(layer)[0]   
      
      #layer = layer.centroid
      
      ids = []
      count = 0

      try:
        features = layer.getFeatures()
      except:
        self.setMessage(f'No features in layer {layer}')
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

      
      fields = layer.fields()
      feature_id_field = fields[0].name()
      features = layer.getFeatures()
      
      for feature in features:
        feature_geometry = feature.geometry()
        feature_geometry_type = feature_geometry.type()
        break  

      
      if (feature_geometry_type != QgsWkbTypes.PointGeometry):
        self.setMessage(f"Layer {self.config['Settings']['Layer_car']} not consist point")
        return 0  
     
      
      features = layer.getFeatures()
      if self.cbSelectedOnly1.isChecked():
         features = layer.selectedFeatures()

      
      for feature in features:
        count += 1
        id = feature[feature_id_field]  
        geom = feature.geometry()
        point = geom.asPoint() 
        
        points_to_tie = [QgsPointXY(point.x(), point.y())]
        
        ids.append((int(id), points_to_tie)) 
        if limit != 0 and count == limit:
            break 
      
      return ids
    
    def time_to_seconds(self, time_str):
      hours, minutes, seconds = map(int, time_str.split(':'))
      total_seconds = hours * 3600 + minutes * 60 + seconds
      return total_seconds
    
    def callShortestPath(self):
      
      layer_road = self.config['Settings']['LayerRoad_Car']
      layer_road = QgsProject.instance().mapLayersByName(layer_road)[0]  

      layer_origins = self.config['Settings']['Layer_Car']
      layer_origins = QgsProject.instance().mapLayersByName(layer_origins)[0]  

      path_to_protocol = self.config['Settings']['pathtoprotocols_car'] 
      #speed = float(self.config['Settings']['Speed_CAR'].replace(',', '.')) * 1000 / 3600  # from km/h to m/sec
      speed = float(self.config['Settings']['Speed_CAR'].replace(',', '.'))
      
      strategy_id = 1
      idx_field = int(self.config['Settings']['FieldSpeed_car']) - 1
      idx_field_direction = int(self.config['Settings']['FieldDirection_car']) - 1
      
      points_to_tie = self.points
      use_aggregate = self.config['Settings']['UseField_car'] == "True"
      field_aggregate = self.config['Settings']['Field_car']
      
      max_time_minutes = int(self.config['Settings']['MaxTimeTravel_car'])
      time_step_minutes = int(self.config['Settings']['TimeInterval_car'])

      self.setMessage('Preparing GTFS. Calc footpath on road. Converting layer road multiline to line ...')
      converter = MultiLineStringToLineStringConverter(self, layer_road)
      layer_road = converter.execute()
      if layer_road != 0:
        ShortestPath = ShortestPathUtils (self, layer_road, idx_field, idx_field_direction, layer_origins, points_to_tie, speed, strategy_id, path_to_protocol, max_time_minutes, time_step_minutes, self.mode, self.protocol_type, use_aggregate, field_aggregate)
        ShortestPath.run()
        
      converter.remove_temp_layer()  

    def prepare(self):  
      self.break_on = False
        
      QApplication.processEvents()
           
      sources = [] 

      self.points = self.get_feature_from_layer()
            
      if self.points == 0:
        self.setMessage(f"No exist points in layer '{self.cmbLayers.currentText()}'")
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
        msgBox.setText(f"Layer contains {len(self.points)+1} feature. No more than 10 objects are recommended. The calculations can take a long time and require a lot of resources. Are you sure?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        result = msgBox.exec_()
        if result == QMessageBox.Yes:
          run = True
        else:
          run = False
                   
      if run:
         self.callShortestPath()
         

      if not(run):
         self.run_button.setEnabled(True)
         self.close_button.setEnabled(True)
         self.textLog.clear()
         self.tabWidget.setCurrentIndex(0) 
         self.setMessage("")

         
      

    def get_qgis_info(self):
      qgis_info = {}
      qgis_info['QGIS version'] = qgis.core.Qgis.QGIS_VERSION
      qgis_info['QGIS code revision'] = qgis.core.Qgis.QGIS_RELEASE_NAME
      qgis_info['Qt version'] = qgis.PyQt.QtCore.QT_VERSION_STR
      qgis_info['Python version'] = sys.version
      qgis_info['GDAL version'] = osgeo.gdal.VersionInfo('RELEASE_NAME')
      return qgis_info
    
    def get_config_info(self):
      config_info = []
      config_info.append(f"<a></a>")              
      
      for section in self.config.sections():
        
        
        for key, value in self.config.items(section):
                    
            if key == "pathtoprotocols_car":
              config_info.append(f"<a>Output folder: {value}</a>")  

            if key == "layer_car":
              config_info.append(f"<a>Layer of origins (points/polygons): {value}</a>")

            if key == "selectedonly1_car":
              config_info.append(f"<a>Selected feature only from layer of origins (points/polygons): {value}</a>")  

            if key == "layerroad_car":
              config_info.append(f"<a>Layer of road: {value}</a>")  

            if key == "fieldspeed_car":
              config_info.append(f"<a>Field with speed: {self.cmbFieldsSpeed.currentText()}</a>")    

            if key == "fielddirection_car":
              config_info.append(f"<a>Field with direction value: {self.cmbFieldsDirection.currentText()}</a>")      
           
            if key == "speed_car":
              config_info.append(f"<a>Speed drive: {value} km/h</a>") 
            

            if self.protocol_type == 2:    
              if key == "layerdest_car":
                config_info.append(f"<a>Layer of destinations (points/polygons): {value}</a>")

              if key == "selectedonly2_car":
                config_info.append(f"<a>Selected feature only from layer of destinations (points/polygons): {value}</a>") 

              if key == "field_car":
                config_info.append(f"<a>Field to aggregate: {value}</a>")

              if key == "usefield_car":
                config_info.append(f"<a>Run aggregate: {value}</a>")      

              if key == "timeinterval_car":
                config_info.append(f"<a>Time interval between stored maps: {value} min</a>")  

              if key == "maxtimetravel_car":
                config_info.append(f"<a>Maximal time travel: {value} min</a>")           
            
      return config_info

    def fillComboBoxWithLayerFieldsSpeed(self):
      self.cmbFieldsSpeed.clear()
      selected_layer_name = self.cmbLayersRoad.currentText()
      selected_layer = QgsProject.instance().mapLayersByName(selected_layer_name)
      if selected_layer:
        layer = selected_layer[0]
          
      try:
        fields = [field.name() for field in layer.fields()]
      except:
        return 0
      
      
      self.cmbFieldsSpeed.addItem("no use field")
      for field in fields:
        self.cmbFieldsSpeed.addItem(field)

    def fillComboBoxFieldsDirection(self):
      self.cmbFieldsDirection.clear()
      selected_layer_name = self.cmbLayersRoad.currentText()
      selected_layer = QgsProject.instance().mapLayersByName(selected_layer_name)
      if selected_layer:
        layer = selected_layer[0]
          
      try:
        fields = [field.name() for field in layer.fields()]
      except:
        return 0
      
      
      self.cmbFieldsDirection.addItem("no use field")
      for field in fields:
        self.cmbFieldsDirection.addItem(field)    
    
    def fillComboBoxWithLayerFields(self):
      self.cmbFields.clear()
      selected_layer_name = self.cmbLayersDest.currentText()
      selected_layer = QgsProject.instance().mapLayersByName(selected_layer_name)
      if selected_layer:
        layer = selected_layer[0]
          
      try:
        fields = [field.name() for field in layer.fields()]
      except:
        return 0
      
      

      for field in fields:
        self.cmbFields.addItem(field)

    
    def eventFilter(self, obj, event):
        if obj == self.cmbLayers and event.type() == QEvent.Wheel:
            # Если комбо-бокс в фокусе, игнорируем событие прокрутки колесом мыши
            if self.cmbLayers.hasFocus():
                event.ignore()
                return True
            
        if obj == self.cmbLayersDest and event.type() == QEvent.Wheel:
            # Если комбо-бокс в фокусе, игнорируем событие прокрутки колесом мыши
            if self.cmbLayersDest.hasFocus():
                event.ignore()
                return True
            
         
        return super().eventFilter(obj, event)

    
  
  
    