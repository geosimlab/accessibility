import os
import sys
import qgis.core
from qgis.PyQt import QtCore
from qgis.core import QgsProject, QgsWkbTypes

import osgeo.gdal
import osgeo.osr

from PyQt5.QtWidgets import (QDialogButtonBox, 
                             QDialog, 
                             QFileDialog, 
                             QApplication, 
                             QMessageBox
                             )
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QDesktopServices
from PyQt5 import uic

from GTFS import GTFS
from PKL import PKL
from datetime import datetime
from converter_layer import MultiLineStringToLineStringConverter

import configparser



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
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
            

            self.showAllLayersInCombo(self.cmbLayers)
            self.cmbLayers.installEventFilter(self)
            
            self.showAllLayersInCombo(self.cmbLayersRoad)
            self.cmbLayersRoad.installEventFilter(self)
            
            self.toolButton_layer_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayers))
            self.toolButton_layer_road_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayersRoad))
            
           
            self.btnBreakOn.clicked.connect(self.set_break_on)
            
            
            self.run_button = self.buttonBox.addButton("Run", QDialogButtonBox.ActionRole)
            self.close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            self.help_button = self.buttonBox.addButton("Help", QDialogButtonBox.HelpRole)
            
            self.run_button.clicked.connect(self.on_run_button_clicked)
            self.close_button.clicked.connect(self.on_close_button_clicked)
            self.help_button.clicked.connect(self.on_help_button_clicked)
            
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
        
        
        if not (self.check_feature_from_layer()):
          self.run_button.setEnabled(True)
          return 0

        if self.cbRunCalcFootPathRoad.isChecked():
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
      if 'PathToGTFS_pkl' not in self.config['Settings']:
        self.config['Settings']['PathToGTFS_pkl'] = 'C:/'
      
      if 'PathToProtocols_pkl' not in self.config['Settings']:
        self.config['Settings']['PathToProtocols_pkl'] = 'C:/'

      if 'layerroad_pkl' not in self.config['Settings']:
        self.config['Settings']['layerroad_pkl'] = ''

      if 'Layer_pkl' not in self.config['Settings']:
        self.config['Settings']['Layer_pkl'] = ''    

      if 'RunCalcFootPathRoad_pkl' not in self.config['Settings']:
        self.config['Settings']['RunCalcFootPathRoad_pkl'] = 'False'  


    # update config file   
    def saveParameters(self):
      
      f = self.user_home + "/parameters_accessibility.txt" 
      self.config.read(f)
      
      
      self.config['Settings']['PathToProtocols_pkl'] = self.txtPathToProtocols.text()
      self.config['Settings']['PathToGTFS_pkl'] = self.txtPathToGTFS.text()
      self.config['Settings']['Layer_pkl'] = self.cmbLayers.currentText()
      self.config['Settings']['LayerRoad_pkl'] = self.cmbLayersRoad.currentText()
      self.config['Settings']['RunCalcFootPathRoad_pkl'] = str(self.cbRunCalcFootPathRoad.isChecked())
      
      with open(f, 'w') as configfile:
          self.config.write(configfile)
      
         

    def ParametrsShow(self):
            
      self.readParameters()
      
      self.txtPathToGTFS.setText(self.config['Settings']['PathToGTFS_pkl'])
      self.cmbLayersRoad.setCurrentText(self.config['Settings']['Layerroad_pkl'])  
      self.cmbLayers.setCurrentText(self.config['Settings']['Layer_pkl'])
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols_pkl'])

      Checked = self.config['Settings']['RunCalcFootPathRoad_pkl'].lower() == "true"  
      self.cbRunCalcFootPathRoad.setChecked(Checked)  

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
      
      if not os.path.exists(self.txtPathToGTFS.text()):
        self.setMessage(f"Folder '{self.txtPathToGTFS.text()}' no exist")
        return False
      
      required_files = ['stops.txt', 'trips.txt', 'routes.txt', 'stop_times.txt', 'calendar.txt']
      missing_files = [file for file in required_files if not os.path.isfile(os.path.join(self.txtPathToGTFS.text(), file))]

      if missing_files:
        missing_files_message = ", ".join(missing_files)
        self.setMessage(f"The following files are missing from the folder '{self.txtPathToGTFS.text()}': {missing_files_message}")
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


    def check_feature_from_layer (self):
                 
      layer = self.cmbLayers.currentText()
      layer = QgsProject.instance().mapLayersByName(layer)[0]   
     
      try:
        features = layer.getFeatures()
      except:
        self.setMessage(f'No features in layer {layer}')
        return 0  
      
      features = layer.getFeatures()
      
      for feature in features:
        feature_geometry = feature.geometry()
        feature_geometry_type = feature_geometry.type()
        break  
      
      if (feature_geometry_type != QgsWkbTypes.PointGeometry):
        self.setMessage(f"Layer {self.cmbLayers.currentText()} not consist point")
        return 0  
     
      return 1
    
    def time_to_seconds(self, time_str):
      hours, minutes, seconds = map(int, time_str.split(':'))
      total_seconds = hours * 3600 + minutes * 60 + seconds
      return total_seconds
    
    def prepare(self):
      time_start_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      self.textLog.append(f'<a>Time start computation {time_start_computation}</a>') 

      self.break_on = False

      layer_road = self.config['Settings']['LayerRoad_pkl']
      layer_road = QgsProject.instance().mapLayersByName(layer_road)[0]  

      layer_origins = self.config['Settings']['Layer_pkl']
      layer_origins = QgsProject.instance().mapLayersByName(layer_origins)[0]  
        
      QApplication.processEvents()
      
      self.txtPathToGTFS.setText(self.config['Settings']['PathToGTFS_pkl'])
      self.cmbLayersRoad.setCurrentText(self.config['Settings']['Layerroad_pkl'])  
      self.cmbLayers.setCurrentText(self.config['Settings']['Layer_pkl'])
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols_pkl'])

      gtfs_path = os.path.join(self.config['Settings']['PathToProtocols_pkl'], 'GTFS')
      pkl_path = os.path.join(self.config['Settings']['PathToProtocols_pkl'], 'PKL')

      path_to_file = self.config['Settings']['PathToProtocols_pkl']+'/GTFS//'
      path_to_GTFS = self.config['Settings']['PathToGTFS_pkl']+'//'

      RunCalcFootPathRoad = self.cbRunCalcFootPathRoad.isChecked()

      run = True

      if RunCalcFootPathRoad:
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle("Confirm")
        msgBox.setText(f"You have selected the mode for calculating footpath on roads. Calculations can take a long time. Are you sure?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        result = msgBox.exec_()
        if result == QMessageBox.Yes:
          run = True
        else:
          run = False
        
      if run:
          if not os.path.exists(gtfs_path):
            os.makedirs(gtfs_path)

          if not os.path.exists(pkl_path):
            os.makedirs(pkl_path)

          self.setMessage('Preparing GTFS. Calc footpath on road. Converting layer road multiline to line ...')
          converter = MultiLineStringToLineStringConverter(self, layer_road)
          layer_road = converter.execute()
          if layer_road != 0:
                  
            calc_GTFS = GTFS(self, path_to_file, path_to_GTFS, layer_origins, layer_road, RunCalcFootPathRoad)
            res = calc_GTFS.correcting_files()
      
            if res == 1:
              calc_PKL = PKL (self, dist = 400, path_to_pkl = pkl_path, path_to_GTFS = gtfs_path, layer_buildings = layer_origins, RunCalcFootPathRoad = RunCalcFootPathRoad)
              calc_PKL.create_files()
          
          converter.remove_temp_layer()
      
          self.setMessage(f'Calculating done')
          QApplication.processEvents()
          time_after_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
          self.textLog.append(f'<a>Time after computation {time_after_computation}</a>') 
          self.textLog.append(f'<a href="file:///{gtfs_path}" target="_blank" >GTFS in folder</a>')
          self.textLog.append(f'<a href="file:///{pkl_path}" target="_blank" >pkl in folder</a>')
      
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

            if key == "pathtogtfs_pkl":
              config_info.append(f"<a>Output folder: {value}</a>")          
          

            if key == "layer_pkl":
              config_info.append(f"<a>Layer of buildings (points/polygons): {value}</a>")

            if key == "layerroad_pkl":
              config_info.append(f"<a>Layer of road: {value}</a>")  

            if key == "pathtoprotocols_pkl":
              config_info.append(f"<a>Output folder: {value}</a>")    

            if self.cbRunCalcFootPathRoad.isChecked():
              if key == "RunCalcFootPathRoad_pkl":
                config_info.append(f"<a>Run calculation footpath on road: {value}</a>")    

            
            
      return config_info
    
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            # Если комбо-бокс в фокусе, игнорируем событие прокрутки колесом мыши
            if obj.hasFocus():
                event.ignore()
                return True
        
         
        return super().eventFilter(obj, event)

    
  
  
    