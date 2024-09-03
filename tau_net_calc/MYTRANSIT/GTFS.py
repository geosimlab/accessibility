"""
Creatint cut from GTFS using file routes.txt
Also creating file transfers.txt
Also creating archive including all files
"""
from scipy.spatial import cKDTree
import pandas as pd
import csv
import pyproj

import geopandas as gpd
import codecs
import os
from shapely.geometry import Point
#from qgis.core import (QgsCoordinateReferenceSystem, 
#                       QgsPointXY,  
#                       QgsGeometry)
from zipfile import ZipFile
from datetime import datetime
from collections import defaultdict
from PyQt5.QtWidgets import QApplication
from footpath_on_road import footpath_on_road


class GTFS ():
  
    
    def __init__(self, 
                 parent, 
                 path_to_file, 
                 path_to_GTFS, 
                 layer_origins, 
                 layer_road,
                 layer_origins_field 
                 ):
        self.__path_to_file = path_to_file
        self.__path_to_GTFS = path_to_GTFS
        self.__zip_name = f'{path_to_file}/gtfs_cut.zip'
        self.__directory = path_to_file
        self.parent = parent
        self.layer_origins = layer_origins
        self.layer_road = layer_road
        self.layer_origins_field = layer_origins_field
        
        
        self.already_display_break = False
        


    def zip_directory(self):    
        timestamp = time.strftime("%Y%m%d%H%M%S")
        zip_name = f"{self.__zip_name}_{timestamp}.zip"

        with ZipFile(zip_name, 'w') as zipf:        
            for root, dirs, files in os.walk(self.__directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_name = os.path.basename(file_path)
                    if file_name != os.path.basename(zip_name):  
                        relative_path = os.path.relpath(file_path, self.__directory)        
                        zipf.write(file_path, relative_path)

    

    def create_cut_from_GTFS(self, path_routes_cut):
        
        file1 = os.path.join(self.__path_to_GTFS, 'routes.txt')
        file2 = os.path.join(self.__path_to_file, 'routes.txt')
        routes_eilat = pd.read_csv(path_routes_cut)
        routes = pd.read_csv(file1)
        filtered_routes = routes[routes['route_id'].isin(routes_eilat['route_id'])]
        filtered_routes.to_csv(file2, index=False)

        file3 = os.path.join(self.__path_to_GTFS, 'trips.txt')
        file4 = os.path.join(self.__path_to_file, 'trips.txt')
        trips = pd.read_csv(file3)
        filtered_trips = trips[trips['route_id'].isin(routes_eilat['route_id'])]
        filtered_trips.to_csv(file4, index=False)

        file5 = os.path.join(self.__path_to_GTFS, 'stop_times.txt')
        file6 = os.path.join(self.__path_to_file, 'stop_times.txt')
        stop_times = pd.read_csv(file5)
        filtered_stop_times = stop_times[stop_times['trip_id'].isin(filtered_trips['trip_id'])]
        filtered_stop_times.to_csv(file6, index=False)

        file7 = os.path.join(self.__path_to_GTFS, 'stops.txt')
        file8 = os.path.join(self.__path_to_file, 'stops.txt')
        stops = pd.read_csv(file7)
        filtered_stops = stops[stops['stop_id'].isin(filtered_stop_times['stop_id'])]
        filtered_stops.to_csv(file8, index=False)

        file9 = os.path.join(self.__path_to_GTFS, 'calendar.txt')
        file10 = os.path.join(self.__path_to_file, 'calendar.txt')
        calendar = pd.read_csv(file9)
        filtered_calendar = calendar[calendar['service_id'].isin(filtered_trips['service_id'])]
        filtered_calendar.to_csv(file10, index=False)


    def change_time(self, time1_str):
        time1 = pd.to_datetime(time1_str, errors='coerce')  # Преобразование времени, с возможностью обработки неправильных значений
        if not pd.isnull(time1):  # Проверка, является ли значение пустым
            next_day_midnight = pd.to_datetime('00:00:00') + pd.Timedelta(days=1)
            time_diff = next_day_midnight - pd.Timestamp.combine(pd.Timestamp.today(), time1.time())
            result = ((pd.Timestamp('00:00:00') + time_diff).time())
            return result
        else:
            return pd.NaT  # Возвращаем NaT для пустых значений времени


    # modify time 24:00:00 - xx.yy.zz in stop_times.txt
    # change stop_sequency, change sorting
    def modify_time_and_sequence (self):
        
        stops_df = pd.read_csv(f'{self.__path_to_file}//stop_times.txt')
        
        print ("# Filtering stoptimes")
        trips_df = pd.read_csv(f'{self.__path_to_file}//trips.txt', encoding='utf-8')
        unique_trip_ids = trips_df['trip_id'].unique()

        filtered_stops_df = stops_df[stops_df['trip_id'].isin(unique_trip_ids)].sort_values(by='arrival_time')
        filtered_stops_df[['hour', 'minute', 'second']] = filtered_stops_df['arrival_time'].str.split(':', expand=True)
        filtered_stops_df['hour'] = filtered_stops_df['hour'].astype(int)
        filtered_stops_df = filtered_stops_df[filtered_stops_df['hour'] <= 23]
        
        filtered_stops_df['arrival_time'] = filtered_stops_df['hour'].astype(str) + ':' + filtered_stops_df['minute'].astype(str) + ':' + filtered_stops_df['second'].astype(str)
        filtered_stops_df.drop(columns=['hour', 'minute', 'second'], inplace=True)

        df = filtered_stops_df



        print ("# Изменяем pd.to_datetime")
        df['arrival_time'] = pd.to_datetime(df['arrival_time'])
        df['departure_time'] = pd.to_datetime(df['departure_time'])

        # Получаем полночь (00:00:00) следующего дня
        next_day_midnight = pd.to_datetime('00:00:00') + pd.Timedelta(days=1)

        print ("# Изменяем время прибытия и отправления")
        # Изменяем время прибытия и отправления
        df['arrival_time'] = next_day_midnight - (df['arrival_time'] - df['arrival_time'].dt.normalize())
        df['departure_time'] = next_day_midnight - (df['departure_time'] - df['departure_time'].dt.normalize())
        df['arrival_time'] = df['arrival_time'].dt.time
        df['departure_time'] = df['departure_time'].dt.time

        print ("# Меняем порядок stop_sequence")
        # Меняем порядок stop_sequence
        df['stop_sequence'] = df.groupby('trip_id')['stop_sequence'].transform(lambda x: x.max() - x + x.min())

        print ("# Сортировка значений внутри каждого trip_id по stop_sequence")
        # Сортировка значений внутри каждого trip_id по stop_sequence
        df = df.groupby('trip_id').apply(lambda x: x.sort_values(by='stop_sequence')).reset_index(drop=True)

        print ("# Сохраняем изменения обратно в файл")
        # Сохраняем изменения обратно в файл
        df.to_csv(f'{self.__path_to_file}//stop_times_mod.txt', index=False)
        


    # modify time 24:00:00 - xx.yy.zz in filename (csv protokol)
    # in all columns
       
    def modify_time_in_file(self, filename):
        df = pd.read_csv(filename)

        # Преобразование всех столбцов времени в формат времени
        time_columns = ['Start_time', 'Bus1_start_time', 'Bus1_finish_time', 'Bus2_start_time', 'Bus2_finish_time', 'Bus3_start_time', 'Bus3_finish_time', 'Destination_time' ]
        for col in time_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')  # errors='coerce' позволяет обработать неправильные значения времени, преобразовав их в NaT

        # Применение функции change_time к каждому столбцу времени
        for col in time_columns:
            df[col] = df[col].apply(self.change_time)

        # Сохранение изменений в файл
        df.to_csv('C://Users//geosimlab//Documents//Igor//Protocols//modified_your_file.csv', index=False)

    
    # Функция для сравнения массивов stop_id и stop_sequence
    def compare_trip(self, trip1, trip2):
            return trip1['stop_id'] == trip2['stop_id'] and trip1['stop_sequence'] == trip2['stop_sequence']
            
    
    """"""""""""""
    #Dividing routes into subgroups if different trips are used at different stops
    """"""""""""""

    def create_my_routes(self):
        
        stop_times_file = self.stop_times_df.reset_index()

        routes_file = self.routes_df.reset_index()
        routes_file = routes_file.set_index('route_id')

        trips_file1 = self.trips_df.reset_index()
        trips_file2 = self.trips_df.reset_index()
        trips_file2 = trips_file2.set_index('trip_id')
                
        # merging
        df = pd.merge(stop_times_file, trips_file1, on='trip_id')
        df.set_index(['stop_id', 'stop_sequence'], inplace=True)
        
                                     
        # Словарь для хранения типов поездок и их массивов stop_id и stop_sequence
        trip_types = defaultdict(list)
        result = []
        result_routes = []
        
        # Группировка данных по route_id
        grouped_routes = df.groupby('route_id')
        

        
        # Итерация по группам
        i = 0
        for route_id, route_group in grouped_routes:
            i += 1
            if i%50 == 0:
                self.parent.setMessage(f'Separating route {i} from {len(grouped_routes)} ...')
                QApplication.processEvents()
                if self.verify_break():
                    return 0
            
                
            # Группировка данных по trip_id
            grouped_trips = route_group.groupby(['trip_id'])

            num_route = 0
            trip_types = defaultdict(list)
            # Итерация по поездкам
            for trip_id, trip_group in grouped_trips:
                
                trip_id = trip_id[0]
                target_trip = trips_file2.loc[trip_id]  # Доступ через индекс
                
                current_trip = {'stop_id': trip_group.index.get_level_values('stop_id').tolist(),
                'stop_sequence': trip_group.index.get_level_values('stop_sequence').tolist()}
                trip_found = False
    
                # Проверка текущей поездки на совпадение с уже существующими типами
                for trip_type, trip_type_data in trip_types.items():
                    for existing_trip in trip_type_data:
                   
                        if self.compare_trip(current_trip, existing_trip):

                            shape_id = target_trip['shape_id']
                            if pd.isnull(shape_id):
                                shape_id_str = ''
                            else:
                                shape_id_str = str(int(shape_id))
                           
                            result.append((trip_type, target_trip['service_id'], target_trip.name, target_trip['trip_headsign'],target_trip['direction_id'],shape_id_str))    
                            
                            trip_found = True
                            break

                    if trip_found:
                        break
    
                # Если поездка не имеет существующего типа, создаем новый тип
                if not trip_found:
                    num_route += 1
                    trip_types[f'{route_id}_{num_route}'].append(current_trip)
                    
                    shape_id = target_trip['shape_id']
                    if pd.isnull(shape_id):
                        shape_id_str = ''
                    else:
                        shape_id_str = str(int(shape_id))

                    new_route_id = f'{route_id}_{num_route}'
                    result.append((new_route_id, target_trip['service_id'], target_trip.name, target_trip['trip_headsign'], target_trip['direction_id'], shape_id_str))
                    target_routes = routes_file.loc[route_id] 
                    result_routes.append((new_route_id, target_routes['agency_id'],target_routes['route_short_name'],target_routes['route_long_name'],target_routes['route_desc'],target_routes['route_type'],target_routes['route_color']))    
                    
                             
        trips_result_df = pd.DataFrame(result)
        routes_result_df = pd.DataFrame(result_routes)

        self.trips_df = trips_result_df 
        self.trips_df.columns = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id']
        self.routes_df = routes_result_df
        self.routes_df.columns = ['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color'] 
        
        return 1
    
    # Группируем данные по trip_id и проверяем, что stop_sequence не имеет пропусков
    def check_stop_sequence(self, stop_times):
        trips_to_delete = set()
        i = 0
        for trip_id, group in stop_times.groupby('trip_id'):
            i += 1
            if i%100 == 0:
                if self.verify_break():
                    return 0   
                QApplication.processEvents()
    
            #max_sequence = group['stop_sequence'].max()
            max_sequence = group.index.get_level_values('stop_sequence').max()
            # Проверяем, равен ли размер группы последнему значению stop_sequence
            if len(group) != max_sequence:
                #print(f"Trip ID {trip_id} has missing stop_sequence values.")
                trips_to_delete.add(trip_id)
        return trips_to_delete
        
    def load_GTFS (self):
        
        self.parent.setMessage(f'Loadig data ...')
        QApplication.processEvents()
        if self.verify_break():
                return 0
        self.routes_df = pd.read_csv(f'{self.__path_to_GTFS}//routes.txt', sep=',')
        self.trips_df = pd.read_csv(f'{self.__path_to_GTFS}//trips.txt', sep=',')
        QApplication.processEvents()
        if self.verify_break():
                return 0
        self.stop_times_df = pd.read_csv(f'{self.__path_to_GTFS}//stop_times.txt', sep=',')
        QApplication.processEvents()
        if self.verify_break():
                return 0
        self.stop_df = pd.read_csv(f'{self.__path_to_GTFS}//stops.txt', sep=',')
        self.calendar_df = pd.read_csv(f'{self.__path_to_GTFS}//calendar.txt', sep=',')

        
        self.parent.setMessage(f'Selecting Tuesday trips ...')
        QApplication.processEvents()
        self.trips_df = pd.merge(self.trips_df, self.calendar_df, on='service_id').query('tuesday == 1')
        if self.verify_break():
                return 0        
        self.parent.setMessage(f'Merging data ...')
        QApplication.processEvents()
        self.merged_df = pd.merge(self.routes_df, self.trips_df, on="route_id")
        self.merged_df = pd.merge(self.merged_df, self.stop_times_df, on="trip_id")
        if self.verify_break():
                return 0
        # filtering on trip_id
        self.parent.setMessage(f'Filtering data ...')
        QApplication.processEvents()
        self.stop_times_df = self.stop_times_df[self.stop_times_df['trip_id'].isin(self.trips_df['trip_id'])]
        if self.verify_break():
                return 0
        
                

    def correcting_files(self):
        
        self.parent.progressBar.setMaximum(12)
        self.parent.progressBar.setValue(0)
        
        self.parent.break_on = False
        self.load_GTFS()
        self.parent.progressBar.setValue(1)
        if self.verify_break():
                return 0
        QApplication.processEvents()
                
        self.create_my_routes()
        self.parent.progressBar.setValue(2)
        if self.verify_break():
                return 0
        QApplication.processEvents()

        self.correct_repeated_stops_in_trips()
        self.parent.progressBar.setValue(3)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        
        trips_group = self.stop_times_df.groupby("trip_id") 
        
        self.stop_times_df.reset_index()
        
        
        self.parent.setMessage(f'Filtering data ...')
        self.parent.progressBar.setValue(4)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        #trips_with_correct_timestamps = [id for id, trip in trips_group if list(trip.arrival_time) == list(trip.arrival_time.sort_values())]
        trips_with_correct_timestamps = []
        i = 0 
        for id, trip in trips_group:
            i += 1
            if i%100 == 0:
                if self.verify_break():
                    return 0
                QApplication.processEvents()
            if list(trip.arrival_time) == list(trip.arrival_time.sort_values()):
                trips_with_correct_timestamps.append(id)
        self.stop_times_df = self.stop_times_df[self.stop_times_df.index.get_level_values('trip_id').isin(trips_with_correct_timestamps)]

               
        self.parent.setMessage(f'Filtering data ...')
        self.parent.progressBar.setValue(5)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        
        #trips_with_correct_stop_sequence = [id for id, trip in trips_group if list(trip.index.get_level_values('stop_sequence')) == list(trip.index.get_level_values('stop_sequence').sort_values())]
        trips_with_correct_stop_sequence = []
        i = 0
        for id, trip in trips_group:

            i += 1
            if i%100 ==0: 
                QApplication.processEvents()
                if self.verify_break():
                    return 0
                
            if list(trip.index.get_level_values('stop_sequence')) == list(trip.index.get_level_values('stop_sequence').sort_values()):
                trips_with_correct_stop_sequence.append(id)

        self.stop_times_df = self.stop_times_df[self.stop_times_df.index.get_level_values('trip_id').isin(trips_with_correct_stop_sequence)]

        #Еще один баг в GTFS – пропущенный номер stop_sequence
        # Проверка последовательности остановок и удаление неправильных trip_id
       
        self.parent.setMessage(f'Filtering data ...')
        self.parent.progressBar.setValue(6)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        trips_to_delete = self.check_stop_sequence(self.stop_times_df)
        self.stop_times_df = self.stop_times_df[~self.stop_times_df.index.get_level_values('trip_id').isin(trips_to_delete)]
        
        
        self.parent.setMessage(f'Saving ...')
        self.parent.progressBar.setValue(7)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        self.save_GTFS()
        
        """
        self.parent.setMessage(f'Peparing GTFS. Creating footpath air ...')
        self.parent.progressBar.setValue(8)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        self.create_footpath_AIR()
                        
        self.parent.setMessage(f'Peparing GTFS. Creating footpath air building to building...')
        self.parent.progressBar.setValue(9)
        if self.verify_break():
                return 0
        QApplication.processEvents()
        self.create_footpath_AIR_b_b()
        """
        
        footpath_road = footpath_on_road (self.parent, 
                                              self.layer_road, 
                                              self.layer_origins, 
                                              self.__path_to_file,
                                              self.layer_origins_field,
                                              )
        """
        self.parent.setMessage (f'Building network shortest paths…')
        QApplication.processEvents()
        self.parent.progressBar.setValue(10)
        if self.verify_break():
                return 0
        footpath_road.run_b_b()
        """
        
        self.parent.setMessage (f'Building network shortest paths…')
        QApplication.processEvents()
        self.parent.progressBar.setValue(11)
        if self.verify_break():
                return 0
        footpath_road.run()
        
        
        self.parent.progressBar.setValue(12)
        return 1
                
    def found_repeated_in_trips_stops(self):
        stop_times_file = pd.read_csv(f'{self.__path_to_GTFS}/stop_times.txt', sep=',')
        trips_group = stop_times_file.groupby("trip_id")

        all_group = len(trips_group)
        i = 0 
        for trip_id, trip in trips_group:
            i += 1
            #if i == 10000:
            #    break
            print (f'Run {i} from {all_group}', end='\r')
            stop_ids = {}  # Создаем пустое множество для отслеживания уникальных stop_id в поездке
                        
            # Проверяем каждую остановку в поездке
            for index, stop in trip.iterrows():
                stop_id = stop["stop_id"]
                if stop_id in stop_ids:
                    stop_ids[stop_id] += 1
                    if stop_ids[stop_id] > 2:
                        c = stop_ids[stop_id]
                        print(f"Trip {trip_id} Stop {stop_id} repeated {c} times")
                else:
                    stop_ids[stop_id] = 1
                
    def correct_repeated_stops_in_trips(self):
        
        self.stop_times_df.reset_index
        self.merged_df = pd.merge(self.routes_df, self.trips_df, on="route_id")
        self.merged_df = pd.merge(self.merged_df, self.stop_times_df, on="trip_id")

        self.stop_times_df = self.stop_times_df.set_index(['trip_id', 'stop_sequence'])

        #print (f'Merging data ...')
        self.parent.setMessage(f'Correcting repeated stops...')
        QApplication.processEvents()
        
        self.parent.setMessage(f'Grouping ...')
        QApplication.processEvents()

        grouped = self.merged_df.groupby('route_id')
        
        self.max_stop_id = self.stop_df['stop_id'].max()

        all_routes = len(grouped)
        count = 0
        
        new_stops = []
        for route_id, group in grouped:
            count += 1
            if count%100 == 0:
                
                self.parent.setMessage (f'Cleaning duplicate stops, route {count} of {all_routes}')
                QApplication.processEvents()
                if self.verify_break():
                    return 0

            first_trip_id = group['trip_id'].iloc[0]  
            trip = self.stop_times_df.xs(first_trip_id, level='trip_id')
            trip = trip.reset_index()
            stop_ids = []            
            
            for index, row in trip.iterrows():
                stop_id = row['stop_id']
                stop_sequence = row['stop_sequence']
                                            
                if stop_id in stop_ids:
                    new_stop_id = self.create_new_stop(stop_id)
                    new_stops.append((route_id, stop_sequence, new_stop_id))
                else:
                    stop_ids.append(stop_id)
            
                
        
        count = 0
        len_stops = len(new_stops)

                     
         # Optimize the stop replacement by bulk operation
        if new_stops:
            new_stops_df = pd.DataFrame(new_stops, columns=['route_id', 'stop_sequence', 'new_stop_id'])

            # Merge with stop_times_df to identify rows to update
            
            stops_to_update = self.merged_df.merge(new_stops_df, on=['route_id', 'stop_sequence'], how='inner')

            self.parent.setMessage (f'Cleaning duplicate stops...')
            QApplication.processEvents() 
            if self.verify_break():
                return 0   
            # Update the stop_ids in bulk
            for _, row in stops_to_update.iterrows():
                self.stop_times_df.loc[(row['trip_id'], row['stop_sequence']), 'stop_id'] = row['new_stop_id']
                        

    def save_GTFS(self):
        #print(f'', end='\n')
        #print ('Saving GTFS ...') 
        self.parent.setMessage ('Saving stops ...')
        QApplication.processEvents()  
        if self.verify_break():
                return 0                                 
        self.stop_df.to_csv(f'{self.__path_to_file}//stops.txt', index=False) 
        self.parent.setMessage ('Saving time schedule ...')
        QApplication.processEvents()  
        if self.verify_break():
                return 0                                 
        self.stop_times_df.to_csv(f'{self.__path_to_file}//stop_times.txt', index=True)
        
        self.stop_times_df = self.stop_times_df.reset_index()
        unique_trip_ids = self.stop_times_df['trip_id'].unique()
        
        self.parent.setMessage ('Saving trips ...')
        QApplication.processEvents()
        if self.verify_break():
                return 0    
        
        self.trips_df.columns = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id']
        self.trips_df = self.trips_df[self.trips_df['trip_id'].isin(unique_trip_ids)]
        self.trips_df.to_csv(f'{self.__path_to_file}//trips.txt', header=['route_id','service_id','trip_id','trip_headsign','direction_id','shape_id'], index=False)
        
        self.parent.setMessage ('Saving routes ...')
        QApplication.processEvents() 
        if self.verify_break():
                return 0   
        
        self.routes_df.columns = ['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color']
        unique_routes_ids =  self.trips_df['route_id'].unique()
        self.routes_df = self.routes_df[self.routes_df['route_id'].isin(unique_routes_ids)]
        self.routes_df.to_csv(f'{self.__path_to_file}//routes.txt', header=['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color'], index=False)
        if self.verify_break():
                return 0
        
        return 1

    def get_new_stop_id(self):
        self.max_stop_id += 1
        if self.max_stop_id < 10000000000:
            self.max_stop_id = 10000000000
        return self.max_stop_id

    def create_new_stop (self, stop_id):
        
        new_stop_id = self.get_new_stop_id()
        new_stop = self.stop_df[self.stop_df['stop_id'] == stop_id].copy()
        new_stop['stop_id'] = new_stop_id
        self.stop_df = pd.concat([self.stop_df, new_stop], ignore_index=True)
        return new_stop_id
        

    def create_stops_gpd(self):
        wgs84 = pyproj.CRS('EPSG:4326')  # WGS 84
        web_mercator = pyproj.CRS('EPSG:2039')  # Web Mercator
        transformer = pyproj.Transformer.from_crs(wgs84, web_mercator, always_xy=True)

        points = []
        
        filename = self.__path_to_file + 'stops.txt'
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            #next(reader, None)  # Пропускаем заголовок
            for row in reader:
                stop_id = int(row['stop_id'])
                latitude = float(row['stop_lat'])  # Широта
                longitude = float(row['stop_lon'])  # Долгота
                x_meter, y_meter = transformer.transform(longitude, latitude)
                points.append((stop_id, Point(x_meter, y_meter)))  

        points_copy = gpd.GeoDataFrame(points, columns=['stop_id', 'geometry'], crs=web_mercator)
        return points_copy
    """
    def create_footpath_AIR (self):    
        
        points_copy = self.create_stops_gpd()
        points_layer = self.layer_origins
        
        crs_target = QgsCoordinateReferenceSystem("EPSG:2039")
        points_layer.setCrs(crs_target)

        centroids = []
        for feature in points_layer.getFeatures():
            geom = feature.geometry()
            
            centroid = geom.centroid().asPoint()
            centroids.append((feature['osm_id'], QgsPointXY(centroid)))

        points_layer.updateExtents()

        centroids_coords = [(centroid[1].x(), centroid[1].y()) for centroid in centroids]
        centroids_tree = cKDTree(centroids_coords)

        stops_coords = [(geom.x, geom.y) for geom in points_copy.geometry]
        stops_tree = cKDTree(stops_coords)

       
    
        close_pairs = []

        current_combination = 0
        # Найди пары здание - остановка 
        
        for i, geom in enumerate(points_copy.geometry):
            nearest_centroids = centroids_tree.query_ball_point((geom.x, geom.y), 400)
            for j in nearest_centroids:
                current_combination = current_combination + 1
                if current_combination%1000 == 0:
                    self.parent.setMessage(f'Peparing GTFS. Processing combination build<->stop {current_combination}')
                    QApplication.processEvents()
                    if self.verify_break():
                        return 0
                    
                stop_id1 = points_copy.iloc[i]['stop_id']
                centroid_geom = QgsGeometry.fromPointXY(centroids[j][1])
                distance = geom.distance(Point(centroid_geom.asPoint().x(), centroid_geom.asPoint().y()))
                if distance <= 400:
                    close_pairs.append((centroids[j][0], stop_id1, round(distance)))
       
        # Найди пары остановок
        for i, geom in enumerate(points_copy.geometry):
            nearest_stops = stops_tree.query_ball_point((geom.x, geom.y), 400)
            for j in nearest_stops:
                if i == j:
                    continue
                current_combination +=  1
                if current_combination%1000 == 0:
                    self.parent.setMessage(f'Peparing GTFS. Processing combination stop<->stop {current_combination}')
                    QApplication.processEvents()
                    if self.verify_break():
                        return 0
                    
                stop_id1 = points_copy.iloc[i]['stop_id']
                distance = geom.distance(points_copy.iloc[j]['geometry'])
                if distance <= 400 and points_copy.iloc[j]['stop_id'] != stop_id1:
                    close_pairs.append((points_copy.iloc[j]['stop_id'], stop_id1, round(distance))) 
           
        filename = self.__path_to_file + 'footpath_AIR.txt'
        with open(filename, 'w') as file:
            file.write(f'from_stop_id,to_stop_id,min_transfer_time\n')
            for pair in close_pairs:
                id_from_points_layer = pair[0]
                stop_id1 = pair[1]
                distance = pair[2]
                file.write(f'{id_from_points_layer},{stop_id1},{distance}\n')
                file.write(f'{stop_id1},{id_from_points_layer},{distance}\n')
    """
    """
    def create_footpath_AIR_b_b (self):    
               
        points_layer = self.layer_origins
        crs_target = QgsCoordinateReferenceSystem("EPSG:2039")
        points_layer.setCrs(crs_target)

        centroids = []
        for feature in points_layer.getFeatures():
            geom = feature.geometry()
            
            centroid = geom.centroid().asPoint()
            centroids.append((feature['osm_id'], QgsPointXY(centroid)))

        points_layer.updateExtents()

        centroids_coords = [(centroid[1].x(), centroid[1].y()) for centroid in centroids]
        centroids_tree = cKDTree(centroids_coords)
    
        close_pairs = []
        current_combination = 0
        # Найди пары здание - здание
        for i, (id1, geom1) in enumerate(centroids):
            nearest_centroids = centroids_tree.query_ball_point((geom1.x(), geom1.y()), 400)
            var = QgsGeometry.fromPointXY(geom1)

            for j in nearest_centroids:
                current_combination += 1
                if current_combination % 100000 == 0:
                    self.parent.setMessage(f'Peparing GTFS. Processing combination build<->build {current_combination}')
                    QApplication.processEvents()
                    if self.verify_break():
                        return 0

                id2 = centroids[j][0]
                geom2 = centroids[j][1]
                if id1 == id2:
                         continue
                distance = var.distance(QgsGeometry.fromPointXY(geom2))
                if distance <= 400:
                    close_pairs.append((id1, id2, round(distance)))
        
        filename = self.__path_to_file + 'footpath_AIR_b_b.txt'
        with open(filename, 'w') as file:
            file.write(f'from_osm_id,to_osm_id,min_transfer_time\n')
            for pair in close_pairs:
                b1 = pair[0]
                b2 = pair[1]
                distance = pair[2]
                file.write(f'{b1},{b2},{distance}\n')
    """                
    
    def verify_break (self):
      if self.parent.break_on:
            self.parent.setMessage ("Dictionary construction is interrupted ")
            if not self.already_display_break:
                self.parent.textLog.append (f'<a><b><font color="red">Process preparing GTFS is break</font> </b></a>')
                self.already_display_break = True
            self.parent.progressBar.setValue(0)  
            return True
      return False


if __name__ == "__main__":
    
    #path_to_file = r'C:/Users/geosimlab/Documents/Igor/sample_gtfs/separated double stops//'
    #path_to_GTFS = r'C:/Users/geosimlab/Documents/Igor/israel-public-transportation_gtfs//'
    
    parent = ""
    path_to_file = r"C:\Users\geosimlab\Documents\Igor\israel-public-transportation_gtfs\eilat\cut_gtfs" 
    path_to_GTFS = r"C:\Users\geosimlab\Documents\Igor\israel-public-transportation_gtfs\eilat\full_gtfs" 
    layer_origins = ""
    layer_road = ""

    calc = GTFS(parent, 
                 path_to_file, 
                 path_to_GTFS, 
                 layer_origins, 
                 layer_road
                 )
    calc.create_cut_from_GTFS(r"C:\Users\geosimlab\Documents\Igor\israel-public-transportation_gtfs\eilat\cut_gtfs\routes_eilat.csv")
    #calc.correct_repeated_stops_in_trips()
    #calc.found_repeated_in_trips_stops()
    
    #calc.modify_time_and_sequence()
    #calc.modify_time_in_file (r'C:/Users/geosimlab/Documents/Igor/Protocols//access_1_detail.csv')
    #print (calc.change_time ('8:52:00'))
    #calc.correcting_files()

