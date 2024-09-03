import os
import glob
import pandas as pd
import webbrowser
import re
from common import getDateTime, get_qgis_info
import numpy as np

from PyQt5.QtWidgets import (QDialogButtonBox, 
                             QDialog, 
                             QFileDialog, 
                             QApplication, 
                             QMessageBox)

from qgis.core import (QgsProject, 
                       QgsWkbTypes, 
                       QgsVectorLayer
                      )

from PyQt5.QtCore import (Qt, 
                          QEvent, 
                          QVariant)
from PyQt5.QtGui import QDesktopServices
from PyQt5 import uic

from datetime import datetime

import configparser

from visualization import visualization

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
                          
            self.curr_DateTime = getDateTime()

            self.setWindowTitle(title)

            self.splitter.setSizes([200, 200])   
            

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

            self.showAllLayersInCombo_Polygon(self.cbVisLayers)
            self.fillComboBoxFields_Id()
            self.cbVisLayers.currentIndexChanged.connect(self.fillComboBoxFields_Id)

            self.cbVisLayers.installEventFilter(self)
            self.cbVisLayers_fields.installEventFilter(self)

            self.default_aliase = f'{getDateTime()}' 

            self.ParametrsShow()

            
    def fillComboBoxFields_Id(self):
      self.cbVisLayers_fields.clear()
      selected_layer_name = self.cbVisLayers.currentText()
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
            self.cbVisLayers_fields.addItem(field_name)
            if field_name == "osm_id":
                osm_id_exists = True
        elif field_type == QVariant.String:
            # Проверяем первое значение поля на наличие только цифр
            first_value = None
            for feature in layer.getFeatures():
                first_value = feature[field_name]
                break  # Останавливаемся после первого значения
            
            if first_value is not None and digit_pattern.match(str(first_value)):
                self.cbVisLayers_fields.addItem(field_name)
                if field_name == "osm_id":
                    osm_id_exists = True
    
      if osm_id_exists:
        index = self.cbVisLayers_fields.findText("osm_id")
        if index != -1:
            self.cbVisLayers_fields.setCurrentIndex(index)
      

    def showAllLayersInCombo_Polygon(self, cmb):
      layers = QgsProject.instance().mapLayers().values()
      polygon_layers = [layer for layer in layers 
                      if isinstance(layer, QgsVectorLayer) and 
                      layer.geometryType() == QgsWkbTypes.PolygonGeometry and
                      layer.featureCount() > 1]
      cmb.clear()
      for layer in polygon_layers:
        cmb.addItem(layer.name(), [])        
        

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
        
        if not(self.cb_ratio.isChecked()) \
            and not(self.cb_difference.isChecked())  \
            and not(self.cb_relative_difference.isChecked()):
           
           self.setMessage('At least one calculation mode must be enabled.')
           self.run_button.setEnabled(True)
           return 0
        

        mode_first, self.MAP_first, max_time_travel_PT, time_interval_PT, run_aggregate_PT, field_to_aggregate_PT = self.check_log(self.txtPathToPT.text())
        mode_second, self.MAP_second, max_time_travel_Car, time_interval_Car, run_aggregate_Car, field_to_aggregate_Car = self.check_log(self.txtPathToCar.text())

        if  mode_second != mode_second:
            self.setMessage(
                            "Firts csv mode: {}. Second csv mode: {}. Must be the same.".format(
                            "forward" if mode_first else "backward",
                            "forward" if mode_second else "backward"
                            )
                            )
            self.run_button.setEnabled(True)
            return 0
        
        if self.MAP_first != self.MAP_second:
           self.setMessage(
                            "Firts csv type: {}. Second csv type: {}. Must be the same.".format(
                            "MAP" if self.MAP_first else "MAP",
                            "AREA" if self.MAP_second else "AREA"
                            )
                            )
           self.run_button.setEnabled(True)
           return 0
        
        """
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
        """
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
        
        layer =  QgsProject.instance().mapLayersByName(self.config['Settings']['VisLayer_relative'])[0]
        self.layer_vis_path = layer.dataProvider().dataSourceUri().split("|")[0]
        self.aliase = self.txtAliase.text() if self.txtAliase.text() != "" else self.default_aliase

        self.textLog.append("<a style='font-weight:bold;'>[Settings]</a>")
        self.textLog.append(f'<a> Scenario name: {self.aliase}</a>')
        self.textLog.append(f"<a>Results_1 folder: {self.config['Settings']['PathToPT_relative']}</a>")            
        self.textLog.append(f"<a>Results_2 folder: {self.config['Settings']['PathToCAR_relative']}</a>")
        self.textLog.append(f"<a>Output folder: {self.config['Settings']['PathToOutput_relative']}</a>")          
        self.textLog.append(f"<a>Layer for visualization : {self.layer_vis_path}</a>")  
        self.textLog.append(f"<a>Calc ratio: {self.config['Settings']['calc_ratio_relative']}</a>")              
        self.textLog.append(f"<a>Calc difference: {self.config['Settings']['calc_difference_relative']}</a>")                
        self.textLog.append(f"<a>Calc difference relative: {self.config['Settings']['calc_relative_difference_relative']}</a>")                    
        

        LayerVis = self.config['Settings']['VisLayer_relative']
        fieldname_layer = self.config['Settings']['VisLayers_fields_relative']
        
        if self.MAP_first:
           mode_visualization = 1
        else:
           mode_visualization = 2   

        self.make_log_compare()
        vis = visualization (self, 
                              LayerVis, 
                              mode = mode_visualization, 
                              fieldname_layer = fieldname_layer,
                              mode_compare = True
                              )
        aliase = self.txtAliase.text() if self.txtAliase.text() != "" else self.default_aliase

        begin_computation_time = datetime.now()
        begin_computation_str = begin_computation_time.strftime('%Y-%m-%d %H:%M:%S')
        self.textLog.append(f'<a>Started: {begin_computation_str}</a>') 
        list_file_name = []
        if self.cb_ratio.isChecked():
          self.mode_calc = "ratio"
          self.prepare()
          aliase_res = f'ratio_{aliase}'
          vis.add_thematic_map (self.path_output, aliase_res)
          list_file_name.append(self.path_output)

        if self.cb_difference.isChecked():  
          self.mode_calc = "difference"
          self.prepare()
          aliase_res = f'diff_{aliase}'
          vis.add_thematic_map (self.path_output, aliase_res)
          list_file_name.append(self.path_output)

        if self.cb_relative_difference.isChecked():    
          self.mode_calc = "relative_difference"
          self.prepare()
          aliase_res = f'rel_diff_{aliase}'
          vis.add_thematic_map (self.path_output, aliase_res)
          list_file_name.append(self.path_output)
        
        QApplication.processEvents()
        after_computation_time = datetime.now()
        after_computation_str = after_computation_time.strftime('%Y-%m-%d %H:%M:%S')
        self.textLog.append(f'<a>Finished: {after_computation_str}</a>') 
        duration_computation = after_computation_time - begin_computation_time
        duration_without_microseconds = str(duration_computation).split('.')[0]
        self.textLog.append(f'<a>Processing time: {duration_without_microseconds}</a>') 
        text = self.textLog.toHtml()
        filelog_name = f'{self.folder_name}//log_{self.curr_DateTime}.html'
        with open(filelog_name, "w") as file:
            file.write(text)
        self.textLog.append(f'<a>Output</a>')
        for file_name in list_file_name:
          self.textLog.append(f'<a>{file_name}</a>')

        self.textLog.append(f'<a href="file:///{self.folder_name}" target="_blank" >Protocol in folder</a>')

        self.setMessage ("Finished")

        self.close_button.setEnabled(True)
               
    
    def on_close_button_clicked(self):
        
        self.reject()
        
    def on_help_button_clicked(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        module_path = os.path.join(current_dir, 'help', 'build', 'html')
        file = os.path.join(module_path, 'relative_ready-made.html')
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

      if 'PathToOutput_relative' not in self.config['Settings']:
        self.config['Settings']['PathToOutput_relative'] = 'C:/'

      if 'PathToPT_relative' not in self.config['Settings']:
        self.config['Settings']['PathToPT_relative'] = 'C:/'  
      
      if 'PathToCar_relative' not in self.config['Settings']:
        self.config['Settings']['PathToCar_relative'] = 'C:/'  
      
      if 'calc_ratio_relative' not in self.config['Settings']:
        self.config['Settings']['calc_ratio_relative'] = "True"
      
      if 'calc_difference_relative' not in self.config['Settings']:
        self.config['Settings']['calc_difference_relative'] = "True"

      if 'calc_relative_difference_relative' not in self.config['Settings']:
        self.config['Settings']['calc_relative_difference_relative'] = "True"  

      if 'VisLayer_relative' not in self.config['Settings']:
        self.config['Settings']['VisLayer_relative'] = ''  

      if 'VisLayers_fields_relative' not in self.config['Settings']:
        self.config['Settings']['VisLayers_fields_relative'] = ''    


    # update config file   
    def saveParameters(self):
      
      project_directory = os.path.dirname(QgsProject.instance().fileName())
      f = os.path.join(project_directory, 'parameters_accessibility.txt')
      
      self.config.read(f)
      
      
      self.config['Settings']['PathToOutput_relative'] = self.txtPathToOutput.text()
      self.config['Settings']['PathToPT_relative'] = self.txtPathToPT.text()
      self.config['Settings']['PathToCar_relative'] = self.txtPathToCar.text()

      self.config['Settings']['calc_ratio_relative'] = str(self.cb_ratio.isChecked())
      self.config['Settings']['calc_difference_relative'] = str(self.cb_difference.isChecked())
      self.config['Settings']['calc_relative_difference_relative'] = str(self.cb_relative_difference.isChecked())

      self.config['Settings']['VisLayer_relative'] = self.cbVisLayers.currentText()
      self.config['Settings']['VisLayers_fields_relative'] = self.cbVisLayers_fields.currentText()
      
      
      with open(f, 'w') as configfile:
          self.config.write(configfile)
      
         

    def ParametrsShow(self):
            
      self.readParameters()
      
      self.txtPathToOutput.setText(self.config['Settings']['PathToOutput_relative'])
      self.txtPathToPT.setText(self.config['Settings']['PathToPT_relative'])
      self.txtPathToCar.setText(self.config['Settings']['PathToCar_relative'])

      
      cb1 = self.config['Settings']['calc_ratio_relative'].lower() == "true"  
      self.cb_ratio.setChecked(cb1)
      cb1 = self.config['Settings']['calc_difference_relative'].lower() == "true"  
      self.cb_difference.setChecked(cb1)
      cb1 = self.config['Settings']['calc_relative_difference_relative'].lower() == "true"  
      self.cb_relative_difference.setChecked(cb1)
      
      self.cbVisLayers.setCurrentText(self.config['Settings']['VisLayer_relative'])
      self.cbVisLayers_fields.setCurrentText(self.config['Settings']['VisLayers_fields_relative'])

      self.txtAliase.setText (self.default_aliase)

    def check_output_folder(self):
      self.setMessage("")
      if not os.path.exists(self.txtPathToOutput.text()):
        self.setMessage(f"Output folder '{self.txtPathToOutput.text()}' does not exist")
        return False
            
      try:
        tmp_prefix = "write_tester";
        filename = f'{self.txtPathToOutput.text()}//{tmp_prefix}'
        with open(filename, 'w') as f:
          f.write("test")
        os.remove(filename)
      except Exception as e:
        self.setMessage (f"An access to the output folder '{self.txtPathToOutput.text()}' is denied")
        return False
      
      return True

    def parse_log_file(self, file_path):
      params = {}
      with open(file_path, 'r') as file:
        inside_mode = False
        for line in file:
            line = line.strip()
            if line.startswith('[Mode]'):
                inside_mode = True
                continue
            if line.startswith('Started:'):
                break
            if inside_mode and ': ' in line:
                param, value = line.split(': ', 1)
                params[param] = value
      return params  

    def make_log_compare(self):
        path1 = self.txtPathToPT.text()
        path2 = self.txtPathToCar.text()

        pattern = 'log_*.txt'
        file_path1 = glob.glob(os.path.join(path1, pattern))[0]
        file_path2 = glob.glob(os.path.join(path2, pattern))[0]

        # Парсим оба файла
        params_file1 = self.parse_log_file(file_path1)
        params_file2 = self.parse_log_file(file_path2)
        comparison_array = []

        # Обрабатываем параметр Mode отдельно, чтобы он был первым
        mode_value_file1 = params_file1.pop('Mode', 'XXX')
        mode_value_file2 = params_file2.pop('Mode', 'XXX')

        comparison_array.append({
          'parameter': 'Mode',
          'value_file1': mode_value_file1,
          'value_file2': mode_value_file2
          })

        all_params = set(params_file1.keys()).union(set(params_file2.keys()))
        
        # Добавляем все параметры из первого файла
        for param in params_file1:
          comparison_array.append({
              'parameter': param,
              'value_file1': params_file1[param],
              'value_file2': params_file2.get(param, 'XXX')
                })

        # Добавляем оставшиеся параметры из второго файла, которые не были в первом
        for param in params_file2:
          if param not in [entry['parameter'] for entry in comparison_array]:
            comparison_array.append({
            'parameter': param,
            'value_file1': 'XXX',
            'value_file2': params_file2[param]
              })
          
        # Генерация HTML таблицы
        html_table = self.generate_html_table(comparison_array)

        # Добавление HTML в QTextBrowser
        self.textLog.append(html_table)  

    
    def generate_html_table(self, comparison_array):
      html = "<table border='1' cellpadding='5' cellspacing='0'>"
      html += "<tr><th>Params</th><th>File1</th><th>File2</th></tr>"
    
      for entry in comparison_array:
        html += f"<tr><td>{entry['parameter']}</td><td>{entry['value_file1']}</td><td>{entry['value_file2']}</td></tr>"
    
      html += "</table>"
      return html

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
                  
        return  (found_forward, 
                found_map, 
                max_time_travel, 
                time_interval, 
                run_aggregate, 
                field_to_aggregate)
              
    def check_folder_and_file(self, path):
     
      if not os.path.exists(path):
        self.setMessage(f"The folder '{path}' does not exist")
        return False
               
      required_patterns = ['access_*.csv', 'log_*.txt']
      missing_files = []

      for pattern in required_patterns:
        pattern_path = os.path.join(path, pattern)
        matching_files = glob.glob(pattern_path)
        if not matching_files:
          missing_files.append(pattern)


      if missing_files:
        missing_files_message = ", ".join(missing_files)
        self.setMessage (f"Files are missing in '{path}': {missing_files_message}")
        return False
    
      return True

    def setMessage (self, message):
      self.lblMessages.setText(message)
            
    def prepare(self):
      
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
        self.path_output = f'{self.folder_name}//{self.mode_calc}_{self.curr_DateTime}.csv'
        
        if not os.path.exists(self.folder_name):
            os.makedirs(self.folder_name)
                
        file1 = glob.glob(os.path.join(self.txtPathToPT.text(), 'access*.csv'))[0]
        file2 = glob.glob(os.path.join(self.txtPathToCar.text(), 'access*.csv'))[0]

        if self.MAP_first:
          self.calc_MAP(file1, file2)
        else:
          self.calc_AREA(file1, file2)
      
      if not(run):
         self.run_button.setEnabled(True)
         self.close_button.setEnabled(True)
         self.textLog.clear()
         self.tabWidget.setCurrentIndex(0) 
         self.setMessage("")

         
    def calc_MAP(self, file1, file2):
      
      df1 = pd.read_csv(file1)
      df2 = pd.read_csv(file2)
      postfix1 = "_1"
      postfix2 = "_2"
      common_columns = [col for col in df1.columns if col != 'Origin_ID' and col in df2.columns]

      merged_df = pd.merge(df1, df2, on='Origin_ID', suffixes=(postfix1, postfix2))
      result_df = pd.DataFrame()
      result_df['Origin_ID'] = merged_df['Origin_ID']

      for col in common_columns:
        col1 = f'{col}{postfix1}'
        col2 = f'{col}{postfix2}'
        
        result_df[col1] = merged_df[col1]
        result_df[col2] = merged_df[col2]

        if self.mode_calc == "ratio":
          
          if col == "Total":
            ratio_col = "Total"
            # Используем numpy.where, чтобы обработать деление на 0
            result_df[ratio_col] = np.where(result_df[col2] != 0, result_df[col1] / result_df[col2], 0)

          
        if self.mode_calc == "difference":
          
          if col == "Total":
            ratio_col = "Total"
            result_df[ratio_col] = (result_df[col1] - result_df[col2])
          
        if self.mode_calc == "relative_difference":
          
          if col == "Total":
            ratio_col = "Total"
            result_df[ratio_col] = np.where(result_df[col2] != 0, (result_df[col1] - result_df[col2]) / result_df[col2], 0)


      result_df.to_csv(self.path_output, index=False, na_rep='NaN')

      
    def calc_AREA(self, file1, file2):
      
      df1 = pd.read_csv(file1)
      df2 = pd.read_csv(file2)

      postfix1 = ""
      postfix2 = "_2"
    
      # Фильтрация данных по первому значению Origin_ID
      origin_id = df1['Origin_ID'].iloc[0]
      df1_filtered = df1[df1['Origin_ID'] == origin_id]
      df2_filtered = df2[df2['Origin_ID'] == origin_id]
    
      result_df = pd.DataFrame()
    
      # Сохранение значений Destination_ID из первого файла
      result_df['Destination_ID'] = df1_filtered['Destination_ID']
    
      # Соединение по Destination_ID
      merged_df = pd.merge(df1_filtered[['Origin_ID','Destination_ID', 'Duration']],
                         df2_filtered[['Destination_ID', 'Duration']],
                         on='Destination_ID',
                         suffixes=(postfix1, postfix2))

      result_df = merged_df[['Origin_ID', 'Destination_ID']].copy()
      result_df['Duration1'] = merged_df[f'Duration{postfix1}']
      result_df['Duration2'] = merged_df[f'Duration{postfix2}']

      # Расчет отношения Duration из первого файла к Duration из второго файла
      if self.mode_calc == "ratio":
        result_df['Duration'] = np.where(merged_df[f'Duration{postfix2}'] != 0, 
                                         merged_df[f'Duration{postfix1}'] / merged_df[f'Duration{postfix2}'], 
                                         0)
              
      if self.mode_calc == "difference":
         result_df['Duration'] = (merged_df[f'Duration{postfix1}'] - merged_df[f'Duration{postfix2}'])
      
      if self.mode_calc == "relative_difference":
        
        result_df['Duration'] = np.where(merged_df[f'Duration{postfix2}'] != 0, 
                                         (merged_df[f'Duration{postfix1}'] - merged_df[f'Duration{postfix2}']) / merged_df[f'Duration{postfix2}'], 
                                         0)
      
    
      # Сохранение результата в файл
      result_df.to_csv(self.path_output, index=False, na_rep='NaN')  
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            # Если комбо-бокс в фокусе, игнорируем событие прокрутки колесом мыши
            if obj.hasFocus():
                event.ignore()
                return True
        
         
        return super().eventFilter(obj, event)
    
  