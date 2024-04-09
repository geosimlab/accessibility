#################
THIS IS DRAFT
#################



import pandas as pd
import json

# Загрузка данных остановок из GTFS
stops_df = pd.read_csv('stops.txt')

# Преобразование в GeoJSON
features = []
for idx, row in stops_df.iterrows():
    feature = {
        "type": "Feature",
        "properties": {
            "stop_id": row['stop_id'],
            "stop_name": row['stop_name'],
            "stop_desc": row['stop_desc']
        },
        "geometry": {
            "type": "Point",
            "coordinates": [row['stop_lon'], row['stop_lat']]
        }
    }
    features.append(feature)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

# Сохранение в файл
with open('stops.geojson', 'w') as f:
    json.dump(geojson, f)



import pandas as pd
import json

# Загрузка данных остановок и маршрутов из GTFS
stops_df = pd.read_csv('stops.txt')
routes_df = pd.read_csv('routes.txt')
stop_times_df = pd.read_csv('stop_times.txt')

# Объединение данных для получения связи между маршрутами и остановками
merged_data = stop_times_df.merge(routes_df, on='trip_id').merge(stops_df, on='stop_id')

# Создание GeoJSON
features = []

# Группировка данных по маршрутам
for route_id, group in merged_data.groupby('route_id'):
    stops = []
    for idx, row in group.iterrows():
        stop = {
            "type": "Feature",
            "properties": {
                "stop_id": row['stop_id'],
                "stop_name": row['stop_name'],
                "route_id": row['route_id'],
                "trip_id": row['trip_id']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [row['stop_lon'], row['stop_lat']]
            }
        }
        stops.append(stop)

    feature = {
        "type": "Feature",
        "properties": {
            "route_id": route_id
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [[row['stop_lon'], row['stop_lat']] for idx, row in group.iterrows()]
        }
    }
    features.append(feature)
    features.extend(stops)

geojson = {
    "type": "FeatureCollection",
    "features": features
}

# Сохранение в файл
with open('routes_with_stops.geojson', 'w') as f:
    json.dump(geojson, f)




from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from qgis.core import QgsVectorLayer, QgsProject
from qgis.gui import QgsMapCanvas
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoJSON Loader")
        self.setGeometry(100, 100, 800, 600)

        self.canvas = QgsMapCanvas()
        self.setCentralWidget(self.canvas)

        self.load_action = QAction("Load GeoJSON", self)
        self.load_action.triggered.connect(self.load_geojson)
        self.menuBar().addAction(self.load_action)

        self.project = QgsProject.instance()

    def load_geojson(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("GeoJSON files (*.geojson)")
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        if file_dialog.exec_():
            selected_files = file_dialog.selectedFiles()
            for file_path in selected_files:
                layer = QgsVectorLayer(file_path, "Layer", "ogr")
                if not layer.isValid():
                    print("Invalid layer:", layer.name())
                    return
                self.project.addMapLayer(layer)
                self.canvas.setExtent(layer.extent())
                self.canvas.setLayers([layer])
                self.canvas.refresh()

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()


from qgis.core import QgsVectorLayer, QgsProject

# Путь к файлу GeoJSON
geojson_file = '/path/to/your/geojson/file.geojson'

# Загрузка файла GeoJSON как векторного слоя
layer = QgsVectorLayer(geojson_file, 'Layer Name', 'ogr')
if not layer.isValid():
    print('Layer failed to load!')

# Добавление слоя в проект
QgsProject.instance().addMapLayer(layer)

# Применение файла стилей QML
qml_file = '/path/to/your/qml/style.qml'
layer.loadNamedStyle(qml_file)

# Сохранение изменений проекта
QgsProject.instance().write()

print('Layer loaded and styled successfully!')