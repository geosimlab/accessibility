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


from itertools import combinations
from multiprocessing import Pool

class GTFS ():
  
    
    def __init__(self, path_to_file, path_to_GTFS):
        self.__path_to_file = path_to_file
        self.__path_to_GTFS = path_to_GTFS
        self.__zip_name = f'{path_to_file}\gtfs_cut.zip'
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
     
        path_to_file = self.__path_to_file.rstrip("\\")

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
            routes_df = pd.read_csv(f'{self.__path_to_file}\\routes.txt', encoding='utf-8-sig')
        except:
            routes_df = pd.read_csv(f'{self.__path_to_file}\\routes.txt', encoding='windows-1255')

        trips_df = pd.read_csv(f'{self.__path_to_GTFS}\\trips.txt')
        merged_df = pd.merge(trips_df, routes_df, on='route_id', how='inner')
        merged_df.to_csv(f'{self.__path_to_file}\\trips.txt', index=False, encoding='')
        ###
        trips_df = pd.read_csv(f'{self.__path_to_file}\\trips.txt', encoding='utf-8')
        stops_df = pd.read_csv(f'{self.__path_to_GTFS}\\stop_times.txt')
        unique_trip_ids = trips_df['trip_id'].unique()
        filtered_stops_df = stops_df[stops_df['trip_id'].isin(unique_trip_ids)].sort_values(by='arrival_time')


        filtered_stops_df[['hour', 'minute', 'second']] = filtered_stops_df['arrival_time'].str.split(':', expand=True)
        filtered_stops_df['hour'] = filtered_stops_df['hour'].astype(int)
        filtered_stops_df = filtered_stops_df[filtered_stops_df['hour'] <= 23]
        filtered_stops_df['arrival_time'] = filtered_stops_df['hour'].astype(str) + ':' + filtered_stops_df['minute'].astype(str) + ':' + filtered_stops_df['second'].astype(str)
        filtered_stops_df.drop(columns=['hour', 'minute', 'second'], inplace=True)

        filtered_stops_df.to_csv(f'{self.__path_to_file}\\stop_times.txt', index=False, encoding='utf-8')
        ###

        stop_df = pd.read_csv(f'{self.__path_to_GTFS}\\stops.txt')
        stop_times_df = pd.read_csv(f'{self.__path_to_file}\\stop_times.txt')
        unique_stop_ids = stop_times_df['stop_id'].unique()
        filtered_stop_df = stop_df[stop_df['stop_id'].isin(unique_stop_ids)]
        filtered_stop_df.to_csv(f'{self.__path_to_file}\\stops.txt', index=False, encoding='windows-1255')

        
       
        #self.create_tranfers_txt()

        # Coding 2 files (routes.txt, stops.txt)to utf-8-sig
        try:
            file_path = f'{self.__path_to_file}\\routes.txt'
            with codecs.open(file_path, 'r', encoding='windows-1255') as file:
                content = file.read()
            with codecs.open(file_path, 'w', 'utf-8-sig') as file:
                file.write(content)
        except:
            error = 0

        file_path = f'{self.__path_to_file}\\stops.txt'
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
        """
        df = pd.read_csv(f'{self.__path_to_file}\\stop_times.txt')
        print ('filtering')
        # Отфильтровать значения времени, превышающие 24 часа
        df['arrival_time'] = df['arrival_time'].apply(lambda x: x if (pd.to_datetime(x, errors='coerce').hour or 0) < 24 else None)
        df['departure_time'] = df['departure_time'].apply(lambda x: x if (pd.to_datetime(x, errors='coerce').hour or 0) < 24 else None)

        print ('deleting')
        # Удаление строк с недопустимыми значениями времени
        df.dropna(subset=['arrival_time', 'departure_time'], inplace=True)
        print ('convert')
        # Преобразование времени прибытия и отправления в формат datetime
        df['arrival_time'] = pd.to_datetime(df['arrival_time'])
        df['departure_time'] = pd.to_datetime(df['departure_time'])

        # Получение полночи следующего дня
        next_day_midnight = pd.to_datetime('00:00:00') + pd.Timedelta(days=1)
        print ('change time')
        # Изменение времени прибытия и отправления
        df['arrival_time'] = next_day_midnight - (df['arrival_time'] - df['arrival_time'].dt.normalize())
        df['departure_time'] = next_day_midnight - (df['departure_time'] - df['departure_time'].dt.normalize())

        # Применение операции остатка от деления на 24 часа
        #df['arrival_time'] = df['arrival_time'] % pd.Timedelta(days=1)
        #df['departure_time'] = df['departure_time'] % pd.Timedelta(days=1)

        print ('convert2')
        # Преобразование времени обратно в формат времени
        df['arrival_time'] = df['arrival_time'].dt.time
        df['departure_time'] = df['departure_time'].dt.time

        print ('change stopseq')
        # Меняем порядок stop_sequence
        df['stop_sequence'] = df.groupby('trip_id')['stop_sequence'].transform(lambda x: x.max() - x + x.min())

        print ('sorting')
        # Сортировка значений внутри каждого trip_id по stop_sequence
        df = df.groupby('trip_id').apply(lambda x: x.sort_values(by='stop_sequence')).reset_index(drop=True)

        print ('save')    
        # Сохраняем изменения обратно в файл
        df.to_csv(f'{self.__path_to_file}\\stop_times_mod.txt', index=False)
        print ('stop_times_mod done')
        """
        stops_df = pd.read_csv(f'{self.__path_to_file}\\stop_times.txt')
        
        print ("# Filtering stoptimes")
        trips_df = pd.read_csv(f'{self.__path_to_file}\\trips.txt', encoding='utf-8')
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
        df.to_csv(f'{self.__path_to_file}\\stop_times_mod.txt', index=False)
        


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
        df.to_csv('C:\\Users\\geosimlab\\Documents\\Igor\\Protocols\\modified_your_file.csv', index=False)

    
    # Функция для сравнения массивов stop_id и stop_sequence
    def compare_trip(self, trip1, trip2):
            return trip1['stop_id'] == trip2['stop_id'] and trip1['stop_sequence'] == trip2['stop_sequence']
    
    """"""""""""""
    #Dividing routes into subgroups if different trips are used at different stops
    """"""""""""""

    def create_my_routes(self):
        file1 = self.__path_to_file + 'stop_times.txt'
        file2 = self.__path_to_file + 'trips.txt'
        file3 = self.__path_to_file + 'routes.txt'

        print ('reading')
        df = pd.read_csv(file1)
        trips_file = pd.read_csv(file2)
        print ('merging')
        df = pd.merge(df, trips_file, on='trip_id')

        routes_file = pd.read_csv(file3)
                     
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

            if i%100 == 0:
                print (f'route {i} from {len(grouped_routes)}')
                
                trips_result_df = pd.DataFrame(result)
                routes_result_df = pd.DataFrame(result_routes)

                trips_result_df.to_csv(self.__path_to_file + 'my_trips.txt', header=['route_id','service_id','trip_id','trip_headsign','direction_id','shape_id'], index=False)
                routes_result_df.to_csv(self.__path_to_file + 'my_routes.txt', header=['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color'], index=False)
                return
                

            

            # Группировка данных по trip_id
            grouped_trips = route_group.groupby(['trip_id'])

            num_route = 0
            trip_types = defaultdict(list)
            # Итерация по поездкам
            for trip_id, trip_group in grouped_trips:

                
                trip_id = trip_id[0]
                target_trip = trips_file.loc[trips_file['trip_id'] == trip_id].iloc[0]
                
                current_trip = {'stop_id': trip_group['stop_id'].tolist(), 'stop_sequence': trip_group['stop_sequence'].tolist()}

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
                           
                            result.append((trip_type, target_trip['service_id'],target_trip['trip_id'],target_trip['trip_headsign'],target_trip['direction_id'],shape_id_str))    
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
                    result.append((new_route_id, target_trip['service_id'],target_trip['trip_id'],target_trip['trip_headsign'],target_trip['direction_id'],shape_id_str))    

                    target_routes = routes_file.loc[routes_file['route_id'] == route_id].iloc[0]
                    #print (f'new_route_id {new_route_id}')
                    result_routes.append((new_route_id, target_routes['agency_id'],target_routes['route_short_name'],target_routes['route_long_name'],target_routes['route_desc'],target_routes['route_type'],target_routes['route_color']))    

                    
                             
        trips_result_df = pd.DataFrame(result)
        routes_result_df = pd.DataFrame(result_routes)

        trips_result_df.to_csv(self.__path_to_file + 'my_trips.txt', header=['route_id','service_id','trip_id','trip_headsign','direction_id','shape_id'], index=False)
        routes_result_df.to_csv(self.__path_to_file + 'my_routes.txt', header=['route_id','agency_id','route_short_name','route_long_name','route_desc','route_type','route_color'], index=False)
        
        return 1
    
    # Группируем данные по trip_id и проверяем, что stop_sequence не имеет пропусков
    def check_stop_sequence(self, stop_times):
        trips_to_delete = set()
        for trip_id, group in stop_times.groupby('trip_id'):
            max_sequence = group['stop_sequence'].max()
            # Проверяем, равен ли размер группы последнему значению stop_sequence
            if len(group) != max_sequence:
                print(f"Trip ID {trip_id} has missing stop_sequence values.")
                trips_to_delete.add(trip_id)
        return trips_to_delete
        
    
    def correcting_files(self):
        print ("start load GTFS")
        
        routes_file = pd.read_csv(f'{self.__path_to_file}/routes.txt', sep=',')
        trips_file = pd.read_csv(f'{self.__path_to_file}/trips.txt', sep=',')
        calendar_file = pd.read_csv(f'{self.__path_to_file}/calendar.txt', sep=',')
        stop_times_file = pd.read_csv(f'{self.__path_to_file}/stop_times.txt', sep=',')

        # Filtering trips  on field service_id, take tips only on day TUESDAY
        #print (f' len(self.__trips_file before) {len(self.__trips_file)}')
        trips_file = pd.merge(trips_file, calendar_file, on='service_id').query('tuesday == 1')
        #print (f' len(self.__trips_file) after filter calendar {len(self.__trips_file)}')


        # filtering hour <= 23
        print ("filtering stoptimes <=23")
        stop_times_file[['hour', 'minute', 'second']] = stop_times_file['arrival_time'].str.split(':', expand=True)
        stop_times_file['hour'] = stop_times_file['hour'].astype(int)
        stop_times_file = stop_times_file[stop_times_file['hour'] <= 23]
        #self.__stop_times_file['arrival_time'] = self.__stop_times_file['hour'].astype(str) + ':' + self.__stop_times_file['minute'].astype(str) + ':' + filtered_stops_df['second'].astype(str)
        #self.__stop_times_file.drop(columns=['hour', 'minute', 'second'], inplace=True)
        ####

        #stop_times_file.arrival_time = pd.to_datetime(stop_times_file.arrival_time, format='%H:%M:%S')

        print ("merging stoptimes")
        stop_times_file = pd.merge(stop_times_file, trips_file, on='trip_id')

        trips_group = stop_times_file.groupby("trip_id") 
        # Verify cycle_tips        
        
        """
        routes_group = self.__stop_times_file.groupby("route_id") 
        count_cycle_routes = 0
        for route_id, route_group in routes_group:
            trips_group = route_group.groupby("trip_id")
            for trip_id, trip in trips_group:
                first_stop = trip.iloc[0]
                last_stop = trip.iloc[-1]
                if first_stop["stop_id"] == last_stop["stop_id"]:
                    count_cycle_routes += 1
                    break
                
        print (f'count_cycle_routes = {count_cycle_routes}')
        """
        print ("filtering stoptimes by cycle trip")
        """
        trips_no_cycle = []
        count_cyclce_trip = 0
        for trip_id, trip in trips_group:
            first_stop = trip.iloc[0]
            last_stop = trip.iloc[-1]
            if first_stop["stop_id"] != last_stop["stop_id"]:
                count_cyclce_trip += 1
                trips_no_cycle.append(trip_id)
        """
        # remove all trips with cycle
        trips_no_cycle = []
        for trip_id, trip in trips_group:
            stop_ids = set()  # Создаем пустое множество для отслеживания уникальных stop_id в поездке
            is_cycle_trip = False  # Флаг для обозначения циклической поездки

            # Проверяем каждую остановку в поездке
            for index, stop in trip.iterrows():
                stop_id = stop["stop_id"]
                if stop_id in stop_ids:
                    is_cycle_trip = True  # Если текущий stop_id уже был встречен, обозначаем поездку как циклическую
                    break
                else:
                    stop_ids.add(stop_id)  # Добавляем stop_id в множество

            # Если поездка не циклическая, увеличиваем счетчик
            if not is_cycle_trip:
                #count_no_cycle_trip += 1
                trips_no_cycle.append(trip_id)

        stop_times_file = stop_times_file[stop_times_file["trip_id"].isin(trips_no_cycle)]
        

        # This drops all trips for which timestamps and stop_sequence are not sorted
         
        print ("filtering stoptimes by arrival time sorting")
        trips_with_correct_timestamps = [id for id, trip in trips_group if list(trip.arrival_time) == list(trip.arrival_time.sort_values())]
        """
        incorrectly_sorted_trips = []
        for trip_id, trip in trips_group:
        # Проверяем, если временные метки прибытия не равны их отсортированной версии
            if list(trip.arrival_time) != list(trip.arrival_time.sort_values()):
                incorrectly_sorted_trips.append(trip_id)
        print("Неправильно отсортированные поездки time:")
        print(incorrectly_sorted_trips)
        """
        stop_times_file = stop_times_file[stop_times_file["trip_id"].isin(trips_with_correct_timestamps)]    

        print ("filtering stoptimes by stop sequence sorting")
        trips_with_correct_stop_sequence = [id for id, trip in trips_group if list(trip.stop_sequence) == list(trip.stop_sequence.sort_values())]
        
        """
        incorrectly_sorted_stop_sequence = []
        for trip_id, trip in trips_group:
        # Проверяем, если временные метки прибытия не равны их отсортированной версии
            if list(trip.stop_sequence) != list(trip.stop_sequence.sort_values()):
                incorrectly_sorted_stop_sequence.append(trip_id)
        print("Неправильно отсортированные поездки stop_sequence:")
        print(incorrectly_sorted_stop_sequence)
        """    
        stop_times_file = stop_times_file[stop_times_file["trip_id"].isin(trips_with_correct_stop_sequence)] 


        #Еще один баг в GTFS – пропущенный номер stop_sequence
        # Проверка последовательности остановок и удаление неправильных trip_id
        print("filtering stoptimes by missing stop_sequence")
        trips_to_delete = self.check_stop_sequence(stop_times_file)
        stop_times_file = stop_times_file[~stop_times_file['trip_id'].isin(trips_to_delete)]

        print ('saving stop_times file ...')
        stop_times_file_filer_fields = stop_times_file[['trip_id','arrival_time','departure_time','stop_id','stop_sequence','pickup_type','drop_off_type','shape_dist_traveled']]
        stop_times_file_filer_fields.to_csv(f'{self.__path_to_file}\\stop_times_mod.txt', index=False)

        unique_trip_ids = stop_times_file_filer_fields['trip_id'].unique()

        print ('filtering and saving trips_file ...')
        filtered_trips = trips_file[trips_file['trip_id'].isin(unique_trip_ids)]
        filtered_trips= filtered_trips[['route_id','service_id','trip_id','trip_headsign','direction_id','shape_id']]
        filtered_trips.to_csv(f'{self.__path_to_file}\\trips_mod.txt', index=False)  

        print ('filtering and saving routes_files ...')
        
        unique_routes_ids = filtered_trips['route_id'].unique()
        filtered_routes = routes_file[routes_file['route_id'].isin(unique_routes_ids)]
        filtered_routes.to_csv(f'{self.__path_to_file}\\routes_mod.txt', index=False)  
        


if __name__ == "__main__":
    
    path_to_file = r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\full cut test\\'
    path_to_GTFS = r'C:\Users\geosimlab\Documents\Igor\israel-public-transportation_gtfs\\'
        
    calc = GTFS(path_to_file, path_to_GTFS)
    #calc.create_cut_from_GTFS()
    calc.modify_time_and_sequence()
    #calc.modify_time_in_file (r'C:\Users\geosimlab\Documents\Igor\Protocols\\access_1_detail.csv')
    #print (calc.change_time ('8:52:00'))
    
    #calc.create_tranfers_txt(400, "transfers_start.txt")
    #calc.create_tranfers_txt(400, "transfers_process.txt")
    #calc.create_tranfers_txt(400, "transfers_finish.txt")
    #calc.create_my_routes()
    #calc.correcting_files()

