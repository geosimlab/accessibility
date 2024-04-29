import os

import sys
import qgis.core
import osgeo.gdal
import osgeo.osr

from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QFileDialog, QApplication
from PyQt5.QtCore import QRegExp, QDateTime
from PyQt5.QtGui import QRegExpValidator

from PyQt5 import uic
from PyQt5.QtGui import QDesktopServices

from qgis.PyQt import QtCore
from qgis.core import QgsProject,QgsWkbTypes
from datetime import datetime, date

from query_file import runRaptorWithProtocol


import configparser

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'raptor.ui'))

class RaptorDetailed(QDialog, FORM_CLASS):
    def __init__(self, mode, protocol_type, title = "Raptor detailed"):
            super().__init__()
            self.setupUi(self)
            self.user_home = os.path.expanduser("~")
            
            self.setWindowTitle(title)
            self.tabWidget.setCurrentIndex(0) 
            self.config = configparser.ConfigParser()
            self.break_on = False
            
            self.mode = mode
            self.protocol_type = protocol_type
            self.title = title
            self.change_time = 1
            #self.stops_id_name = "stop_id"
            #self.stops_build_name = "osm_id"
            self.progressBar.setValue(0)

            self.txtTimeInterval.setVisible(False)
            self.lblTimeInterval.setVisible(False)
            self.cmbFields.setVisible(False)
            self.lblFields.setVisible(False)
            self.cbUseFields.setVisible(False)

            self.textLog.setOpenLinks(False)
            self.textLog.anchorClicked.connect(self.openFolder)
            
            self.toolButton_PKL.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToPKL))
            self.toolButton_protocol.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToProtocols))

            self.showAllLayersInCombo(self.cmbLayers)
            self.showAllLayersInCombo(self.cmbLayersDest)
            
            self.toolButton_layer_dest_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayersDest))
            self.toolButton_layer_refresh.clicked.connect(lambda: self.showAllLayersInCombo(self.cmbLayers))
           
            
            self.btnBreakOn.clicked.connect(self.set_break_on)
            
            
            self.run_button = self.buttonBox.addButton("Run", QDialogButtonBox.ActionRole)
            self.close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            self.help_button = self.buttonBox.addButton("Help", QDialogButtonBox.HelpRole)
            
            self.run_button.clicked.connect(self.on_run_button_clicked)
            self.close_button.clicked.connect(self.on_close_button_clicked)
            self.help_button.clicked.connect(self.on_help_button_clicked)
                        
            # Создание экземпляра регулярного выражения для целых чисел
            regex = QRegExp(r"\d*")     
            int_validator1 = QRegExpValidator(regex)
            
            # 0,1,2
            regex2 = QRegExp(r"[0-2]{1}")
            int_validator2 = QRegExpValidator(regex2)

            self.txtMinTransfers.setValidator(int_validator2)
            self.txtMaxTransfers.setValidator(int_validator2)
            self.txtMaxWalkDist1.setValidator(int_validator1)
            self.txtMaxWalkDist2.setValidator(int_validator1)
            self.txtMaxWalkDist3.setValidator(int_validator1)
            self.txtSpeed.setValidator(int_validator1)
            self.txtMaxWaitTime.setValidator(int_validator1)
            self.txtMaxWaitTimeTransfer.setValidator(int_validator1)
            self.txtMaxTimeTravel.setValidator(int_validator1)
            self.txtVoronoi.setValidator(int_validator1)

            self.ParametrsShow()

    def openFolder(self, url):
        QDesktopServices.openUrl(url)
        

    def set_break_on (self):
      self.break_on = True
      self.run_button.setEnabled(True)

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
        
        self.saveParameters()
        self.readParameters()

        
        self.setMessage ("Starting ...")
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

        self.prepareRaptor()
       
        self.run_button.setEnabled(True)
        
    
    def on_close_button_clicked(self):
        self.break_on = True
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

    # update config file   
    def saveParameters(self):

      f = self.user_home + "/parameters_accessibility.txt" 
      self.config.read(f)
      
      self.config['Settings']['PathToPKL'] = self.txtPathToPKL.text()
      self.config['Settings']['PathToProtocols'] = self.txtPathToProtocols.text()
      self.config['Settings']['Layer'] = self.cmbLayers.currentText()
      self.config['Settings']['LayerDest'] = self.cmbLayersDest.currentText()
      self.config['Settings']['Min_transfer'] = self.txtMinTransfers.text()
      self.config['Settings']['Max_transfer'] = self.txtMaxTransfers.text()
      self.config['Settings']['MaxWalkDist1'] = self.txtMaxWalkDist1.text()
      self.config['Settings']['MaxWalkDist2'] = self.txtMaxWalkDist2.text()
      self.config['Settings']['MaxWalkDist3'] = self.txtMaxWalkDist3.text()
      self.config['Settings']['TIME'] = self.dtStartTime.dateTime().toString("HH:mm:ss")
      self.config['Settings']['Speed'] = self.txtSpeed.text()
      self.config['Settings']['MaxWaitTime'] = self.txtMaxWaitTime.text()
      self.config['Settings']['MaxWaitTimeTranfer'] = self.txtMaxWaitTimeTransfer.text()
      self.config['Settings']['MaxTimeTravel'] = self.txtMaxTimeTravel.text()
      self.config['Settings']['Voronoi'] = self.txtVoronoi.text()

      with open(f, 'w') as configfile:
          self.config.write(configfile)
      
         

    def ParametrsShow(self):
            
      self.readParameters()
      self.txtPathToPKL.setText(self.config['Settings']['PathToPKL'])
      self.txtPathToProtocols.setText(self.config['Settings']['PathToProtocols'])

      if isinstance(self.config['Settings']['Layer'], str) and self.config['Settings']['Layer'].strip():
        self.cmbLayers.setCurrentText(self.config['Settings']['Layer'])

      if isinstance(self.config['Settings']['LayerDest'], str) and self.config['Settings']['LayerDest'].strip():  
        self.cmbLayersDest.setCurrentText(self.config['Settings']['LayerDest'])

      
      self.txtMinTransfers.setText(self.config['Settings']['Min_transfer'])
      self.txtMaxTransfers.setText(self.config['Settings']['Max_transfer'])
      self.txtMaxWalkDist1.setText(self.config['Settings']['MaxWalkDist1'])
      self.txtMaxWalkDist2.setText(self.config['Settings']['MaxWalkDist2'])
      self.txtMaxWalkDist3.setText(self.config['Settings']['MaxWalkDist3'])

            
      datetime = QDateTime.fromString(self.config['Settings']['TIME'], "HH:mm:ss")
      self.dtStartTime.setDateTime(datetime)

      self.txtSpeed.setText(self.config['Settings']['Speed'])
      self.txtMaxWaitTime.setText(self.config['Settings']['MaxWaitTime'])
      self.txtMaxWaitTimeTransfer.setText(self.config['Settings']['MaxWaitTimeTranfer'])
      self.txtMaxTimeTravel.setText( self.config['Settings']['MaxTimeTravel'])
      
      self.txtVoronoi.setText(self.config['Settings']['Voronoi'])

    def check_folder_and_file(self):
      
      if not os.path.exists(self.txtPathToPKL.text()):
        self.setMessage(f"Folder '{self.txtPathToPKL.text()}' no exist")
        return False
      
      file_path = os.path.join(self.txtPathToPKL.text(), 'stops_dict_pkl.pkl')
      if not os.path.isfile(file_path):
        self.setMessage(f"PKL files no founded in folder '{self.txtPathToPKL.text()}'")
        return False
      
      if not os.path.exists(self.txtPathToProtocols.text()):
        self.setMessage(f"Folder '{self.txtPathToProtocols.text()}' no exist")
        return False
      
      #if not (os.access(self.txtPathToProtocols.text(), os.W_OK)):
      #  self.setMessage(f"Folder '{self.txtPathToProtocols.text()}' permission denied")
      #  return False

      try:
        tmp_prefix = "write_tester";
        filename = f'{self.txtPathToProtocols.text()}\\{tmp_prefix}'
        with open(filename, 'w') as f:
          f.write("test")
        os.remove(filename)
      except Exception as e:
        self.setMessage(f"Folder '{self.txtPathToProtocols.text()}' permission denied")
        return False
    
      return True

    def setMessage (self, message):
      self.lblMessages.setText(message)

    def get_feature_from_layer (self, limit = 10):
      
      layer = self.config['Settings']['Layer']
      layer = QgsProject.instance().mapLayersByName(layer)[0]   
      
      ids = []
      count = 0

      try:
        features = layer.getFeatures()
      except:
        self.setMessage(f'No features in layer {layer}')
        return 0  

      fields = layer.fields()
      feature_id_field = fields[0].name()

      for feature in features:
        feature_geometry = feature.geometry()
        feature_geometry_type = feature_geometry.type()
        break  

      if (feature_geometry_type != QgsWkbTypes.PointGeometry and feature_geometry_type != QgsWkbTypes.PolygonGeometry):
        self.setMessage("Layer not consist point and polygon")
        return 0  
     
      features = layer.getFeatures()
      for feature in features:
        count += 1
        id = feature[feature_id_field]  
        ids.append(int(id)) 
        if limit != 0 and count == limit:
            break 
      
      return ids
    
    def time_to_seconds(self, time_str):
      hours, minutes, seconds = map(int, time_str.split(':'))
      total_seconds = hours * 3600 + minutes * 60 + seconds
      return total_seconds
    
    def prepareRaptor(self):  
      self.break_on = False
        
      QApplication.processEvents()

      mode = self.mode
      protocol_type = self.protocol_type
      D_TIME = self.time_to_seconds(self.config['Settings']['TIME'])
      sources = [] 

      stops = self.get_feature_from_layer()
      if stops:
        for stop_id in stops:
          sources.append((stop_id, D_TIME))
      else:
        self.setMessage("No exist points in layer")
        return 0
                   
      runRaptorWithProtocol(self, sources, mode, protocol_type)
      

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
      for section in self.config.sections():
        config_info.append(f"<a>[{section}]</a>")
        for key, value in self.config.items(section):
            config_info.append(f"<a>{key}: {value}</a>")
      return config_info
      