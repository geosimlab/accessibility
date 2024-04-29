"""
Module contains function related to RAPTOR, rRAPTOR, One-To-Many rRAPTOR, HypRAPTOR
"""
from collections import deque as deque

#import pandas as pd
#from datetime import timedelta
from PyQt5.QtWidgets import QApplication

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
    return marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time


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
    
    #max_waiting_time = timedelta(seconds = max_wait_time)
    #change_time = timedelta(days=change_time.days, seconds=change_time.seconds)
    
    for trip_idx, trip in (stoptimes_dict[route].items()): 
            
            
            # ! this error occurs due to the removal of stop_times > 23:59 !
            try:
                t1 = trip[pi_index-1][1] 
            except IndexError:
                return -1, -1  
            
            if t1 == 0:
                continue
            
            
            if (t1 >= arrival_time_at_pi + change_time) and (t1 <= arrival_time_at_pi + max_waiting_time) :   
                return f'{route}_{trip_idx}', stoptimes_dict[route][trip_idx]
    return -1, -1  # No trip is found after arrival_time_at_pi
    
    # No trip exsist for this route. in this case check tripid from trip file for this route and then look waybill.ID. 
    # Likely that trip is across days thats why it is rejected in stoptimes builder while checking



def post_processing (DESTINATION: int, pi_label, MIN_TRANSFER, MaxWalkDist) -> tuple:
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

        print (f'rounds_inwhich_desti_reached {rounds_inwhich_desti_reached}')        
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
                          k = k - 1  
                          walking_stops = []
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
            
            print (f'journey {journey}')
            #print (f'journey[-1][3] {journey[-1][3]}')
            #print (f'MaxWalkDist {MaxWalkDist}')
            #print (f'transfer_needed {transfer_needed}')
            #print (f'MIN_TRANSFER {MIN_TRANSFER}')

            
            #if len(journey) > 0 and not (journey[-1][0] == 'walking' and journey[-1][3].total_seconds() > MaxWalkDist) and (transfer_needed >= MIN_TRANSFER):
            if len(journey) > 0 and not (journey[-1][0] == 'walking' and journey[-1][3] > MaxWalkDist) and (transfer_needed+1 >= MIN_TRANSFER):    
                pareto_set.append((transfer_needed, journey))
        
        if len(pareto_set) == 0:
          return None, None, None,None
        return pareto_set

  


def post_processingAll(call_name, SOURCE, D_TIME, label, pi_label, MIN_TRANSFER, MaxWalkDist) -> tuple:
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
            pareto_set = post_processing (p_i, pi_label, MIN_TRANSFER, MaxWalkDist)           
            

            total_time_to_dest = -1           
            total_walk_time = -1
            total_waiting_time = -1 
            total_boarding_count = -1
            total_drive_time = -1
            
            
            print (f'pareto_set {pareto_set}')
            
            if pareto_set != (None, None, None, None) and len(pareto_set) > 0:
             #Just one journey with minimal time will be in pareto set
             if call_name == "raptor":
              optimal_pair = get_optimal_journey(pareto_set)
             else:
              optimal_pair = get_rev_optimal_journey(pareto_set) 
             pareto_set = [optimal_pair]
            
             journey = pareto_set[0][1]
             if call_name == "raptor":
              total_time_to_dest,total_walk_time,total_waiting_time,total_boarding_count,total_drive_time=\
                post_processing_2(D_TIME, journey)
             else:
                total_time_to_dest,total_walk_time,total_waiting_time,total_boarding_count,total_drive_time=\
                revpost_processing_2(D_TIME, journey)
            else:
             count_not_accessible = count_not_accessible + 1
            
            newDict[p_i] = \
            [SOURCE, begin_time, total_time_to_dest, total_walk_time, total_waiting_time,
             total_boarding_count, total_drive_time, pareto_set ]   
        
   #print (f' avg len_pareto {len_pareto_set/count_stops}')
   reachedLabels = newDict
   return  reachedLabels




def get_optimal_journey(pareto_set):
   result = None
   res = {}
   item_in_pareto_set = 0
   
   for transfers, journey in pareto_set:
        item_in_pareto_set = item_in_pareto_set + 1
        count_leg = 0
        time_finish = ""

        for leg in journey:
            count_leg = count_leg + 1
            if leg[0] == 'walking':
               #current_arrive_time = leg[4].time()                
               current_arrive_time = leg[4]
            else:
               #current_arrive_time = leg[3].time()
               current_arrive_time = leg[3]
            time_finish = current_arrive_time

        res[item_in_pareto_set] = []
        res[item_in_pareto_set].append((count_leg, time_finish))
                        

   # найти в res такой item_in_pareto_set у которого time_finish минимальный, 
   # если минимальных несколько то тот у которого меньше count_leg
   # find in res an item_in_pareto_set whose time_finish is minimal, 
   # if there are several minimal ones, then the one with less count_leg 
               
   min_item = min(res, key=lambda x: (res[x][0][1], res[x][0][0]))
   transfers, journey = pareto_set[min_item - 1]
   result = (transfers, journey)
   
   return result  
      
