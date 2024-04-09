import pandas as pd
import os
import pickle
from datetime import datetime
from io import StringIO
import geopandas as gpd
from math import radians, sin, cos, sqrt, atan2


def haversine(lat1, lon1, lat2, lon2):
    # Радиус Земли в километрах
    R = 6371.0
    
    # Преобразование координат из градусов в радианы
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)
    
    # Разница между широтами и долготами
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Вычисление расстояния с использованием формулы гаверсинуса
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c * 1000
    
    return distance

class PKL_class ():
      
    def __init__(self, dist1 = 0, dist2 = 0 , dist3 = 0 , PathToNetwork = '', NETWORK_NAME = '', path_to_txt_files = '', path_to_shp_buildings= ''):
        if path_to_txt_files == '':
            self.__path_gtfs = f'{PathToNetwork}/gtfs/{NETWORK_NAME}'
        else:
            self.__path_gtfs = path_to_txt_files

        self.__path_pkl = f'{PathToNetwork}/dict_builder/{NETWORK_NAME}'

        self.__dist1 = dist1
        self.__dist2 = dist2
        self.__dist3 = dist3
        self.__path_to_shp_buildings = path_to_shp_buildings
                

    def create_files(self):

        self.__unique_stops = set()
        
        self.load_gtfs()
               
        
        self.__stop_pkl = self.build_stops_dict()
        self.build_stopstimes_dict()
        self.build_stop_idx_in_route()
        
        #self.build_footpath_dict(self.__transfers_start_file, "transfers_start_dict.pkl", self.__dist1, True)
        #self.build_footpath_dict(self.__transfers_process_file, "transfers_process_dict.pkl", self.__dist2, True)
        #self.build_footpath_dict(self.__transfers_finish_file, "transfers_finish_dict.pkl", self.__dist3, True)
        
        self.build__route_by_stop()
        self.build_routes_by_stop_dict()

        self.build_reversed_stops_dict()
        self.build_reversed_stoptimes_dict()
        self.build_reverse_stoptimes_file_txt()
        self.build_rev_stop_idx_in_route()

    def load_gtfs(self):
        """
        Args:
        NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:
        stops_file (pandas.dataframe): dataframe with stop details.
        trips_file (pandas.dataframe): dataframe with trip details.
        stop_times_file (pandas.dataframe): dataframe with stoptimes details.
        transfers_file (pandas.dataframe): dataframe with transfers (footpath) details.
        """
        print ("start load GTFS")
        self.__stops_file = pd.read_csv(f'{self.__path_gtfs}/stops.txt', sep=',').sort_values(by=['stop_id']).reset_index(drop=True)
        self.__trips_file = pd.read_csv(f'{self.__path_gtfs}/trips.txt', sep=',')
        self.__stop_times_file = pd.read_csv(f'{self.__path_gtfs}/stop_times.txt', sep=',')

        print ("merging stoptimes")
        self.__stop_times_file = pd.merge(self.__stop_times_file, self.__trips_file, on='trip_id')
               
        self.__stop_times_file['arrival_time'] = self.__stop_times_file['arrival_time'].apply(lambda x: datetime.strptime(x, '%H:%M:%S').time())
        
        

    def build_stops_dict(self):
        """
            This function saves a dictionary to provide easy access to all the stops in the route.

            Args:
            stop_times_file (pandas.dataframe): stop_times.txt file in GTFS.
            trips_file (pandas.dataframe): trips.txt file in GTFS.
            NETWORK_NAME (str): path to network NETWORK_NAME.

            Returns:
            stops_dict (dict): keys: route_id, values: list of stop id in the route_id. Format-> dict[route_id] = [stop_id]
        """
        print("building stops dict")
                        
        if not os.path.exists(self.__path_pkl):
            os.makedirs(self.__path_pkl)
    
        stop_times = self.__stop_times_file

        print (f'stop_times {stop_times.head()}')
        
        route_groups = stop_times.drop_duplicates(subset=['route_id', 'stop_sequence'])[['stop_id', 'route_id', 'stop_sequence']].groupby('route_id')
        stops_dict = {id: routes.sort_values(by='stop_sequence')['stop_id'].to_list() for id, routes in route_groups}
        f = f'{self.__path_pkl}/stops_dict_pkl.pkl'
        
        with open(f, "wb") as pickle_file:
            pickle.dump(stops_dict, pickle_file)

        print("stops_dict done")
        
        return stops_dict


    def build_stopstimes_dict(self) -> dict:
        """
        This function saves a dictionary to provide easy access to all the trips passing along a route id. Trips are sorted
        in the increasing order of departure time. A trip is list of tuple of form (stop id, arrival time)

        Args:
        stop_times_file (pandas.dataframe): stop_times.txt file in GTFS.
        trips_file (pandas.dataframe): dataframe with transfers (footpath) details.
        NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:
        stoptimes_dict (dict): keys: route ID, values: list of trips in the increasing order of start time. Format-> dict[route_ID] = [trip_1, trip_2] where trip_1 = [(stop id, arrival time), (stop id, arrival time)]
        """
        print("building stoptimes dict")
        
        merged_data = self.__stop_times_file.merge(self.__trips_file, on='trip_id')
        print ('merged ok')
        grouped_data = merged_data.groupby('route_id_y')
        print ('grouped ok')
        result_dict = {}
        cycle = 0
        
        today_date = pd.Timestamp(datetime.now().date())

        for route_id, group in grouped_data:
            cycle += 1
            if cycle%500 == 0:
                print(f'{cycle} from {len(grouped_data)}')

            trip_dict = {}
            for trip_id, trip_data in group.groupby('trip_id'):
                trip_data = trip_data.sort_values('arrival_time', ascending = True)
                trip_dict[trip_id] = list(zip(trip_data['stop_id'], trip_data['arrival_time']))

            sorted_trips = sorted(trip_dict.items(), key=lambda x: x[1][0][1], reverse = False)
            result_dict[route_id] = {trip_id: [(stop_id, today_date.replace(hour=arrival_time.hour, minute=arrival_time.minute, second=arrival_time.second)) for stop_id, arrival_time in trip_data] for trip_id, trip_data in sorted_trips}

        with open(f'{self.__path_pkl}/stoptimes_dict_pkl.pkl', 'wb') as pickle_file:
            pickle.dump(result_dict, pickle_file)  
        print("stoptimes_dict_pkl done") 

        return 1
    

    def build_footpath_dict(self, obj_txt, file_name, distance, add_builds) -> dict:
        """
        This function saves a dictionary to provide easy access to all the footpaths through a stop id.

        Args:
            transfers_file (pandas.dataframe): dataframe with transfers (footpath) details.
            NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:
            footpath_dict (dict): keys: from stop_id, values: list of tuples of form (to stop id, footpath duration). Format-> dict[stop_id]=[(stop_id, footpath_duration)]
        """
        print("building footpath dict")
        
        footpath_dict = {}
        #g = self.__transfers_file.groupby("from_stop_id")
        g = obj_txt.groupby("from_stop_id")
        for from_stop, details in g:
            footpath_dict[from_stop] = []
            for _, row in details.iterrows():
                footpath_dict[from_stop].append(
                    (row.to_stop_id, pd.to_timedelta(float(row.min_transfer_time), unit='seconds')))
    
        # test
        if add_builds:
            
            buildings = self.get_buildings()
            count_building = len (buildings.items())
            print (f'count_building {count_building}')
            count = 0
            for building, buildings_coords in buildings.items():
                
                count += 1
                if count%100 == 0:
                    print (f' building {count} from {count_building}')

                build_item = building
                lng1, lat1  = buildings_coords

                for index, row in self.__stops_file.iterrows():
                    stop_item = row['stop_id']
                    lat2 = row['stop_lat']
                    lng2 = row['stop_lon']
                    
                    distance_calc = haversine(lat1, lng1, lat2, lng2)
                    #print (f' !!! lat1 {lat1}\n !!!lng1 {lng1} lat2 {lat2} lng2 {lng2}')
                    #print (f' !!! distance_calc {distance_calc}\n !!!distance {distance}')
                    
                    if distance_calc <= int(distance):
                        
                        if build_item not in footpath_dict:
                            footpath_dict[build_item] = [(stop_item, pd.to_timedelta(float(distance_calc), unit='seconds'))]
                        else:
                            footpath_dict[build_item].append((stop_item, pd.to_timedelta(float(distance_calc), unit='seconds')))

                        if stop_item not in footpath_dict:
                            footpath_dict[stop_item] = [(build_item, pd.to_timedelta(float(distance_calc), unit='seconds'))]
                        else:
                            footpath_dict[stop_item].append((build_item, pd.to_timedelta(float(distance_calc), unit='seconds')))    



        """
        footpath_dict[99999] = []
        footpath_dict[99999].extend([
                    (2, pd.to_timedelta(float(276), unit='seconds')),
                    (9, pd.to_timedelta(float(262), unit='seconds')),
                    (16, pd.to_timedelta(float(418), unit='seconds')),
                    (15, pd.to_timedelta(float(319), unit='seconds')),
                    (14, pd.to_timedelta(float(439), unit='seconds'))
                    ])
        
        key =2
        if key not in footpath_dict:
            footpath_dict[key] = [(99999, pd.to_timedelta(float(276), unit='seconds'))]
        else:
            footpath_dict[key].append((99999, pd.to_timedelta(float(276), unit='seconds')))

        key = 9
        if key not in footpath_dict:
            footpath_dict[key] = [(99999, pd.to_timedelta(float(262), unit='seconds'))]
        else:
            footpath_dict[key].append((99999, pd.to_timedelta(float(262), unit='seconds')))

        key = 16
        if key not in footpath_dict:
            footpath_dict[key] = [(99999, pd.to_timedelta(float(418), unit='seconds'))]
        else:
            footpath_dict[key].append((99999, pd.to_timedelta(float(418), unit='seconds')))    

        key = 15
        if key not in footpath_dict:
            footpath_dict[key] = [(99999, pd.to_timedelta(float(319), unit='seconds'))]
        else:
            footpath_dict[key].append((99999, pd.to_timedelta(float(319), unit='seconds')))    

        key = 14
        if key not in footpath_dict:
            footpath_dict[key] = [(99999, pd.to_timedelta(float(439), unit='seconds'))]
        else:
            footpath_dict[key].append((99999, pd.to_timedelta(float(439), unit='seconds')))    
                               
        footpath_dict[99998] = []
        footpath_dict[99998].extend([
                    (4, pd.to_timedelta(float(219), unit='seconds')),
                    (22, pd.to_timedelta(float(250), unit='seconds')),
                    (23, pd.to_timedelta(float(285), unit='seconds')),
                    (11, pd.to_timedelta(float(138), unit='seconds'))
                    ])
        
        #footpath_dict[4].extend([(99998, pd.to_timedelta(float(219), unit='seconds'))])
        #footpath_dict[22].extend([(99998, pd.to_timedelta(float(250), unit='seconds'))])
        #footpath_dict[23].extend([(99998, pd.to_timedelta(float(285), unit='seconds'))])
        #footpath_dict[11].extend([(99998, pd.to_timedelta(float(138), unit='seconds'))])

        
        key = 4
        if key not in footpath_dict:
            footpath_dict[key] = [(99998, pd.to_timedelta(float(219), unit='seconds'))]
        else:
            footpath_dict[key].append((99998, pd.to_timedelta(float(219), unit='seconds')))    

        key = 22
        if key not in footpath_dict:
            footpath_dict[key] = [(99998, pd.to_timedelta(float(250), unit='seconds'))]
        else:
            footpath_dict[key].append((99998, pd.to_timedelta(float(250), unit='seconds')))    

        key = 23
        if key not in footpath_dict:
            footpath_dict[key] = [(99998, pd.to_timedelta(float(285), unit='seconds'))]
        else:
            footpath_dict[key].append((99998, pd.to_timedelta(float(285), unit='seconds')))    
        
        key = 11
        if key not in footpath_dict:
            footpath_dict[key] = [(99998, pd.to_timedelta(float(138), unit='seconds'))]
        else:
            footpath_dict[key].append((99998, pd.to_timedelta(float(138), unit='seconds')))
                   
        """ 
        #with open(f'{self.__path_pkl}/transfers_dict_full.pkl', 'wb') as pickle_file:
        with open(f'{self.__path_pkl}/{file_name}', 'wb') as pickle_file:    
            pickle.dump(footpath_dict, pickle_file)
        
        

        for key, values in footpath_dict.items():
            for value_tuple in values:
                self.__unique_stops.add(value_tuple[0])

        self.__save_list_stops = list(self.__unique_stops)

                
        print(f'transfers_dict done' )

        return 1


    def build_stop_idx_in_route (self):
        """
        This function saves a dictionary to provide easy access to index of a stop in a route.

        Args:
            stop_times_file (pandas.dataframe): stop_times.txt file in GTFS.
            NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:    
            idx_by_route_stop_dict (dict): Keys: (route id, stop id), value: stop index. Format {(route id, stop id): stop index in route}.
        """
        stoptimes_txt = pd.read_csv(f'{self.__path_gtfs}/stop_times.txt')
        #stoptimes_txt = self.__stop_times_file
        stop_times_file = pd.merge(stoptimes_txt, self.__trips_file, on='trip_id')

        pandas_group = stop_times_file.groupby(["route_id", "stop_id"])
        idx_by_route_stop = {route_stop_pair: details.stop_sequence.iloc[0] for route_stop_pair, details in pandas_group}

        with open(f'{self.__path_pkl}/idx_by_route_stop.pkl', 'wb') as pickle_file:
            pickle.dump(idx_by_route_stop, pickle_file)
    
        return 1


    def build_routes_by_stop_dict(self):
        """
        This function saves a dictionary.

        Args:
            NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:
            routesindx_by_stop_dict (dict): Keys: stop id, value: [(route_id, stop index), (route_id, stop index)]
        """
        with open(f'{self.__path_pkl}/stops_dict_pkl.pkl', 'rb') as file:
            stops_dict = pickle.load(file)

    
        routes_stops_index = {}

        for route, stops in stops_dict.items():
            for stop_index, stop in enumerate(stops):
                routes_stops_index[(route, stop)] = stop_index
        routesindx_by_stop_dict = routes_stops_index


        with open(f'{self.__path_pkl}/routesindx_by_stop.pkl', 'wb') as pickle_file:
            pickle.dump(routesindx_by_stop_dict, pickle_file)
        print("routesindx_by_stop_dict done")
        return 1

    def build_reversed_stops_dict(self):
        print ('build_reversed_stops_dict')
 
        for key in self.__stop_pkl.keys():
            self.__stop_pkl[key] = self.__reverse(self.__stop_pkl[key])

        with open(self.__path_pkl+'/stops_dict_reversed_pkl.pkl', 'wb') as pickle_file:
            pickle.dump(self.__stop_pkl, pickle_file)    

        print("stops_dict_reversed_pkl done")
    
    def __reverse(self, lst):
       new_lst = lst[::-1]
       return new_lst
        
    def build_reversed_stoptimes_dict(self):
      
        merged_data = self.__stop_times_file.merge(self.__trips_file, on='trip_id')
        print ('merged ok')
        grouped_data = merged_data.groupby('route_id_y')
        print ('grouped ok')
        result_dict = {}
        cycle = 0
        
        today_date = pd.Timestamp(datetime.now().date())

        for route_id, group in grouped_data:
            cycle += 1
            if cycle%500 == 0:
                print(f'{cycle} from {len(grouped_data)}')

            trip_dict = {}
            for trip_id, trip_data in group.groupby('trip_id'):
                trip_data = trip_data.sort_values('arrival_time', ascending=False)
                trip_dict[trip_id] = list(zip(trip_data['stop_id'], trip_data['arrival_time']))

            sorted_trips = sorted(trip_dict.items(), key=lambda x: x[1][0][1], reverse=True)
            result_dict[route_id] = {trip_id: [(stop_id, today_date.replace(hour=arrival_time.hour, minute=arrival_time.minute, second=arrival_time.second)) for stop_id, arrival_time in trip_data] for trip_id, trip_data in sorted_trips}

        with open(f'{self.__path_pkl}/stoptimes_dict_reversed_pkl.pkl', 'wb') as pickle_file:
            pickle.dump(result_dict, pickle_file)  
        print("stoptimes_dict_reversed_pkl done")      

    # Функция для замены номеров остановок на противоположные в пределах каждой поездки
    def reverse_stop_sequence(self, group, *args, **kwargs):
       
        num_stops = len(group)
        reversed_stop_sequence = range(num_stops, 0, -1)
        group = group.assign(stop_sequence=reversed_stop_sequence)
        return group



    def build_reverse_stoptimes_file_txt(self):
        print ("build rev_stop_times.txt ok")    
        
        with open(self.__path_gtfs + "/stop_times.txt", "r") as f:
            allrows = f.readlines()
        

        # Преобразование списка строк в строку с разделителями и создание DataFrame
        # Convert a list of strings to a delimited string and create a DataFrame
        data_str = '\n'.join(allrows)
        df = pd.read_csv(StringIO(data_str))
               

        # Применение функции к DataFrame
        # Applying a Function to a DataFrame
    
        print ("reverse_stop_sequence ... ")
        df_result = df.groupby('trip_id', group_keys=False).apply(self.reverse_stop_sequence)
        print ("reverse_stop_sequence ...  ok")

        # Снова использование StringIO для записи DataFrame в строку
        # Using StringIO again to write a DataFrame to a String
        output_str = StringIO()
        df_result.to_csv(output_str, index=False, lineterminator='\n')
        print ("to_csv ok")
  
        # Получаем строку данных
        # We get a row of data
        output_data = output_str.getvalue()
        print ("getvalue ok")

        # Записываем данные обратно в файл
        # Write the data back to the file
        with open(self.__path_gtfs + "/rev_stop_times.txt", "w") as output_file:
            output_file.write(output_data)

        print ("rev_stop_times.txt ok")

        return 1
    

    def build_rev_stop_idx_in_route(self):
        """
        This function saves a dictionary to provide easy access to index of a stop in a route.

        Args:
        stop_times_file (pandas.dataframe): stop_times.txt file in GTFS.
        NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:
        idx_by_route_stop_dict (dict): Keys: (route id, stop id), value: stop index. Format {(route id, stop id): stop index in route}.
        """
          
        reverse_stoptimes_txt = pd.read_csv(f'{self.__path_gtfs}/rev_stop_times.txt')
        rev_stop_times_file = pd.merge(reverse_stoptimes_txt, self.__trips_file, on='trip_id')
    
        pandas_group = rev_stop_times_file.groupby(["route_id", "stop_id"])
        idx_by_route_stop = {route_stop_pair: details.stop_sequence.iloc[0] for route_stop_pair, details in pandas_group}

    
        with open(f'{self.__path_pkl}/rev_idx_by_route_stop.pkl', 'wb') as pickle_file:
            pickle.dump(idx_by_route_stop, pickle_file)

        print("rev idx_by_route_stop done")
        return 1
    
    def build__route_by_stop(self):
        """
        This function saves a dictionary to provide easy access to all the routes passing through a stop_id.

        Args:
        stop_times_file (pandas.dataframe): stop_times.txt file in GTFS.
        NETWORK_NAME (str): path to network NETWORK_NAME.

        Returns:
        route_by_stop_dict_new (dict): keys: stop_id, values: list of routes passing through the stop_id. Format-> dict[stop_id] = [route_id]
        """
        
        #stops_by_route = self.__stop_times_file.drop_duplicates(subset=['route_id', 'stop_sequence'])[['stop_id', 'route_id']].groupby('stop_id')
        stops_by_route = self.__stop_times_file.drop_duplicates(subset=['route_id', 'stop_id'])[['stop_id', 'route_id']].groupby('stop_id')

        route_by_stop_dict = {id: list(routes.route_id) for id, routes in stops_by_route}


        """
        route_by_stop_dict [99999] = []
        route_by_stop_dict [99998] = []
        """
        # add buildings
        
        building_dict = self.get_buildings()
        osm_ids = list(building_dict.keys())
        for building in osm_ids:
            route_by_stop_dict[building] = []

        with open(f'{self.__path_pkl}/routes_by_stop.pkl', 'wb') as pickle_file:
            pickle.dump(route_by_stop_dict, pickle_file)
    
        print("routes_by_stop done")
        return 1


    
    def get_stoptimes (self):
        path_to_stops_file = f'{self.__path_pkl}/stoptimes_dict_pkl.pkl'
        with open(path_to_stops_file, 'rb') as f:
            data = pickle.load(f)
        stoptimes = data

        return stoptimes

    def get_stops (self, limit):
        path_to_stops_file = f'{self.__path_pkl}/routes_by_stop.pkl'
        with open(path_to_stops_file, 'rb') as f:
            data = pickle.load(f)
        
        if limit > 0:
            data = {k: data[k] for k in sorted(data.keys())[:limit]}
        stops = sorted(data.keys())

        return stops

    def get_buildings (self):
        centroid_dict = {}
        if self.__path_to_shp_buildings !='':
            gdf = gpd.read_file(self.__path_to_shp_buildings)
            gdf['centroid'] = gdf['geometry'].centroid
            centroid_dict = {int (row['osm_id']): (row['centroid'].x, row['centroid'].y) for index, row in gdf.iterrows()}
        
        return centroid_dict
              

if __name__ == "__main__":
    
    PathToNetwork = "C:/Users/geosimlab/Documents/Igor/israel-public-transportation_gtfs"
    NETWORK_NAME = "israel-public-transportation_cut"
    path_to_txt_files = "C:/Users/geosimlab/Documents/Igor/sample_gtfs/full cut test rev"
    path_to_shape_buildings = "C:/Users/geosimlab/Documents/Igor/qgis_prj/haifa/haifa_buildings.shp"
    #path_to_shape_buildings = ""
    
    dist1 = 400
    dist2 = 400
    dist3 = 400

    PKL = PKL_class (dist1 , dist2 , dist3, PathToNetwork, NETWORK_NAME,  
                     path_to_txt_files = path_to_txt_files, path_to_shp_buildings = path_to_shape_buildings)
    PKL.create_files()
    
