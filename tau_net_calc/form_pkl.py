import os
import sys
import webbrowser
import re
import configparser

from qgis.PyQt import QtCore
import qgis.core
import osgeo.gdal
import osgeo.osr

from qgis.core import (QgsProject, 
                       QgsWkbTypes, 
                       QgsVectorLayer
                       )

from PyQt5.QtCore import (Qt, 
                          QEvent, 
                          QVariant)

from PyQt5.QtWidgets import (QDialogButtonBox, 
                             QDialog, 
                             QFileDialog, 
                             QApplication,                              
                             )

from PyQt5.QtGui import QDesktopServices
from PyQt5 import uic

from GTFS import GTFS
from PKL import PKL
from datetime import datetime
from converter_layer import MultiLineStringToLineStringConverter
from common import get_qgis_info

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'pkl.ui'))

class form_pkl(QDialog, FORM_CLASS):
    def __init__(self, title):
            super().__init__()
            self.setupUi(self)
            self.setModal(False)
            self.setWindowFlags(Qt.Window);
            self.user_home = os.path.expanduser("~")
                          
            
            self.setWindowTitle(title)

            self.splitter.setSizes([10, 250])   
            

            self.tabWidget.setCurrentIndex(0) 
            self.config = configparser.ConfigParser()

            self.break_on = False
            
            self.title = title

            self.progressBar.setValue(0)
               

            self.textLog.setOpenLinks(False)
            self.textLog.anchorClicked.connect(self.openFolder)
            
            
            self.toolButton_GTFS.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToGTFS))
            self.toolButton_protocol.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToProtocols))
            

            self.showAllLayersInCombo_Point_and_Polygon(self.cmbLayers)
            self.cmbLayers.installEventFilter(self)
            self.cmbLayers_fields.installEventFilter(self)
                       
            self.showAllLayersInCombo_Line(self.cmbLayersRoad)
            self.cmbLayersRoad.installEventFilter(self)
            

            
            self.fillComboBoxFields_Id(self.cmbLayers, self.cmbLayers_fields)
           
            self.cmbLayers.currentIndexChanged.connect(
                                    lambda: self.fillComboBoxFields_Id
                                                (self.cmbLayers, self.cmbLayers_fields))

            self.btnBreakOn.clicked.connect(self.set_break_on)
            
            
            self.run_button = self.buttonBox.addButton("Run", QDialogButtonBox.ActionRole)
            self.close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            self.help_button = self.buttonBox.addButton("Help", QDialogButtonBox.HelpRole)
            
            self.run_button.clicked.connect(self.on_run_button_clicked)
            self.close_button.clicked.connect(self.on_close_button_clicked)
            self.help_button.clicked.connect(self.on_help_button_clicked)

            self.ParametrsShow()
    
    def fillComboBoxFields_Id(self, obj_layers, obj_layer_fields):
      obj_layer_fields.clear()
      selected_layer_name = obj_layers.currentText()
      layer = QgsProject.instance().mapLayersByName(selected_layer_name)[0]
    
      fields = layer.fields()
      osm_id_exists = False
    
      # Регулярное выражение для проверки наличия только цифр
      digit_pattern = re.compile(r'^\d+$')
    
      # Проверка полей по типам и значениям
      for field in fields:
        field_name = field.name()
        field_type = field.type()
        
        if field_type in (QVariant.Int, QVariant.Double, QVariant.LongLong):
            # Добавляем числовые поля
            obj_layer_fields.addItem(field_name)
            if field_name.lower() == "osm_id":
                osm_id_exists = True
        elif field_type == QVariant.String:
            # Проверяем первое значение поля на наличие только цифр
            first_value = None
            for feature in layer.getFeatures():
                first_value = feature[field_name]
                break  # Останавливаемся после первого значения
            
            if first_value is not None and digit_pattern.match(str(first_value)):
                obj_layer_fields.addItem(field_name)
                if field_name.lower() == "osm_id":
                    osm_id_exists = True
    
      if osm_id_exists:
        # Перебираем все элементы комбобокса и сравниваем их с "osm_id", игнорируя регистр
        for i in range(obj_layer_fields.count()):
            if obj_layer_fields.itemText(i).lower() == "osm_id":
                obj_layer_fields.setCurrentIndex(i)
                break
      

    def showAllLayersInCombo_Line(self, cmb):
      layers = QgsProject.instance().mapLayers().values()
      line_layers = [layer for layer in layers
                   if isinstance(layer, QgsVectorLayer) and
                   layer.geometryType() == QgsWkbTypes.LineGeometry and
                   not layer.name().startswith("Temp")]
      cmb.clear()
      for layer in line_layers:
        cmb.addItem(layer.name(), []) 

    def showAllLayersInCombo_Point_and_Polygon(self, cmb):
        layers = QgsProject.instance().mapLayers().values()
        point_layers = [layer for layer in layers 
                    if isinstance(layer, QgsVectorLayer) and 
                    (layer.geometryType() == QgsWkbTypes.PointGeometry or layer.geometryType() == QgsWkbTypes.PolygonGeometry) ]
        cmb.clear()
        for layer in point_layers:
          cmb.addItem(layer.name(), [])

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
          self.setMessage ("Choose the layer")    
          return 0
        
        
        if not (self.check_feature_from_layer()):
          self.run_button.setEnabled(True)
          return 0

        if not(self.check_type_layer_road()):
            self.run_button.setEnabled(True)
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
               
        layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['layerroad_pkl'])[0]
        self.layer_road_path = layer.dataProvider().dataSourceUri().split("|")[0]
        layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['Layer_pkl'])[0]
        self.layer_buildings_path = layer.dataProvider().dataSourceUri().split("|")[0]

        self.textLog.append(f"<a> Layer of streets and roads: {self.layer_road_path}</a>")          
        self.textLog.append(f"<a> Layer of buildings: {self.layer_buildings_path}</a>")
        self.textLog.append(f"<a> GTFS folder: {self.config['Settings']['PathToGTFS_pkl']}</a>")          
        self.textLog.append(f"<a> Folder for the pkl-dictionary: {self.config['Settings']['PathToProtocols_pkl']}</a>")          
            
        self.prepare()
        self.close_button.setEnabled(True)
       
        
    
    def on_close_button_clicked(self):
        #self.break_on = True
        self.reject()
        
    
    def on_help_button_clicked(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(current_dir, 'help', 'build', 'html')
        file = os.path.join(module_path, 'building_pkl.html')
        webbrowser.open(f'file:///{file}')
   
        
    def showFoldersDialog(self, obj):        
      folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", obj.text())
      if folder_path:  
          obj.setText(folder_path)
      else:  
          obj.setText(obj.text())   

    def readParameters(self):
      project_directory = os.path.dirname(QgsProject.instance().fileName())
      file_path = os.path.join(project_directory, 'parameters_accessibility.txt')

      self.config.read(file_path)

      if 'PathToGTFS_pkl' not in self.config['Settings']:
        self.config['Settings']['PathToGTFS_pkl'] = 'C:/'
      
      if 'PathToProtocols_pkl' not in self.config['Settings']:
        self.config['Settings']['PathToProtocols_pkl'] = 'C:/'

      if 'layerroad_pkl' not in self.config['Settings']:
        self.config['Settings']['layerroad_pkl'] = ''
      
      if 'Layer_field_pkl' not in self.config['Settings']:
        self.config['Settings']['Layer_field_pkl'] = ''    


    # update config file   
    def saveParameters(self):
      
      project_directory = os.path.dirname(QgsProject.instance().fileName())
      f = os.path.join(project_directory, 'parameters_accessibility.txt')
      
      
      self.config['Settings']['PathToProtocols_pkl'] = self.txtPathToProtocols.text()
      self.config['Settings']['PathToGTFS_pkl'] = self.txtPathToGTFS.text()
      self.config['Settings']['Layer_pkl'] = self.cmbLayers.currentText()
      self.config['Settings']['Layer_field_pkl'] = self.cmbLayers_fields.currentText()
      self.config['Settings']['LayerRoad_pkl'] = self.cmbLayersRoad.currentText()
      
            
      with open(f, 'w') as configfile:
          self.config.write(configfile)
      
         

    def ParametrsShow(self):
            
      self.readParameters()
      
      self.txtPathToGTFS.setText(self.config['Settings']['PathToGTFS_pkl'])
      self.cmbLayersRoad.setCurrentText(self.config['Settings']['Layerroad_pkl'])
      self.cmbLayers.setCurrentText(self.config['Settings']['Layer_pkl'])
      self.cmbLayers_fields.setCurrentText(self.config['Settings']['Layer_field_pkl'])
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols_pkl'])


    def check_folder_and_file(self):
     
      if not os.path.exists(self.txtPathToGTFS.text()):
        self.setMessage(f"The folder '{self.txtPathToGTFS.text()}' does not exist")
        return False
      
      required_files = ['stops.txt', 'trips.txt', 'routes.txt', 'stop_times.txt', 'calendar.txt']
      missing_files = [file for file in required_files if not os.path.isfile(os.path.join(self.txtPathToGTFS.text(), file))]

      if missing_files:
        missing_files_message = ", ".join(missing_files)
        self.setMessage (f"Files are missing in the '{self.txtPathToGTFS.text()}' forlder: {missing_files_message}")
        return False

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

    def check_type_layer_road (self):
            
      layer = self.cmbLayersRoad.currentText()
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


    def check_feature_from_layer (self):
                 
      layer = self.cmbLayers.currentText()
      layer = QgsProject.instance().mapLayersByName(layer)[0]   
     
      try:
        features = layer.getFeatures()
      except:
        self.setMessage(f'No features in the layer {layer}')
        return 0  
            
      return 1
            
    def prepare(self):
      begin_computation_time = datetime.now()
      begin_computation_str = begin_computation_time.strftime('%Y-%m-%d %H:%M:%S')
      self.textLog.append("<a style='font-weight:bold;'>[Processing]</a>")  
      self.textLog.append(f'<a>Started: {begin_computation_str}</a>') 

      self.break_on = False

      layer_road = self.config['Settings']['LayerRoad_pkl']
      layer_road = QgsProject.instance().mapLayersByName(layer_road)[0]  
      

      layer_origins = self.config['Settings']['Layer_pkl']
      layer_origins = QgsProject.instance().mapLayersByName(layer_origins)[0]
      layer_origins_field = self.config['Settings']['Layer_field_pkl']
              
      QApplication.processEvents()
      
      """
      self.txtPathToGTFS.setText(self.config['Settings']['PathToGTFS_pkl'])
      self.cmbLayersRoad.setCurrentText(self.config['Settings']['Layerroad_pkl'])  
      self.cmbLayers.setCurrentText(self.config['Settings']['Layer_pkl'])
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols_pkl'])
      """

      gtfs_path = os.path.join(self.config['Settings']['PathToProtocols_pkl'], 'GTFS')
      pkl_path = os.path.join(self.config['Settings']['PathToProtocols_pkl'], 'PKL')

      path_to_file = self.config['Settings']['PathToProtocols_pkl']+'/GTFS//'
      path_to_GTFS = self.config['Settings']['PathToGTFS_pkl']+'//'


      run = True
        
      if True:
          if not os.path.exists(gtfs_path):
            os.makedirs(gtfs_path)

          if not os.path.exists(pkl_path):
            os.makedirs(pkl_path)

          self.setMessage ('Converting multilines to lines ...')
          converter = MultiLineStringToLineStringConverter(self, layer_road)
          layer_road = converter.execute()
          
          
          if layer_road != 0:

              
            calc_GTFS = GTFS(self, 
                             path_to_file, 
                             path_to_GTFS, 
                             layer_origins, 
                             layer_road,                             
                             layer_origins_field 
                             )
            res = calc_GTFS.correcting_files()
      
            if res == 1:
                  
              calc_PKL = PKL (self, 
                              dist = 400, 
                              path_to_pkl = pkl_path, 
                              path_to_GTFS = gtfs_path, 
                              layer_buildings = layer_origins, 
                              mode_append = False
                              )
              calc_PKL.create_files()

              
          
          converter.remove_temp_layer()
          
          QApplication.processEvents()
          after_computation_time = datetime.now()
          after_computation_str = after_computation_time.strftime('%Y-%m-%d %H:%M:%S')
          self.textLog.append(f'<a>Finished: {after_computation_str}</a>')
          duration_computation = after_computation_time - begin_computation_time
          duration_without_microseconds = str(duration_computation).split('.')[0]
          self.textLog.append(f'<a>Processing time: {duration_without_microseconds}</a>') 

          if res == 1:
            self.textLog.append(f'<a href="file:///{gtfs_path}" target="_blank" >GTFS in folder</a>')
            self.textLog.append(f'<a href="file:///{pkl_path}" target="_blank" >pkl in folder</a>') 

          self.setMessage(f'Finished')
          
      
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

    
  
  
    