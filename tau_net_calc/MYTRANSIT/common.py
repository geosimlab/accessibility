from datetime import datetime
import os
import sys
import configparser
import qgis.core
import qgis.PyQt
import osgeo.gdal

def getDateTime():
      current_datetime = datetime.now()
      month = current_datetime.strftime("%b").lower()  # Преобразуем месяц в нижний регистр
      day = str(current_datetime.day).zfill(2)
      hour = str(current_datetime.hour).zfill(2)
      minute = str(current_datetime.minute).zfill(2)
      second = str(current_datetime.second).zfill(2)
      return f'{day}{month}_{hour}h{minute}m{second}s'

def get_version_from_metadata():
        
      current_dir = os.path.dirname(os.path.abspath(__file__))  # Путь к текущему файлу
      plugin_dir = os.path.dirname(current_dir)  # Путь к папке плагина

      file_path = os.path.join(plugin_dir, 'metadata.txt')

      config = configparser.ConfigParser()
      config.read(file_path)
        
      if 'general' in config and 'version' in config['general']:
            return config['general']['version']
            
      return ""

def get_qgis_info():
      qgis_info = {}
      qgis_info['QGIS version'] = qgis.core.Qgis.QGIS_VERSION
      qgis_info['Qt version'] = qgis.PyQt.QtCore.QT_VERSION_STR
      qgis_info['Python version'] = sys.version
      qgis_info['GDAL version'] = osgeo.gdal.VersionInfo('RELEASE_NAME')
      qgis_info['Plugin version'] = get_version_from_metadata ()
      return qgis_info