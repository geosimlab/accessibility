"""
Creatint cut from GTFS using file routes.txt
Also creating file transfers.txt
Also creating archive including all files
"""
import pandas as pd
from haversine import haversine, Unit
import os
from zipfile import ZipFile
import codecs
import time
from collections import defaultdict
import numpy as np
import datetime

class GTFS ():
  
    
    def __init__(self, path_to_file, path_to_GTFS):
        self.__path_to_file = path_to_file
        self.__path_to_GTFS = path_to_GTFS
        self.__zip_name = f'{path_to_file}/gtfs_cut.zip'
        self.__directory = path_to_file


    def __zip_directory(self):    
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

    def create_tranfers_txt(self, distance, file_name):
        print ('create_tranfers_txt')
     
        path_to_file = self.__path_to_file.rstrip("//")

        try:
            stops_df = pd.read_csv(os.path.join(path_to_file, 'stops.txt'), encoding='windows-1255')
        except:
            stops_df = pd.read_csv(os.path.join(path_to_file, 'stops.txt'), encoding='utf-8')

        stops_df = stops_df.drop_duplicates(subset=['stop_id'])
        
        transfers = []
        len_df = len(stops_df)
    
        for i in range(len_df):

            if i%10 == 0:
                print (f' {i} from {len_df}')

            stop1 = stops_df.iloc[i]
            coord1 = (stop1['stop_lat'], stop1['stop_lon'])    
            for j in range(i+1, len(stops_df)):

               
                stop2 = stops_df.iloc[j]
                coord2 = (stop2['stop_lat'], stop2['stop_lon'])
                #distance_calc = round(geodesic(coord1, coord2).meters)
                distance_calc = round(haversine(coord1, coord2, unit=Unit.METERS))
                if distance_calc <= distance:
                    transfers.append({
                        'from_stop_id': stop1['stop_id'],
                        'to_stop_id': stop2['stop_id'],
                        'min_transfer_time': distance_calc
                    })
                    transfers.append({
                        'from_stop_id': stop2['stop_id'],
                        'to_stop_id': stop1['stop_id'],
                        'min_transfer_time': distance_calc
                    })

        transfers_df = pd.DataFrame(columns=['from_stop_id', 'to_stop_id', 'min_transfer_time'])
        if transfers:
            transfers_df = pd.DataFrame(transfers)
            transfers_df.to_csv(os.path.join(path_to_file, file_name), index=False, encoding='windows-1255')
                        
    
    def create_cut_from_GTFS(self):
        
        ###
        try:
            routes_df = pd.read_csv(f'{self.__path_to_file}//routes.txt', encoding='utf-8-sig')
        except:
            routes_df = pd.read_csv(f'{self.__path_to_file}//routes.txt', encoding='windows-1255')

        trips_df = pd.read_csv(f'{self.__path_to_GTFS}//trips.txt')
        merged_df = pd.merge(trips_df, routes_df, on='route_id', how='inner')
        merged_df.to_csv(f'{self.__path_to_file}//trips.txt', index=False, encoding='')
        ###
        trips_df = pd.read_csv(f'{self.__path_to_file}//trips.txt', encoding='utf-8')
        stops_df = pd.read_csv(f'{self.__path_to_GTFS}//stop_times.txt')
        unique_trip_ids = trips_df['trip_id'].unique()
        filtered_stops_df = stops_df[stops_df['trip_id'].isin(unique_trip_ids)].sort_values(by='arrival_time')


        filtered_stops_df[['hour', 'minute', 'second']] = filtered_stops_df['arrival_time'].str.split(':', expand=True)
        filtered_stops_df['hour'] = filtered_stops_df['hour'].astype(int)
        filtered_stops_df = filtered_stops_df[filtered_stops_df['hour'] <= 23]
        filtered_stops_df['arrival_time'] = filtered_stops_df['hour'].astype(str) + ':' + filtered_stops_df['minute'].astype(str) + ':' + filtered_stops_df['second'].astype(str)
        filtered_stops_df.drop(columns=['hour', 'minute', 'second'], inplace=True)

        filtered_stops_df.to_csv(f'{self.__path_to_file}//stop_times.txt', index=False, encoding='utf-8')
        ###

        stop_df = pd.read_csv(f'{self.__path_to_GTFS}//stops.txt')
        stop_times_df = pd.read_csv(f'{self.__path_to_file}//stop_times.txt')
        unique_stop_ids = stop_times_df['stop_id'].unique()
        filtered_stop_df = stop_df[stop_df['stop_id'].isin(unique_stop_ids)]
        filtered_stop_df.to_csv(f'{self.__path_to_file}//stops.txt', index=False, encoding='windows-1255')

        
       
        #self.create_tranfers_txt()

        # Coding 2 files (routes.txt, stops.txt)to utf-8-sig
        try:
            file_path = f'{self.__path_to_file}//routes.txt'
            with codecs.open(file_path, 'r', encoding='windows-1255') as file:
                content = file.read()
            with codecs.open(file_path, 'w', 'utf-8-sig') as file:
                file.write(content)
        except:
            error = 0

        file_path = f'{self.__path_to_file}//stops.txt'
        with codecs.open(file_path, 'r', encoding='windows-1255') as file:
            content = file.read()
        with codecs.open(file_path, 'w', 'utf-8-sig') as file:
            file.write(content)
        ################################
        self.__zip_directory()


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
            print (f'route {i} from {len(grouped_routes)}', end='\r')
                
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
        self.routes_df = routes_result_df 
        
        return 1
    
    # Группируем данные по trip_id и проверяем, что stop_sequence не имеет пропусков
    def check_stop_sequence(self, stop_times):
        trips_to_delete = set()
        for trip_id, group in stop_times.groupby('trip_id'):
            #max_sequence = group['stop_sequence'].max()
            max_sequence = group.index.get_level_values('stop_sequence').max()
            # Проверяем, равен ли размер группы последнему значению stop_sequence
            if len(group) != max_sequence:
                #print(f"Trip ID {trip_id} has missing stop_sequence values.")
                trips_to_delete.add(trip_id)
        return trips_to_delete
        
    def load_GTFS (self):
        print (f'Loadig data ...')
        self.routes_df = pd.read_csv(f'{self.__path_to_GTFS}//routes.txt', sep=',')
        self.trips_df = pd.read_csv(f'{self.__path_to_GTFS}//trips.txt', sep=',')
        self.stop_times_df = pd.read_csv(f'{self.__path_to_GTFS}//stop_times.txt', sep=',')
        self.stop_df = pd.read_csv(f'{self.__path_to_GTFS}//stops.txt', sep=',')
        self.calendar_df = pd.read_csv(f'{self.__path_to_GTFS}//calendar.txt', sep=',')

        old_len_trips = len(self.trips_df)    
        print('Remained only tuesday trips ...')
        self.trips_df = pd.merge(self.trips_df, self.calendar_df, on='service_id').query('tuesday == 1')
        print(f'Remained trip {len(self.trips_df)} from {old_len_trips}')

        old_len_stops_times = len(self.stop_times_df)  
        print (f'Merging data ...')
        self.merged_df = pd.merge(self.routes_df, self.trips_df, on="route_id")
        self.merged_df = pd.merge(self.merged_df, self.stop_times_df, on="trip_id")

        # filtering on trip_id
        self.stop_times_df = self.stop_times_df[self.stop_times_df['trip_id'].isin(self.trips_df['trip_id'])]
        print(f'Remained stop_times {len(self.stop_times_df)} from {old_len_stops_times}')
                

    def correcting_files2(self):
        print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.load_GTFS()
        self.create_my_routes()
        self.correct_repeated_stops_in_trips()

        trips_group = self.stop_times_df.groupby("trip_id") 
        
        self.stop_times_df.reset_index()
        
        print ("filtering stoptimes by arrival time sorting")
        old_len_stop_times = len (self.stop_times_df)
        trips_with_correct_timestamps = [id for id, trip in trips_group if list(trip.arrival_time) == list(trip.arrival_time.sort_values())]
        #self.stop_times_df = self.stop_times_df[self.stop_times_df["trip_id"].isin(trips_with_correct_timestamps)]    
        self.stop_times_df = self.stop_times_df[self.stop_times_df.index.get_level_values('trip_id').isin(trips_with_correct_timestamps)]

        print (f'remained len stop_times_df {len(self.stop_times_df)} from {old_len_stop_times}')

        print ("filtering stoptimes by stop sequence sorting")
        old_len_stop_times = len (self.stop_times_df)
        #trips_with_correct_stop_sequence = [id for id, trip in trips_group if list(trip.stop_sequence) == list(trip.stop_sequence.sort_values())]
        trips_with_correct_stop_sequence = [id for id, trip in trips_group if list(trip.index.get_level_values('stop_sequence')) == list(trip.index.get_level_values('stop_sequence').sort_values())]

        #self.stop_times_df = self.stop_times_df[self.stop_times_df["trip_id"].isin(trips_with_correct_stop_sequence)]     
        self.stop_times_df = self.stop_times_df[self.stop_times_df.index.get_level_values('trip_id').isin(trips_with_correct_stop_sequence)]
        print (f'remained len stop_times_df {len(self.stop_times_df)} from {old_len_stop_times}')

        #Еще один баг в GTFS – пропущенный номер stop_sequence
        # Проверка последовательности остановок и удаление неправильных trip_id
        print("filtering stoptimes by missing stop_sequence")
        old_len_stop_times = len (self.stop_times_df)
        trips_to_delete = self.check_stop_sequence(self.stop_times_df)
        #self.stop_times_df = self.stop_times_df[~self.stop_times_df['trip_id'].isin(trips_to_delete)]
        self.stop_times_df = self.stop_times_df[~self.stop_times_df.index.get_level_values('trip_id').isin(trips_to_delete)]
        print (f'remained len stop_times_df {len(self.stop_times_df)} from {old_len_stop_times}')

        self.save_GTFS()
        print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
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
        self.stop_times_df = self.stop_times_df.set_index(['trip_id', 'stop_sequence'])

        print (f'Grouping data ...')
        grouped = self.merged_df.groupby('route_id')

        self.max_stop_id = self.stop_df['stop_id'].max()

        all_routes = len(grouped)
        #print("time:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        count = 0
        

        new_stops = []
        for route_id, group in grouped:
            count += 1
            if count%100 == 0:
                print(f'Processing route {count} of {all_routes}', end='\r')
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
        print(f'', end='\n')
        count = 0
        len_stops = len(new_stops)               
        for route_id, stop_sequence, new_stop_id in new_stops:
            count += 1
            print(f'Replacing stop {count} of {len_stops}', end='\r')
            self.inplace_new_stop_on_all_trips(route_id, stop_sequence, new_stop_id)

        

    def save_GTFS(self):
        print(f'', end='\n')
        print ('Saving GTFS ...')                                
        self.stop_df.to_csv(f'{self.__path_to_file}//stops.txt', index=False) 
        self.stop_times_df.to_csv(f'{self.__path_to_file}//stop_times.txt', index=True)
        
        self.stop_times_df = self.stop_times_df.reset_index()
        unique_trip_ids = self.stop_times_df['trip_id'].unique()
        
        print ('filtering trips_file ...')
        
        #columns_to_drop = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday','start_date', 'end_date']
        #self.trips_df = self.trips_df.drop(columns=columns_to_drop)
        
        self.trips_df.columns = ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id']
        self.trips_df = self.trips_df[self.trips_df['trip_id'].isin(unique_trip_ids)]
        self.trips_df.to_csv(f'{self.__path_to_file}//trips.txt', header=['route_id','service_id','trip_id','trip_headsign','direction_id','shape_id'], index=False)
        
        print ('filtering routes_files ...')
        self.routes_df.columns = ['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color']
        unique_routes_ids =  self.trips_df['route_id'].unique()
        self.routes_df = self.routes_df[self.routes_df['route_id'].isin(unique_routes_ids)]
        self.routes_df.to_csv(f'{self.__path_to_file}//routes.txt', header=['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color'], index=False)
 
        
        return 1

    def get_new_stop_id(self):
        self.max_stop_id += 1
        if self.max_stop_id < 1000000:
            self.max_stop_id = 100000000
        return self.max_stop_id

    def create_new_stop (self, stop_id):
        
        new_stop_id = self.get_new_stop_id()
        new_stop = self.stop_df[self.stop_df['stop_id'] == stop_id].copy()
        new_stop['stop_id'] = new_stop_id
        self.stop_df = pd.concat([self.stop_df, new_stop], ignore_index=True)
        return new_stop_id
    
    def inplace_new_stop_on_all_trips (self, route_id, stop_sequence, new_stop_id):
        
        trip_ids = self.merged_df[self.merged_df["route_id"] == route_id]["trip_id"].unique()
        filter_condition = self.stop_times_df.index.get_level_values('trip_id').isin(trip_ids) & (self.stop_times_df.index.get_level_values('stop_sequence') == stop_sequence)
        self.stop_times_df.loc[filter_condition, "stop_id"] = new_stop_id
        
     
        
    
if __name__ == "__main__":
    
    path_to_file = r'C:/Users/geosimlab/Documents/Igor/sample_gtfs/separated double stops//'
    path_to_GTFS = r'C:/Users/geosimlab/Documents/Igor/israel-public-transportation_gtfs//'
        
    calc = GTFS(path_to_file, path_to_GTFS)
    #calc.correct_repeated_stops_in_trips()
    #calc.found_repeated_in_trips_stops()
    #calc.create_cut_from_GTFS()
    #calc.modify_time_and_sequence()
    #calc.modify_time_in_file (r'C:/Users/geosimlab/Documents/Igor/Protocols//access_1_detail.csv')
    #print (calc.change_time ('8:52:00'))
        
    calc.correcting_files2()

