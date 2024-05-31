"""
Module contains function related to RAPTOR, rRAPTOR, One-To-Many rRAPTOR, HypRAPTOR
"""
from collections import deque as deque
from PyQt5.QtWidgets import QApplication

def seconds_to_time(total_seconds):
    total_seconds = round(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    return time_str

def initialize_raptor(routes_by_stop_dict: dict, SOURCE: int, MAX_TRANSFER: int) -> tuple:
    '''
    Initialize values for RAPTOR.

    Args:
        routes_by_stop_dict (dict): preprocessed dict. Format {stop_id: [id of routes passing through stop]}.
        SOURCE (int): stop id of source stop.
        MAX_TRANSFER (int): maximum transfer limit.

    Returns:
        marked_stop (deque): deque to store marked stop.
        marked_stop_dict (dict): Binary variable indicating if a stop is marked. Keys: stop Id, value: 0 or 1.
        label (dict): nested dict to maintain label. Format {round : {stop_id: pandas.datetime}}.
        pi_label (dict): Nested dict used for backtracking labels. Format {round : {stop_id: pointer_label}}
        if stop is reached by walking, pointer_label= ('walking', from stop id, to stop id, time, arrival time)}} else pointer_label= (trip boarding time, boarding_point, stop id, arr_by_trip, trip id)
        star_label (dict): dict to maintain best arrival label {stop id: pandas.datetime}.
        inf_time (pandas.datetime): Variable indicating infinite time (pandas.datetime).

    Examples:
        >>> output = initialize_raptor(routes_by_stop_dict, 20775, 4)
    '''
    #inf_time = pd.to_datetime("today").round(freq='H') + pd.to_timedelta("365 day")
    inf_time = 200000
    roundsCount = MAX_TRANSFER + 1
    pi_label = {x: {stop: -1 for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    label = {x: {stop: inf_time for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    star_label = {stop: inf_time for stop in routes_by_stop_dict.keys()}

    marked_stop = deque()
    marked_stop_dict = {stop: 0 for stop in routes_by_stop_dict.keys()}
    marked_stop.append(SOURCE)
    marked_stop_dict[SOURCE] = 1
    return marked_stop, marked_stop_dict, label, pi_label, star_label


def get_latest_trip_new(stoptimes_dict: dict, route: int, arrival_time_at_pi, pi_index: int, change_time, max_waiting_time) -> tuple:
    '''
    Get latest trip after a certain timestamp from the given stop of a route.

    Args:
        stoptimes_dict (dict): preprocessed dict. Format {route_id: [[trip_1], [trip_2]]}.
        route (int): id of route.
        arrival_time_at_pi (pandas.datetime): arrival time at stop pi.
        pi_index (int): index of the stop from which route was boarded.
        change_time (pandas.datetime): change time at stop (set to 0).

    Returns:
        If a trip exists:
            trip index, trip
        else:
            -1,-1   (e.g. when there is no trip after the given timestamp)

    Examples:
        >>> output = get_latest_trip_new(stoptimes_dict, 1000, pd.to_datetime('2019-06-10 17:40:00'), 0, pd.to_timedelta(0, unit='seconds'))
    '''
    
    for trip_idx, trip in (stoptimes_dict[route].items()): 
            
            # ! this error occurs due to the removal of stop_times > 23:59 !
            """
            try:
                t1 = trip[pi_index-1][1] 
            except IndexError:
            
                return -1, -1  
            """
            
            try:
                t1 = trip[pi_index-1][1] 
            except IndexError:
            
                continue
                

            if t1 == 0:
                continue
           

            if (t1 >= arrival_time_at_pi + change_time) and (t1 <= arrival_time_at_pi + max_waiting_time) :  
                
                return f'{route}_{trip_idx}', stoptimes_dict[route][trip_idx]
    return -1, -1  # No trip is found after arrival_time_at_pi
    
    # No trip exsist for this route. in this case check tripid from trip file for this route and then look waybill.ID. 
    # Likely that trip is across days thats why it is rejected in stoptimes builder while checking



def post_processing (DESTINATION: int, pi_label, MIN_TRANSFER, MaxWalkDist, timetable_mode, Maximal_travel_time, D_Time, mode_raptor, departure_interval) -> tuple:
    '''
    Post processing for std_RAPTOR. Currently supported functionality:
        1. Rounds in which DESTINATION is reached
        2. Trips for covering pareto optimal set
        3. Pareto optimal timestamps.

    Args:
        DESTINATION (int): stop id of destination stop.
        pi_label (dict): Nested dict used for backtracking. Primary keys: Round, Secondary keys: stop id. Format- {round : {stop_id: pointer_label}}
        
        label (dict): nested dict to maintain label. Format {round : {stop_id: pandas.datetime}}.

    Returns:
        rounds_inwhich_desti_reached (list): list of rounds in which DESTINATION is reached. Format - [int]
        trip_set (list): list of trips ids required to cover optimal journeys. Format - [char]
        rap_out (list): list of pareto-optimal arrival timestamps. Format = [(pandas.datetime)]

    Examples:
        >>> output = post_processing(1482, pi_label, 1, label)
    '''
    # раунды, в которых  достигнута цель
    # rounds in which the destination is achieved 

    i = 0    
    rounds_inwhich_desti_reached = [x for x in pi_label.keys() if DESTINATION in pi_label[x] and pi_label[x][DESTINATION] != -1]

       

    pareto_set = []
    valid_result=True
    if rounds_inwhich_desti_reached == []:
        valid_result = False 

    #if len(rounds_inwhich_desti_reached) <= MIN_TRANSFER + 1:
    #   valid_result  =False
       

    if not valid_result:
        return None, None, None,None
    else:
        rounds_inwhich_desti_reached.reverse()
        
        
        last_mode = ""
        trip_set = []
        
        for k in rounds_inwhich_desti_reached:
            transfer_needed = k - 1

            # null transfers:
            # 1) foot path
            # 2) foot path + route
            # 2) foot path + route + foot path
            if transfer_needed == -1:
                transfer_needed = 0
            
            journey = []
            stop = DESTINATION 
            
            walking_stops= []          
            
            
            while pi_label[k][stop] != -1:
                
                journey.append(pi_label[k][stop])
               
                mode = pi_label[k][stop][0]
                if mode == 'walking':
                    if last_mode == "":
                      last_mode = 'walking'
                    
                    """
                    These new checkings were added to process a case when 2 adjacent stops
                    are such that walking is from one to the other so we get infinite loop
                    """
                    if walking_stops != [] : #previous step was also walking
                
                        if stop in walking_stops:
                            #k = k - 1  
                            walking_stops = []
                            # changed 06.05.2024!!!
                            journey = []
                            break
                            # changed 06.05.2024!!!
                        else:
                            walking_stops.append(stop) 
                            stop = pi_label[k][stop][1]               
                    else:                          
                         walking_stops.append(stop) 
                         stop = pi_label[k][stop][1]                                        
                else: 
                    last_mode = ""
                                  
                    trip_set.append(pi_label[k][stop][-1])
                    stop = pi_label[k][stop][1]
                    k = k - 1

                
                if k < 0 or (not  pi_label[k].get(stop)): # Igor changed
                    break   

            journey.reverse()
            append = True                            

            if timetable_mode:
                                
                if len (journey) > 1 and journey[0][0] == "walking" and journey[1][0] != "walking":
                   
                    #new_value = D_Time + journey[0][3] + departure_interval
                    if mode_raptor == 1:
                        new_value = journey[1][0] - departure_interval
                    else:
                        #### it is TESTING
                        new_value = journey[1][0] + departure_interval
                        #new_value = journey[1][0]
                        
                    journey[0] = (journey[0][0], journey[0][1], journey[0][2], journey[0][3], new_value)

            
                duration, start_time, end_time = get_duration_for_timetable_mode (journey, mode_raptor)
                
                if mode_raptor == 1:
                    if (duration > Maximal_travel_time) or start_time < D_Time:
                       append = False 
                
                if mode_raptor == 2:
                    if (duration > Maximal_travel_time) or end_time > D_Time - 300:
                        append = False 
                            
            
            if len(journey) > 0 and not (journey[-1][0] == 'walking' and journey[-1][3] > MaxWalkDist) and (transfer_needed + 1 >= MIN_TRANSFER):    
                if append:
                    pareto_set.append((transfer_needed, journey))
        

        if len(pareto_set) == 0:
          return None, None, None,None
        
        return pareto_set

  
def get_duration_for_timetable_mode (journey, mode_raptor):
    duration = 0
    start_time = 0
    end_time = 0
    
    if mode_raptor == 1:
                
                if len (journey) == 1 and journey[0][0] == "walking":
                    duration = journey[0][3]
                    start_time = journey[0][4]-journey[0][3] 
                    end_time = journey[0][4]
                    return duration, start_time, end_time

                if len (journey) > 1:
                    if journey[0][0] == "walking":
                        start_time = journey[0][4] - journey[0][3] 
                    else:
                        start_time = journey[0][0]

                    if journey[-1][0] == "walking":
                        end_time = journey[-1][4]
                    else:
                        end_time = journey[-1][3]

    if mode_raptor == 2:
                
                if len (journey) == 1 and journey[0][0] == "walking":
                    duration = journey[0][3]
                    start_time = journey[0][4] + journey[0][3] 
                    end_time = journey[0][4]
                    return duration, start_time, end_time

                if len (journey) > 1:
                    if journey[0][0] == "walking":
                        end_time = journey[0][4] + journey[0][3] 
                    else:
                        end_time = journey[0][3]

                    if journey[-1][0] == "walking":
                        start_time = journey[-1][4]  
                    else:
                        start_time = journey[-1][3]

    duration = end_time - start_time
                    
                               
    return duration, start_time, end_time
    

def post_processingAll(call_name, SOURCE, D_TIME, label, pi_label, MIN_TRANSFER, MaxWalkDist, timetable_mode, Maximal_travel_time, departure_interval, mode) -> tuple:
   newDict = dict()   
   stops = label[0].keys()
      
   begin_time = D_TIME
   
   count_not_accessible = 0

   #len_pareto_set = 0
   #count_stops = 0 
   for p_i in stops:
            QApplication.processEvents()
            if SOURCE == p_i:
               continue        
            pareto_set = post_processing (p_i, pi_label, MIN_TRANSFER, MaxWalkDist, timetable_mode, Maximal_travel_time, D_TIME, mode, departure_interval)           
            
            total_time_to_dest = -1           
                        
            if pareto_set != (None, None, None, None) and len(pareto_set) > 0:
             #Just one journey with minimal time will be in pareto set
             if call_name == "raptor":
              optimal_pair = get_optimal_journey(pareto_set, 1)
             else:
              optimal_pair = get_optimal_journey(pareto_set, 2) 
             pareto_set = [optimal_pair]
            
             journey = pareto_set[0][1]

             if call_name == "raptor":
                total_time_to_dest, _, _ = get_duration_for_timetable_mode (journey, 1)
             else:
                total_time_to_dest, _, _ = get_duration_for_timetable_mode (journey, 2)
                
            else:
             count_not_accessible = count_not_accessible + 1
            
            newDict[p_i] = [SOURCE, begin_time, total_time_to_dest, pareto_set ]   
        
   #print (f' avg len_pareto {len_pareto_set/count_stops}')
   reachedLabels = newDict
   return  reachedLabels
      
def get_optimal_journey(pareto_set, raptor_mode):
   
   res = []
   
   id = 0   
   for transfers, journey in pareto_set:
        duration , _, _ = get_duration_for_timetable_mode (journey, raptor_mode)    
        res.append((id, transfers, duration))
        id = id + 1
   
   # Перебор всех элементов в массиве
   min_duration = float('inf')
   min_count_leg = float('inf')
   min_element = None
   for (id, count_leg, duration) in res:
        if duration < min_duration:
            min_duration = duration
            min_count_leg = count_leg
            min_element = id
        # Если duration равен минимальному, проверить count_leg
        elif duration == min_duration:
            if count_leg < min_count_leg:
                min_count_leg = count_leg
                min_element = id

   #transfers, journey = pareto_set[min_element - 1]
   transfers, journey = pareto_set[min_element]  #????????
   result = (transfers, journey) 
   return result
   
                     

def initialize_rev_raptor(routes_by_stop_dict: dict, SOURCE: int, MAX_TRANSFER: int) -> tuple:
    '''
    Initialize values for RAPTOR.

    Args:
        routes_by_stop_dict (dict): preprocessed dict. Format {stop_id: [id of routes passing through stop]}.
        SOURCE (int): stop id of source stop.
        MAX_TRANSFER (int): maximum transfer limit.

    Returns:
        marked_stop (deque): deque to store marked stop.
        marked_stop_dict (dict): Binary variable indicating if a stop is marked. Keys: stop Id, value: 0 or 1.
        label (dict): nested dict to maintain label. Format {round : {stop_id: pandas.datetime}}.
        pi_label (dict): Nested dict used for backtracking labels. Format {round : {stop_id: pointer_label}}
        if stop is reached by walking, pointer_label= ('walking', from stop id, to stop id, time, arrival time)}} else pointer_label= (trip boarding time, boarding_point, stop id, arr_by_trip, trip id)
        star_label (dict): dict to maintain best arrival label {stop id: pandas.datetime}.
        inf_time (pandas.datetime): Variable indicating infinite time (pandas.datetime).

    Examples:
        >>> output = initialize_raptor(routes_by_stop_dict, 20775, 4)
    '''
    #inf_time = pd.to_datetime("today").round(freq='H') - pd.to_timedelta("730 day")
    #    inf_time = pd.to_datetime('2022-01-15 19:00:00')
    inf_time = -1
    roundsCount = MAX_TRANSFER+1
    pi_label = {x: {stop: -1 for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    label = {x: {stop: inf_time for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    star_label = {stop: inf_time for stop in routes_by_stop_dict.keys()}

    marked_stop = deque()
    marked_stop_dict = {stop: 0 for stop in routes_by_stop_dict.keys()}
    marked_stop.append(SOURCE)
    marked_stop_dict[SOURCE] = 1
    return marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time

def get_earliest_trip_new(stoptimes_dict: dict, route: int, arrival_time_at_pi, pi_index: int, change_time, max_waiting_time) -> tuple:

    '''
    Get earliest trip after a certain timestamp from the given stop of a route.

    Args:
        stoptimes_dict (dict): preprocessed dict. Format {route_id: [[trip_1], [trip_2]]}.
        route (int): id of route.
        arrival_time_at_pi (pandas.datetime): arrival time at stop pi.
        pi_index (int): index of the stop from which route was boarded.
        change_time (pandas.datetime): change time at stop (set to 0).
        current_trip_t: distinguish 2 cases: current_trip_t=-1, i.e. not defined
         or current_trip_t!=-1 , that is exists but no accepatable
    Returns:
        If a trip exists:
            trip index, trip
        else:
            -1,-1   (e.g. when there is no trip after the given timestamp)

    Examples:
        >>> output = get_earliest_trip_new(stoptimes_dict, 1000, pd.to_datetime('2019-06-10 17:40:00'), 0, pd.to_timedelta(0, unit='seconds'))
    '''
    
        
    for trip_idx, trip in (stoptimes_dict[route].items()):
        
        # ! this error occurs due to the removal of stop_times > 23:59 !
        try:
            t1 = trip[pi_index-1][1] 
        except IndexError:
            continue
            #return -1, -1 
                        
        if (t1  <= arrival_time_at_pi - change_time)   and (t1 >= arrival_time_at_pi - max_waiting_time) :
                       
            return f'{route}_{trip_idx}', stoptimes_dict[route][trip_idx]


    return -1, -1  # No trip is found after arrival_time_at_pi

     