def get_rev_optimal_journey(pareto_set):
   result = None
   res = {}
   item_in_pareto_set = 0

   
   
   for transfers, journey in pareto_set:
        item_in_pareto_set = item_in_pareto_set + 1
        count_leg = 0
        time_finish = ""

        
        for leg in journey:
            count_leg = count_leg + 1
            if leg[0] == 'walking':
               #current_arrive_time = leg[4].time()                
               current_arrive_time = leg[4]
            else:
               #current_arrive_time = leg[3].time()
               current_arrive_time = leg[3]
            time_finish = current_arrive_time

        res[item_in_pareto_set] = []
        res[item_in_pareto_set].append((count_leg, time_finish))
   

   # найти в res такой item_in_pareto_set у которого time_start max, 
   # если max несколько то тот у которого меньше count_leg
   # find in res an item_in_pareto_set whose time_start is max, 
   # if there are several minimal ones, then the one with less count_leg
   
   item = max(res, key=lambda x: (res[x][0][1], -x))
   transfers, journey = pareto_set[item - 1]
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
    
    
    #max_waiting_time = timedelta(seconds = max_wait_time)
    #change_time = timedelta(days=change_time.days, seconds=change_time.seconds)
        
    for trip_idx, trip in (stoptimes_dict[route].items()):

        # ! this error occurs due to the removal of stop_times > 23:59 !
        try:
            t1 = trip[pi_index-1][1] 
        except IndexError:
     
            return -1, -1 
                        
        if (t1  <= arrival_time_at_pi - change_time)   and (t1 >= arrival_time_at_pi - max_waiting_time) :
                       
            return f'{route}_{trip_idx}', stoptimes_dict[route][trip_idx]


    return -1, -1  # No trip is found after arrival_time_at_pi
    

"""
This function designed for getting raptor statistics as it is described in Return parameters
It is called after function post_processing that returns a jorney array that is input parameter 
for this function. It is supposed that SOURCE and DESTINATION were given
"""
def post_processing_2(D_TIME, journey) -> tuple:
    """
     Returns:
        Origin STOP_ID, START time, Destination STOP_ID, TOTAL JOURNEY time TO destination,
          TOTAL WALK TIME (INCLUDING WAK TO THE STOP OF THE FIRST BOARDING 
          AND WALK TO DESTINATION FORM THE LAST ALIGHTING STOP), 
          TOTAL Waiting time AT STOPS, TOTAL Number of BOARDINGS (IS 0 IF REACHED BY WALK ONLY)
    """ 
    
    total_time_to_dest = 0 
    total_walk_time = 0
    total_waiting_time = 0
    total_boarding_count = 0
    total_drive_time = 0           
    first_leg_found = False
    last_arrive_time = 0
    
    for leg in journey:       
             if leg[0] == 'walking':
               #total_walk_time = total_walk_time + leg[3].total_seconds() 
               total_walk_time = total_walk_time + leg[3]
               last_arrive_time = leg[4]     
               if not first_leg_found:
                    first_leg_found = True        
             else:               
               total_boarding_count = total_boarding_count + 1
               #total_drive_time = total_drive_time + (leg[3] - leg[0]).total_seconds()
               total_drive_time = total_drive_time + (leg[3] - leg[0])
               
               if  first_leg_found:  #distract from boarding time previous arrive time
                  if last_arrive_time != 0:
                        #total_waiting_time = total_waiting_time + (leg[0] - last_arrive_time).total_seconds() 
                        total_waiting_time = total_waiting_time + (leg[0] - last_arrive_time)
               else:
                  #total_waiting_time = (leg[0] - D_TIME).total_seconds()  
                  total_waiting_time = (leg[0] - D_TIME)
                  first_leg_found = True                  
               last_arrive_time = leg[3]
            
    total_time_to_dest = total_walk_time + total_waiting_time + total_drive_time

    return total_time_to_dest,total_walk_time,total_waiting_time,total_boarding_count,total_drive_time 

def revpost_processing_2(D_TIME, journey) -> tuple:
    """
     Returns:
        Origin STOP_ID, START time, Destination STOP_ID, TOTAL JOURNEY time TO destination,
          TOTAL WALK TIME (INCLUDING WAK TO THE STOP OF THE FIRST BOARDING 
          AND WALK TO DESTINATION FORM THE LAST ALIGHTING STOP), 
          TOTAL Waiting time AT STOPS, TOTAL Number of BOARDINGS (IS 0 IF REACHED BY WALK ONLY)
    """ 
    
    total_time_to_dest = 0 
    total_walk_time = 0
    total_waiting_time = 0
    total_boarding_count = 0
    total_drive_time = 0           
    first_leg_found = False
    last_arrive_time = 0
        
    for leg in journey:       
             if leg[0] == 'walking':
               #total_walk_time = total_walk_time + leg[3].total_seconds() 
               total_walk_time = total_walk_time + leg[3]
               last_arrive_time = leg[4]
               if not first_leg_found:
                    first_leg_found = True        
             else:               
               total_boarding_count = total_boarding_count + 1
               #total_drive_time = total_drive_time - (leg[3] - leg[0]).total_seconds()
               total_drive_time = total_drive_time - (leg[3] - leg[0])
               

               if  first_leg_found:  #distract from boarding time previous arrive time
                  if last_arrive_time != 0:
                   #total_waiting_time = total_waiting_time - (leg[0] - last_arrive_time).total_seconds() 
                   total_waiting_time = total_waiting_time - (leg[0] - last_arrive_time)
               else:
                  #total_waiting_time = - (leg[0] - D_TIME).total_seconds()  
                  total_waiting_time = - (leg[0] - D_TIME)
                  first_leg_found = True                  
               last_arrive_time = leg[3]

    
    total_time_to_dest = total_walk_time + total_waiting_time + total_drive_time
    

    return total_time_to_dest, total_walk_time, total_waiting_time, total_boarding_count, total_drive_time 

     