import os
import sys
import qgis.core
from qgis.PyQt import QtCore
from qgis.core import QgsProject, QgsWkbTypes

import osgeo.gdal
import osgeo.osr

from PyQt5.QtWidgets import QDialogButtonBox, QDialog, QFileDialog, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QRegExp, QDateTime, QEvent
from PyQt5.QtGui import QRegExpValidator, QDesktopServices
from PyQt5 import uic

from query_file import runRaptorWithProtocol
import configparser



# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'raptor.ui'))

class RaptorDetailed(QDialog, FORM_CLASS):
    def __init__(self, mode, protocol_type, title, timetable_mode ):
            super().__init__()
            self.setupUi(self)
            self.setModal(False)
            self.setWindowFlags(Qt.Window);
            self.user_home = os.path.expanduser("~")

                           
            
            self.setWindowTitle(title)
            self.tabWidget.setCurrentIndex(0) 
            self.config = configparser.ConfigParser()

            #self.textLog.anchorClicked.connect(self.openExternalLink)

            self.break_on = False
            
            self.mode = mode
            self.protocol_type = protocol_type
            self.title = title
            self.timetable_mode = timetable_mode
            self.change_time = 1
            #self.stops_id_name = "stop_id"
            #self.stops_build_name = "osm_id"
            self.progressBar.setValue(0)

            self.txtTimeInterval.setVisible(False)
            self.lblTimeInterval.setVisible(False)
            self.cmbFields.setVisible(False)
            self.lblFields.setVisible(False)
            self.cbUseFields.setVisible(False)

            if not timetable_mode:
               print ("not timetable_mode")
               self.lblMaxExtraTime.setVisible(False)
               self.txtMaxExtraTime.setVisible(False)
               self.lblDepartureInterval.setVisible(False)
               self.txtDepartureInterval.setVisible(False)

            if timetable_mode:
               self.lblMaxWaitTime.setVisible(False)
               self.txtMaxWaitTime.setVisible(False)
               
            
            if timetable_mode and mode == 2:
              self.lblDepartureInterval.setText("Departure interval latest, min")


               

            self.textLog.setOpenLinks(False)
            self.textLog.anchorClicked.connect(self.openFolder)
            
            self.toolButton_PKL.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToPKL))
            self.toolButton_protocol.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToProtocols))

            self.showAllLayersInCombo(self.cmbLayers)
            self.cmbLayers.installEventFilter(self)
            self.showAllLayersInCombo(self.cmbLayersDest)
            self.cmbLayersDest.installEventFilter(self)

            self.dtStartTime.installEventFilter(self)
            
            
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
            regex1 = QRegExp(r"\d*")     
            int_validator1 = QRegExpValidator(regex1)
            
            # 0,1,2
            regex2 = QRegExp(r"[0-2]{1}")
            int_validator2 = QRegExpValidator(regex2)

             # floating, two digit after dot
            regex3 = QRegExp(r"^\d+(\.\d{1,2})?$")
            int_validator3 = QRegExpValidator(regex3)

            self.txtMinTransfers.setValidator(int_validator2)
            self.txtMaxTransfers.setValidator(int_validator2)
            self.txtMaxWalkDist1.setValidator(int_validator1)
            self.txtMaxWalkDist2.setValidator(int_validator1)
            self.txtMaxWalkDist3.setValidator(int_validator1)
            self.txtSpeed.setValidator(int_validator3)
            self.txtMaxWaitTime.setValidator(int_validator3)
            self.txtMaxWaitTimeTransfer.setValidator(int_validator3)
            self.txtMaxTimeTravel.setValidator(int_validator3)
            self.txtMaxExtraTime.setValidator(int_validator3)
            self.txtDepartureInterval.setValidator(int_validator3)
            
            

            self.ParametrsShow()

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

        self.prepareRaptor()
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
      self.config['Settings']['MaxExtraTime'] = self.txtMaxExtraTime.text()
      self.config['Settings']['DepartureInterval'] = self.txtDepartureInterval.text()
      self.config['Settings']['MaxWalkDist1'] = self.txtMaxWalkDist1.text()
      self.config['Settings']['MaxWalkDist2'] = self.txtMaxWalkDist2.text()
      self.config['Settings']['MaxWalkDist3'] = self.txtMaxWalkDist3.text()
      self.config['Settings']['TIME'] = self.dtStartTime.dateTime().toString("HH:mm:ss")
      self.config['Settings']['Speed'] = self.txtSpeed.text()
      self.config['Settings']['MaxWaitTime'] = self.txtMaxWaitTime.text()
      self.config['Settings']['MaxWaitTimeTrasnfer'] = self.txtMaxWaitTimeTransfer.text()
      self.config['Settings']['MaxTimeTravel'] = self.txtMaxTimeTravel.text()
      
      
      
     

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
      self.txtMaxWaitTimeTransfer.setText(self.config['Settings']['MaxWaitTimeTransfer'])
      self.txtMaxTimeTravel.setText( self.config['Settings']['MaxTimeTravel'])

      max_extra_time = self.config['Settings'].get('maxextratime', '30')
      self.txtMaxExtraTime.setText(max_extra_time)

      DepartureInterval = self.config['Settings'].get('departureinterval', '5')
      self.txtDepartureInterval.setText(DepartureInterval)

     
      

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

    def get_feature_from_layer (self, limit = 0):
      
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
      timetable_mode = self.timetable_mode
      D_TIME = self.time_to_seconds(self.config['Settings']['TIME'])
      sources = [] 

      stops = self.get_feature_from_layer()
      if stops:
        for stop_id in stops:
          sources.append((stop_id, D_TIME))
      else:
        self.setMessage("No exist points in layer")
        self.run_button.setEnabled(True)
        return 0
      
      run = True
      if len(sources) > 10:
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Question)
        msgBox.setWindowTitle("Confirm")
        msgBox.setText(f"Layer contains {len(sources)} feature. No more than 10 objects are recommended. The calculations can take a long time and require a lot of resources. Are you sure?")
        msgBox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        result = msgBox.exec_()
        if result == QMessageBox.Yes:
          run = True
        else:
          run = False
                   
      if run:
         runRaptorWithProtocol(self, sources, mode, protocol_type, timetable_mode)

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
      for section in self.config.sections():
        config_info.append(f"<a>[{section}]</a>")
        for key, value in self.config.items(section):
            if key == "pathtopkl":
              config_info.append(f"<a>Dataset folder: {value}</a>")

            if key == "pathtoprotocols":
              config_info.append(f"<a>Output folder: {value}</a>")  

            if key == "layer":
              config_info.append(f"<a>Layer of origins (points/polygons): {value}</a>")

            if key == "layerdest":
              config_info.append(f"<a>Layer of destinations (points/polygons): {value}</a>")

            
            if key == "min_transfer":
              config_info.append(f"<a>Min transfers: {value}</a>")      
            if key == "max_transfer":
              config_info.append(f"<a>Max transfers: {value}</a>")      

            if self.timetable_mode:
              if key == "maxextratime":
                config_info.append(f"<a>Maximum extra time at a first stop: {value} min</a>") 

              if key == "departureinterval":
                if self.mode == 1:
                  config_info.append(f"<a>Departure interval earliest: {value} min</a>") 
                else:  
                  config_info.append(f"<a>Departure interval latest: {value} min</a>")  

                

            if key == "maxwalkdist1":
              config_info.append(f"<a>Max walk distance to the initial PT stop: {value} m</a>")      
            if key == "maxwalkdist2":
              config_info.append(f"<a>Max walk distance at transfer: {value} m</a>")      
            if key == "maxwalkdist3":
              config_info.append(f"<a>Max walk distance from a last PT stop: {value} m</a>") 

            if key == "time":
              config_info.append(f"<a>Start at/Arrive before (time): {value}</a>")      
            if key == "speed":
              config_info.append(f"<a>Walking speed: {value} km/h</a>")      
            if key == "maxwaittime":
              config_info.append(f"<a>Maximal waiting time at initial stop: {value} min</a>")      
            if key == "maxwaittimetransfer":
              config_info.append(f"<a>Maximal waiting time at transfer stop: {value} min</a>")      
            if key == "maxtimetravel":
              config_info.append(f"<a>Maximal time travel: {value} min</a>") 
            



      return config_info

    
    
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

        if obj == self.dtStartTime and event.type() == QEvent.Wheel:
            # Проверяем, находится ли QDateTimeEdit в фокусе
            if self.dtStartTime.hasFocus():
                # Игнорируем событие колеса мыши
                event.ignore()
                return True
    
         
        return super().eventFilter(obj, event)  
    