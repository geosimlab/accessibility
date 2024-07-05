from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
from PyQt5 import uic
from qgis.PyQt import QtCore
from qgis.core import QgsProject
from .form_raptor_detailed import RaptorDetailed
from .form_car import CarAccessibility



class RaptorSummary(RaptorDetailed):
    def __init__(self, 
                 mode, 
                 protocol_type, 
                 title, 
                 timetable_mode, 
                 relative_mode = False):
            super().__init__(mode, protocol_type, title, timetable_mode)

            self.relative_mode = relative_mode
            self.txtTimeInterval.setVisible(True)
            self.lblTimeInterval.setVisible(True)
            self.cmbFields.setVisible(True)
            self.lblFields.setVisible(True)
            self.cbUseFields.setVisible(True)
                          
            self.fillComboBoxWithLayerFields()

            self.cmbFields.installEventFilter(self)

            self.cbUseFields.stateChanged.connect(self.EnableComboBox)
            self.cmbLayersDest.currentIndexChanged.connect(self.fillComboBoxWithLayerFields)
            
            regex = QRegExp(r"\d*")     
            int_validator1 = QRegExpValidator(regex)            
            self.txtTimeInterval.setValidator(int_validator1)
                        
            self.ParametrsShow()
   
    
    def EnableComboBox(self, state):
      
      if state == QtCore.Qt.Checked:
        self.cmbFields.setEnabled(True)
      else:
        self.cmbFields.setEnabled(False)        

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
   
    def saveParameters(self):

      super().saveParameters()

      f = self.user_home + "/parameters_accessibility.txt" 
      self.config.read(f)

      self.config['Settings']['Field'] = self.cmbFields.currentText()
      self.config['Settings']['UseField'] = str(self.cbUseFields.isChecked())
      self.config['Settings']['TimeInterval'] = self.txtTimeInterval.text()

      with open(f, 'w') as configfile:
          self.config.write(configfile)

    def prepareRaptor(self):
       result = super().prepareRaptor()

       if result and self.relative_mode:
          self.close_button.setText("Close and calc Car accessibility")
          self.close_button.setStyleSheet("QPushButton { color: red !important;}")
          self.close_button.clicked.connect(self.run_car_accessibility)
          

    def run_car_accessibility(self):

      
      params = (self.folder_name,
                self.config['Settings']['Field'],
                self.config['Settings']['UseField'],
                self.config['Settings']['maxtimetravel'],
                self.config['Settings']['timeinterval'],
                self.config['Settings']['layer'],
                self.config['Settings']['selectedonly1'],
                self.config['Settings']['layerdest'],
                self.config['Settings']['selectedonly2']
                )
      text = "forward"
      if self.mode == 2:
         text = "backward"
         
      car_accessibility = CarAccessibility \
                                    (
                                    mode = self.mode, 
                                    protocol_type = 2, 
                                    title = f"Relative accessibility MAP, PT versus Car, {text} accessibility, stage 2 - Car",
                                    relative_mode = True,
                                    params=params
                                    )
      car_accessibility.textInfo.setPlainText("Sample description car accessibility")
      car_accessibility.show()

    def ParametrsShow(self):
            
      super().ParametrsShow()

      #if isinstance(self.config['Settings']['Field'], str) and self.config['Settings']['Field'].strip():    
      self.cmbFields.setCurrentText(self.config['Settings']['Field'])

      use_field = self.config['Settings']['UseField'].lower() == "true"  
      self.cbUseFields.setChecked(use_field)
      self.cmbFields.setEnabled(use_field)
      self.txtTimeInterval.setText( self.config['Settings']['TimeInterval'])

    def get_config_info(self):
        
        config_info = super().get_config_info()
        for section in self.config.sections():
            for key, value in self.config.items(section):
              if key == "field":
                config_info.append(f"<a>Field to aggregate: {value}</a>")

              if key == "usefield":
                config_info.append(f"<a>Run aggregate: {value}</a>")      

              if key == "timeinterval":
                config_info.append(f"<a>Time interval between stored maps: {value} min</a>")       
        
        return config_info    