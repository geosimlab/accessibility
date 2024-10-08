# -*- coding: utf-8 -*-

#from .resources import *
import sys
import os

import py_compile
#import cProfile

from qgis.PyQt.QtCore import (QSettings, 
                              QTranslator, 
                              QCoreApplication, 
                              Qt)
from qgis.PyQt.QtGui import QIcon
from PyQt5.QtWidgets import QDockWidget,  QAction
import shutil
from .accessibility_tools import AccessibilityTools
from qgis.core import QgsProject
import configparser




current_dir = os.path.dirname(os.path.abspath(__file__))


module_path = os.path.join(current_dir, 'MYTRANSIT')
user_home = os.path.expanduser("~")
#utils_path = os.path.join(current_dir, 'utils')
# # Add the relative path to sys.path
sys.path.append(module_path)
#sys.path.append(utils_path)

class TAUNetCalc():
    
    #stops_id_name = "stop_id"
    #stops_build_name = "osm_id"
    #stopsFile = "stops.txt"
    #stopsLayerName = "stops"
     
    def __init__(self, iface):
        
        
        self.widget_visible = False
        self.dock_widget = None
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TAUNetCalc_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&TAU Network Calculator')
        
        self.first_start = None

        plugin_dir = os.path.dirname(__file__)
        self.clean_pyc(plugin_dir)
        self.compile_all_py(plugin_dir)
    
    def tr(self, message):
            return QCoreApplication.translate('TAUNetCalc', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag = True,
        add_to_menu = True,
        add_to_toolbar = True,
        status_tip = None,
        whats_this = None,
        parent = None):

        icon = QIcon(icon_path)
        
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    
    def get_version_from_metadata(self):
        
      current_dir = os.path.dirname(os.path.abspath(__file__))
      file_path = os.path.join(current_dir, 'metadata.txt')

      config = configparser.ConfigParser()
      config.read(file_path)
        
      if 'general' in config and 'version' in config['general']:
            return config['general']['version']
            
      return ""
    
    def initGui(self):

        #cache_dir = os.path.expanduser('~/.qgis2/cache/tau_net_calc')
        #if os.path.exists(cache_dir):
        #    shutil.rmtree(cache_dir)

                
        icon_accessibility_path = os.path.join(os.path.dirname(__file__), 'app.png')
        
        version = self.get_version_from_metadata()
        name_plagin = f'Accessibility tools v.{version}'
        
        self.add_action(
            icon_path=icon_accessibility_path,
            #text=self.tr(u'Accessibility tools v.4.15'),
            text=self.tr(name_plagin),
            callback=self.runAccessibility_tools,
            parent=self.iface.mainWindow())
        self.first_start_accessibility = True

    """Рекурсивно компилирует все .py файлы в указанной директории."""    
    def compile_all_py(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        # Компиляция файла, результат будет сохранен в __pycache__
                        py_compile.compile(file_path)
                        print(f'Compiled: {file_path}')
                    except py_compile.PyCompileError as e:
                        print(f'Failed to compile: {file_path}\nError: {e}')   

    def clean_pyc(self, directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.pyc'):
                    os.remove(os.path.join(root, file))

    def unload(self):
        
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&TAU Network Calculator'),
                action)
            self.iface.removeToolBarIcon(action)
     
    #self.profile_runRaptorWithProtocol(sources, mode, protocol_type)
    #  def profile_runRaptorWithProtocol(self, sources, mode, protocol_type):
    #    cProfile.runctx(
    #    "runRaptorWithProtocol(self,self.settings, sources, mode, protocol_type)",
    #    globals(),
    #    locals(),
    #    filename=r"C:/Users/geosimlab/Documents/Igor/Protocols/plugin_profile.txt"
    #  )
    

    def runAccessibility_tools(self):

         if self.first_start_accessibility == True:
                        
            project_directory = os.path.dirname(QgsProject.instance().fileName())
            parameters_path = os.path.join(project_directory, 'parameters_accessibility.txt')
            source_path = os.path.join(module_path,'parameters_accessibility_shablon.txt')

            if not os.path.exists(parameters_path):
                shutil.copy(source_path, parameters_path)

            parameters_path_road = os.path.join(project_directory, "taunetcalc_type_road.csv")  
            source_path_road = os.path.join(module_path,'taunetcalc_type_road_shablon.csv')

            if not os.path.exists(parameters_path_road):
                shutil.copy(source_path_road, parameters_path_road)    


         if not self.widget_visible:
            my_widget = AccessibilityTools()
            self.dock_widget = QDockWidget("Accessiblity tools")
            self.dock_widget.setWidget(my_widget)
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget)
            self.dock_widget.show()  
            self.widget_visible = True
         else:
            self.dock_widget.show()