"""
Module contains function related to RAPTOR, rRAPTOR, One-To-Many rRAPTOR, HypRAPTOR
"""
from collections import deque as deque


def seconds_to_time(total_seconds):
    total_seconds = round(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    return time_str

def initialize_raptor(routes_by_stop_dict, 
                      SOURCE,                      
                      MAX_TRANSFER) -> tuple:
    
        
    inf_time = 200000
    roundsCount = MAX_TRANSFER + 1
    """
    pi_label = {x: {int(stop): -1 for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    label = {x: {int(stop): inf_time for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    
    """

    routes = list(routes_by_stop_dict.keys())
    pi_label = {x: {int(stop): -1 for stop in routes} for x in range(0, roundsCount + 1)}
    label = {x: {int(stop): inf_time for stop in routes} for x in range(0, roundsCount + 1)}
    

    marked_stop = deque()
    marked_stop_dict = {int(stop): 0 for stop in routes_by_stop_dict.keys()}
    marked_stop.append(SOURCE)
    marked_stop_dict[SOURCE] = 1
    
    return marked_stop, marked_stop_dict, label, pi_label


def get_latest_trip_new(stoptimes_dict, 
                        route, 
                        arrival_time_at_pi, 
                        pi_index, 
                        change_time, 
                        max_waiting_time) -> tuple:
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
    t2 = arrival_time_at_pi + change_time
    t3 = arrival_time_at_pi + max_waiting_time

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
           

            if (t1 >= t2) and (t1 <= t3) :  
                
                return f'{route}_{trip_idx}', stoptimes_dict[route][trip_idx]
    return -1, -1  # No trip is found after arrival_time_at_pi
    
    # No trip exsist for this route. in this case check tripid from trip file for this route and then look waybill.ID. 
    # Likely that trip is across days thats why it is rejected in stoptimes builder while checking



def post_processing (DESTINATION,
                     pi_label, 
                     MIN_TRANSFER, 
                     MaxWalkDist, 
                     timetable_mode, 
                     Maximal_travel_time, 
                     D_Time, 
                     mode_raptor, 
                     departure_interval) -> tuple:
   
    # раунды, в которых  достигнута цель
    # rounds in which the destination is achieved 

    rounds_inwhich_desti_reached = [x for x in pi_label.keys() if DESTINATION in pi_label[x] and pi_label[x][DESTINATION] != -1]

    pareto_set = []
    
    if not rounds_inwhich_desti_reached:
        return None
      

    
    rounds_inwhich_desti_reached.reverse()
        
        
    last_mode = ""
            
    for k in rounds_inwhich_desti_reached:
            transfer_needed = k - 1

            # null transfers:
            # 1) footpath
            # 2) footpath + route
            # 2) footpath + route + footpath
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
                        
                    journey[0] = (journey[0][0], 
                                  journey[0][1], 
                                  journey[0][2], 
                                  journey[0][3], 
                                  new_value)

            
                duration, start_time, end_time = get_duration_for_timetable_mode (journey, mode_raptor)
                
                if mode_raptor == 1:
                    if (duration > Maximal_travel_time) or start_time < D_Time:
                       append = False 
                
                if mode_raptor == 2:
                    if (duration > Maximal_travel_time) or end_time > D_Time - departure_interval:
                        append = False 
                            
            
            if len(journey) > 0 and not (journey[-1][0] == 'walking' and journey[-1][3] > MaxWalkDist) and (transfer_needed + 1 >= MIN_TRANSFER):    
                if append:
                    pareto_set.append((transfer_needed, journey))
        
        
    if len(pareto_set) == 0:
          return None
        
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
    

def post_processingAll(call_name, 
                       SOURCE, 
                       D_TIME, 
                       label, 
                       list_stops,
                       pi_label, 
                       MIN_TRANSFER, 
                       MaxWalkDist, 
                       timetable_mode, 
                       Maximal_travel_time, 
                       departure_interval, 
                       mode) -> tuple:
   newDict = dict()   
      
   for p_i in list_stops:
               
            if SOURCE == p_i:
               continue        
            pareto_set = post_processing (p_i, 
                                          pi_label, 
                                          MIN_TRANSFER, 
                                          MaxWalkDist, 
                                          timetable_mode, 
                                          Maximal_travel_time, 
                                          D_TIME, mode, 
                                          departure_interval)           
            
            if pareto_set == None:
                continue
            
            total_time_to_dest = -1           
                        
            if pareto_set != None and len(pareto_set) > 0:
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
            
            newDict[p_i] = [SOURCE, D_TIME, total_time_to_dest, pareto_set ]   
   
   return  newDict
      
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
   
                     

def initialize_rev_raptor(routes_by_stop_dict, 
                          SOURCE, 
                          MAX_TRANSFER) -> tuple:
        
    
    inf_time = -1
    roundsCount = MAX_TRANSFER + 1
    routes = list(routes_by_stop_dict.keys())
    pi_label = {x: {int(stop): -1 for stop in routes} for x in range(0, roundsCount + 1)}
    label = {x: {int(stop): inf_time for stop in routes} for x in range(0, roundsCount + 1)}
    
    """
    pi_label = {x: {int(stop): -1 for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    label = {x: {int(stop): inf_time for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    
    """

    marked_stop = deque()
    marked_stop_dict = {int(stop): 0 for stop in routes}
    marked_stop.append(SOURCE)
    marked_stop_dict[SOURCE] = 1
    return marked_stop, marked_stop_dict, label, pi_label, inf_time

def get_earliest_trip_new(stoptimes_dict, 
                          route, 
                          arrival_time_at_pi, 
                          pi_index, 
                          change_time, 
                          max_waiting_time) -> tuple:

        
    t2 = arrival_time_at_pi - change_time
    t3 = arrival_time_at_pi - max_waiting_time    
    for trip_idx, trip in (stoptimes_dict[route].items()):
        
        # ! this error occurs due to the removal of stop_times > 23:59 !
        try:
            t1 = trip[pi_index-1][1] 
        except IndexError:
            continue
            #return -1, -1 
                        
        if (t1  <= t2)   and (t1 >= t3) :
                       
            return f'{route}_{trip_idx}', stoptimes_dict[route][trip_idx]


    return -1, -1  # No trip is found after arrival_time_at_pi

     