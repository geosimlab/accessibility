import os
import sys
import qgis.core
import osgeo.gdal
import osgeo.osr
import glob
import pandas as pd

from PyQt5.QtWidgets import (QDialogButtonBox, 
                             QDialog, 
                             QFileDialog, 
                             QApplication, 
                             QMessageBox)

from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QDesktopServices
from PyQt5 import uic

from datetime import datetime


import configparser

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'relative.ui'))

class form_relative(QDialog, FORM_CLASS):
    def __init__(self, title):
            super().__init__()
            self.setupUi(self)
            self.setModal(False)
            self.setWindowFlags(Qt.Window);
            self.user_home = os.path.expanduser("~")
                          
            self.curr_DateTime = self.getDateTime()

            self.setWindowTitle(title)

            self.splitter.setSizes([10, 250])   
            

            self.tabWidget.setCurrentIndex(0) 
            self.config = configparser.ConfigParser()

            self.break_on = False
            
            self.title = title

            self.progressBar.setValue(0)
               

            self.textLog.setOpenLinks(False)
            self.textLog.anchorClicked.connect(self.openFolder)
            
            self.toolButton_Output.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToOutput))
            self.toolButton_PT.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToPT))
            self.toolButton_Car.clicked.connect(lambda: self.showFoldersDialog(self.txtPathToCar))
            
           
            self.btnBreakOn.clicked.connect(self.set_break_on)
                        
            self.run_button = self.buttonBox.addButton("Run", QDialogButtonBox.ActionRole)
            self.close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            self.help_button = self.buttonBox.addButton("Help", QDialogButtonBox.HelpRole)
            
            self.run_button.clicked.connect(self.on_run_button_clicked)
            self.close_button.clicked.connect(self.on_close_button_clicked)
            self.help_button.clicked.connect(self.on_help_button_clicked)
            
            self.ParametrsShow()
        

    def openFolder(self, url):
        QDesktopServices.openUrl(url)
        

    def set_break_on (self):
      self.break_on = True
      self.close_button.setEnabled(True)
    
    def on_run_button_clicked(self):
        
        self.run_button.setEnabled(False)
        

        self.break_on = False
        
        if not (self.check_output_folder()):
           self.run_button.setEnabled(True)
           return 0

        if not (self.check_folder_and_file(self.txtPathToPT.text())):
           self.run_button.setEnabled(True)
           return 0
        
        if not (self.check_folder_and_file(self.txtPathToCar.text())):
           self.run_button.setEnabled(True)
           return 0
        
        mode_PT, MAP_PT, max_time_travel_PT, time_interval_PT, run_aggregate_PT, field_to_aggregate_PT = self.check_log(self.txtPathToPT.text())
        mode_Car, MAP_Car, max_time_travel_Car, time_interval_Car, run_aggregate_Car, field_to_aggregate_Car = self.check_log(self.txtPathToCar.text())
        if  mode_PT != mode_Car:
            self.setMessage(
                            "PT mode: {}. Car mode: {}. Must be the same.".format(
                            "forward" if mode_PT else "backward",
                            "forward" if mode_Car else "backward"
                            )
                            )
            self.run_button.setEnabled(True)
            return 0
        
        if not(MAP_PT):
           self.setMessage('PT protokol is not MAP')
           self.run_button.setEnabled(True)
           return 0
        
        if not(MAP_Car):
           self.setMessage('Car protokol is not MAP')
           self.run_button.setEnabled(True)
           return 0
        
        if max_time_travel_PT != max_time_travel_Car:
           self.setMessage(f'PT mode max time travel: {max_time_travel_PT} min. Car mode max time travel: {max_time_travel_Car} min. Must be the same.')
           self.run_button.setEnabled(True)
           return 0
        
        if time_interval_PT != time_interval_Car:
           self.setMessage(f'PT mode time interval: {time_interval_PT} min. Car mode time interval: {time_interval_Car} min. Must be the same.')
           self.run_button.setEnabled(True)
           return 0
        
        if run_aggregate_PT != run_aggregate_Car:
           self.setMessage(f'PT mode run aggregate: {run_aggregate_PT}. Car mode run aggregate: {run_aggregate_Car}. Must be the same.')
           self.run_button.setEnabled(True)
           return 0
        
        if field_to_aggregate_PT != field_to_aggregate_Car:
           self.setMessage(f'PT mode field to aggregate: {field_to_aggregate_PT}. Car mode field to : {field_to_aggregate_Car}. Must be the same.')
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
    
        info_str = "<br>".join(config_info[1:])
        self.textLog.append("<a style='font-weight:bold;'>[Settings]</a>")
        self.textLog.append(f'<a>{info_str}</a>')

        self.prepare()
        self.close_button.setEnabled(True)
       
        
    
    def on_close_button_clicked(self):
        
        self.reject()
        
    def on_help_button_clicked(self):
        
        pass
   
    
    def showFoldersDialog(self, obj):        
      folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", obj.text())
      if folder_path:  
          obj.setText(folder_path)
      else:  
          obj.setText(obj.text())   

    def readParameters(self):
      self.config.read(self.user_home + "/parameters_accessibility.txt")

      if 'PathToOutput_relative' not in self.config['Settings']:
        self.config['Settings']['PathToOutput_relative'] = 'C:/'

      if 'PathToPT_relative' not in self.config['Settings']:
        self.config['Settings']['PathToPT_relative'] = 'C:/'  
      
      if 'PathToCar_relative' not in self.config['Settings']:
        self.config['Settings']['PathToCar_relative'] = 'C:/'  
      
      


    # update config file   
    def saveParameters(self):
      
      f = self.user_home + "/parameters_accessibility.txt" 
      self.config.read(f)
      
      
      self.config['Settings']['PathToOutput_relative'] = self.txtPathToOutput.text()
      self.config['Settings']['PathToPT_relative'] = self.txtPathToPT.text()
      self.config['Settings']['PathToCar_relative'] = self.txtPathToCar.text()
      
      
      with open(f, 'w') as configfile:
          self.config.write(configfile)
      
         

    def ParametrsShow(self):
            
      self.readParameters()
      
      self.txtPathToOutput.setText(self.config['Settings']['PathToOutput_relative'])
      self.txtPathToPT.setText(self.config['Settings']['PathToPT_relative'])
      self.txtPathToCar.setText(self.config['Settings']['PathToCar_relative'])
      

    def check_output_folder(self):
      self.setMessage("")
      if not os.path.exists(self.txtPathToOutput.text()):
        self.setMessage(f"Output folder '{self.txtPathToOutput.text()}' no exist")
        return False
            
      try:
        tmp_prefix = "write_tester";
        filename = f'{self.txtPathToOutput.text()}//{tmp_prefix}'
        with open(filename, 'w') as f:
          f.write("test")
        os.remove(filename)
      except Exception as e:
        self.setMessage(f"Output folder '{self.txtPathToOutput.text()}' permission denied")
        return False
      
      return True
    
    def check_log(self, path):
        pattern = 'log_*.txt'
        file_path = glob.glob(os.path.join(path, pattern))
        file_path = file_path[0]
        found_forward = False
        found_map = False
        max_time_travel = None
        time_interval = None
        run_aggregate = False
        field_to_aggregate = None
  
        with open(file_path, 'r') as file:
            
            for line in file:
              if "Mode:" in line:
                  if "forward" in line:
                    found_forward = True

                  if "MAP" in line:
                    found_map = True

              if "Maximal time travel:" in line:
                    max_time_travel = int(line.split(':')[1].strip().split()[0])

              if "Time interval between stored maps:" in line:
                    time_interval = int(line.split(':')[1].strip().split()[0])

              if "Run aggregate:" in line:
                    run_aggregate = line.split(':')[1].strip() == 'True'
                
              if "Field to aggregate:" in line:
                    field_to_aggregate = line.split(':')[1].strip()            
                  
        return found_forward, found_map, max_time_travel, time_interval, run_aggregate, field_to_aggregate
              
    def check_folder_and_file(self, path):
     
      if not os.path.exists(path):
        self.setMessage(f"Folder '{path}' no exist")
        return False
               
      required_patterns = ['access_*.csv', 'log_*.txt', 'origins_*.zip']
      missing_files = []

      for pattern in required_patterns:
        pattern_path = os.path.join(path, pattern)
        matching_files = glob.glob(pattern_path)
        if not matching_files:
          missing_files.append(pattern)


      if missing_files:
        missing_files_message = ", ".join(missing_files)
        self.setMessage(f"The following files are missing from the folder '{path}': {missing_files_message}")
        return False
    
      return True

    def setMessage (self, message):
      self.lblMessages.setText(message)
    
    def time_to_seconds(self, time_str):
      hours, minutes, seconds = map(int, time_str.split(':'))
      total_seconds = hours * 3600 + minutes * 60 + seconds
      return total_seconds
    
    def prepare(self):
      time_start_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
      self.textLog.append(f'<a>Time start computation {time_start_computation}</a>') 

      self.break_on = False
 
      QApplication.processEvents()
      
      run = True

      if run:
        """
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
        """  
        self.folder_name = f'{self.txtPathToOutput.text()}//{self.curr_DateTime}'
        path_output = f'{self.folder_name}//access_{self.curr_DateTime}.csv'
        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
                
        file1 = glob.glob(os.path.join(self.txtPathToPT.text(), 'access*.csv'))[0]
        file2 = glob.glob(os.path.join(self.txtPathToCar.text(), 'access*.csv'))[0]
        self.calc(file1, file2, path_output)

        self.setMessage(f'Calculating done')
        QApplication.processEvents()
        time_after_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.textLog.append(f'<a>Time after computation {time_after_computation}</a>') 
        self.textLog.append(f'<a href="file:///{self.folder_name}" target="_blank" >Protocol in folder</a>')
        
      
      if not(run):
         self.run_button.setEnabled(True)
         self.close_button.setEnabled(True)
         self.textLog.clear()
         self.tabWidget.setCurrentIndex(0) 
         self.setMessage("")

         
    def calc(self, file1, file2, path_output):
      
      df1 = pd.read_csv(file1)
      df2 = pd.read_csv(file2)
      common_columns = [col for col in df1.columns if col != 'Source_ID' and col in df2.columns]

      merged_df = pd.merge(df1, df2, on='Source_ID', suffixes=('_pt', '_car'))
      result_df = pd.DataFrame()
      result_df['Source_ID'] = merged_df['Source_ID']

      for col in common_columns:
        pt_col = f'{col}_pt'
        car_col = f'{col}_car'
        ratio_col = f'{col} pt/{col} car'

        result_df[pt_col] = merged_df[pt_col]
        result_df[car_col] = merged_df[car_col]
        result_df[ratio_col] = result_df[pt_col] / result_df[car_col]
     
      #result_df.dropna(inplace=True)
      result_df.to_csv(path_output, index=False)
      

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

            if key == "pathtooutput_relative":
              config_info.append(f"<a>Output folder: {value}</a>")          

            if key == "pathtopt_relative":
              config_info.append(f"<a>Folder of public transport accessibility MAP: {value}</a>")            

            if key == "pathtocar_relative":
              config_info.append(f"<a>Folder of car accessibility MAP: {value}</a>")            
            
      return config_info
    
    
    def eventFilter(self, obj, event):
        if obj == self.cmbLayers and event.type() == QEvent.Wheel:
            # Если комбо-бокс в фокусе, игнорируем событие прокрутки колесом мыши
            if self.cmbLayers.hasFocus():
                event.ignore()
                return True
        
         
        return super().eventFilter(obj, event)
    
    def getDateTime(self):
        current_datetime = datetime.now()
        year = current_datetime.year
        month = str(current_datetime.month).zfill(2)
        day = str(current_datetime.day).zfill(2)
        hour = str(current_datetime.hour).zfill(2)
        minute = str(current_datetime.minute).zfill(2)
        second = str(current_datetime.second).zfill(2)
        return f'{year}{month}{day}_{hour}{minute}{second}'