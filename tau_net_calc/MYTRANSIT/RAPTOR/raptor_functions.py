"""
Module contains function related to RAPTOR, rRAPTOR, One-To-Many rRAPTOR, HypRAPTOR
"""
from collections import deque as deque

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import math
from datetime import datetime, timedelta

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
    inf_time = pd.to_datetime("today").round(freq='H') + pd.to_timedelta("365 day")
    #    inf_time = pd.to_datetime('2022-01-15 19:00:00')
    roundsCount = MAX_TRANSFER + 1
    pi_label = {x: {stop: -1 for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    label = {x: {stop: inf_time for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    star_label = {stop: inf_time for stop in routes_by_stop_dict.keys()}

    marked_stop = deque()
    marked_stop_dict = {stop: 0 for stop in routes_by_stop_dict.keys()}
    marked_stop.append(SOURCE)
    marked_stop_dict[SOURCE] = 1
    return marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time


def check_stop_validity(stops, SOURCE: int, DESTINATION: int) -> None:
    '''
    Check if the entered SOURCE and DESTINATION stop id are present in stop list or not.

    Args:
        stops: GTFS stops.txt
        SOURCE (int): stop id of source stop.
        DESTINATION (int): stop id of destination stop.

    Returns:
        None

    Examples:
        >>> output = check_stop_validity(stops, 20775, 1482)
    '''
    if SOURCE in stops.stop_id and DESTINATION in stops.stop_id:
        print('correct inputs')
    else:
        print("incorrect inputs")
    return None


def get_latest_trip_new(stoptimes_dict: dict, route: int, arrival_time_at_pi, pi_index: int, change_time, max_wait_time, k) -> tuple:
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
    
    max_waiting_time = timedelta(seconds = max_wait_time)
    change_time = timedelta(days=change_time.days, seconds=change_time.seconds)
    if k == 1:
        change_time = pd.to_timedelta(0, unit='seconds')
    
    
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



def post_processing (DESTINATION: int, pi_label, 
                    label, MAX_TRANSFER, ExactTransfersCount, MaxWalkDist2, MaxWalkDist) -> tuple:
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
    # destination = label[0].keys() - all start stop
    # pi_label.keys dict_keys([0, 1, 2, 3, 4])
    # rounds_inwhich_desti_reached [] 
    
    rounds_inwhich_desti_reached = [x for x in pi_label.keys() if DESTINATION in pi_label[x] and pi_label[x][DESTINATION] != -1]

    #print (f'rounds_inwhich_desti_reached {rounds_inwhich_desti_reached()}')
    #print (f'DESTINATION {DESTINATION}')
    #print (f'pi_label[0][DESTINATION] {pi_label[0][DESTINATION]}')
    #print (f'pi_label[1][DESTINATION] {pi_label[1][DESTINATION]}')
    #print (f'pi_label[2][DESTINATION] {pi_label[2][DESTINATION]}')
    

    pareto_set = []
    valid_result=True
    if rounds_inwhich_desti_reached == []:
       #print ('valid_result false1')
       valid_result=False 
    if ExactTransfersCount == 1 and len(rounds_inwhich_desti_reached) != MAX_TRANSFER + 1:
       valid_result=False
       #print ('valid_result false2')  

    if not valid_result:
        return None, None, None,None
    else:
        rounds_inwhich_desti_reached.reverse()
        #if DESTINATION == 171388377:
            #print (f'rounds_inwhich_desti_reached = {rounds_inwhich_desti_reached}')
        
        last_mode = ""
        trip_set = []
        rap_out = [label[k][DESTINATION] for k in rounds_inwhich_desti_reached]
        
        for k in rounds_inwhich_desti_reached:
            transfer_needed = k - 1
            if ExactTransfersCount == 1 and transfer_needed != MAX_TRANSFER:
               continue
            journey = []
            stop = DESTINATION 
            adjacent_walks_time_counter = 0
            walking_stops=[]          
            
            
            while pi_label[k][stop] != -1:

               
                journey.append(pi_label[k][stop])
                """
                if len(journey) > 10:
                  print(f'post_processing len(journey)= {len(journey)}, DESTINATION= {DESTINATION}')
                  return None, None, None,None 
                """  
                mode = pi_label[k][stop][0]
                if mode == 'walking':
                    if last_mode == "":
                      last_mode = 'walking'
                    #adjacent_walks_time_counter = adjacent_walks_time_counter + pi_label[k][stop][3].total_seconds()                        
                    #if adjacent_walks_time_counter > MaxWalkDist2:
                    #   return None, None, None,None
                    """
                    These new checkings were added to process a case when 2 adjacent stops
                    are such that walking is from one to the other so we get infinite loop
                    """
                    if walking_stops != [] : #previous step was also walking
                       #print("k="+str(k)+", stop"+str(stop))
                       if stop in walking_stops:
                          k = k - 1  
                          #print(f'stop in  walking_stops: {stop}')
                          walking_stops = []
                       else:
                         walking_stops.append(stop) 
                         stop = pi_label[k][stop][1]               
                    else:                          
                         walking_stops.append(stop) 
                         stop = pi_label[k][stop][1]                                        
                else: 
                    last_mode = ""
                    adjacent_walks_time_counter = 0                 
                    trip_set.append(pi_label[k][stop][-1])
                    stop = pi_label[k][stop][1]
                    k = k - 1

                #print (f'k {k} stop {stop}')
                if k < 0 or (not  pi_label[k].get(stop)): # Igor changed
                   #print(f'pi_label[k].get(stop) is not found for stop= {stop} , k= {k}') 
                   break   

            journey.reverse()
            
            
            if len(journey) > 0 and not (journey[-1][0] == 'walking' and journey[-1][3].total_seconds() > MaxWalkDist) :
            
                """
                last_leg_walk = False
                double_leg = False
                for leg in journey:
                    if leg[0] == 'walking':
                        if last_leg_walk == True:
                            double_leg = True
                            break
                        else:
                            last_leg_walk = False
                        last_leg_walk = True
                    if leg[0] != 'walking':
                        last_leg_walk = False
                   
                if not double_leg:
                """
                pareto_set.append((transfer_needed, journey))
        
        if len(pareto_set) == 0:
          return None, None, None,None
        return pareto_set

def check_adjacent_walk_time(pi_label, k, stop, WALKING_LIMIT):
    result=True
    adjacent_walks_time_counter=0
    last_mode=""
    while pi_label[k][stop] != -1:
      mode = pi_label[k][stop][0]
      if mode == 'walking':
       if last_mode=="":
         last_mode= 'walking'
       adjacent_walks_time_counter = adjacent_walks_time_counter+ pi_label[k][stop][3].total_seconds()                         
       if adjacent_walks_time_counter>WALKING_LIMIT.seconds:
         result=False
         break
      else:
        last_mode=""
        adjacent_walks_time_counter=0  
        stop = pi_label[k][stop][1]
        k = k - 1  
    return result     

#My function
#DEST is some stop for which exist path pi_label
# For fixed k run on pi_label[k][stop]. The last value pi_label[k][stop]
# is beginng time to reach DEST
"""
This is my recursive function that finds the first boarding time for given stop DEST
It is not used
"""
def getBeginTimeForStop(DEST: int, pi_label: dict,k):  
   
 #firstly define minimal m such that pi_label[m][stop]!=-1
  stop = DEST  
  m=k  
  result=-1
  last_founded_index=-1
  while m>=0:
     if  pi_label[m][stop]!=-1: 
      last_founded_index=m
     m=m-1
  if last_founded_index>=0:
     mode = pi_label[last_founded_index][stop][0]  
     if mode=="walking" :
       if last_founded_index==0:
          result=pi_label[last_founded_index][stop][4] 
       else:
        #result=pi_label[last_founded_index][stop][4] #?     
        stop=pi_label[last_founded_index][stop][1] 
        result=  getBeginTimeForStop(stop, pi_label, last_founded_index)   
     else:
         result=pi_label[last_founded_index][stop][0]
  return result
                   

def _print_Journey_legs(pareto_journeys: list) -> None:
    '''
    Prints journey in correct format. Parent Function: post_processing

    Args:
        pareto_journeys (list): pareto optimal set.

    Returns:
        None

    Examples:
        >>> output = _print_Journey_legs(pareto_journeys)
    '''
    for _, journey in pareto_journeys:
        for leg in journey:
            if leg[0] == 'walking':
                print(f'from {leg[1]} walk till  {leg[2]} for {leg[3].total_seconds()} seconds and reach at {leg[4].time()} ')
                #print(f'from {leg[1]} walk till  {leg[2]} for {leg[3]} minutes and reach at {leg[4].time()}')
            else:
                print(
                    f'from {leg[1]} board at {leg[0].time()} and get down on {leg[2]} at {leg[3].time()} along {leg[-1]}')
        print("####################################")
    return None

"""
This procedure is called from raptor when its main file finished.The cycle worked a number of rounds
Input:
SOURCE
label: dictionary with key: number of round and for each key value is a dictionary
 where keys are all possible stops accesible from SOURCE and for each stop the value is 
 optimal time arriving to the stop
pi_label (dict): Nested dict used for backtracking. 
 Primary keys: Round, Secondary keys: stop id. Format- {round : {stop_id: pointer_label}} 
 That is for fixed round and stop_id pointer_label is stop_id of previous stop in a trip
 More precisely it has form (boarding_time, boarding_point, p_i, arr_by_t_at_pi, tid)
 where boarding_point is previous stop in a trip, boarding_time is departure time for boarding_point
 p_i - current stop(next to boarding_point),arr_by_t_at_pi - arrive time to p_i, tid - id of trip
Maximal_travel_time
inf_time: some big time
Output:
A dictionary where for eachh accessible for Maximal_travel_time stop will be added 
 an information about journeys to this stop
Algorithm:
 run over all possible stops
 for each stops run over all possible rounds k
 find the more earlier time when this stop was found in pi_label
 and define this time as beginning time for this stop
 Then end time (that is arriving time for this stop) get from current label[k]
 If end_time <= begin_time + Maximal_travel_time then define this stop as accessible
 and add it the dictionary of aaccessible stops.
 More precisely paas this stop as desination to method post_processing
 that returns particularly pareto_set of journeys finished by this stop 
 so add for this stop add to the dictionary [SOURCE,begin_time,end_time,pareto_set ]
"""


"""

"""
def post_processingAll(call_name, SOURCE,D_TIME, label, pi_label,MAX_TRANSFER, ExactTransfersCount, MaxWalkDist2, MaxWalkDist) -> tuple:
   newDict = dict()   
   stops = label[0].keys()
   #print (f' label[0].keys() {label[0].keys()}')
   
   begin_time = D_TIME
   
   count_not_accessible = 0

   #len_pareto_set = 0
   #count_stops = 0 
   for p_i in stops:
            if SOURCE == p_i:
               continue        
            pareto_set = post_processing (p_i, pi_label, label, MAX_TRANSFER, ExactTransfersCount, MaxWalkDist2, MaxWalkDist)           
            #print (f'pareto_set {pareto_set}')
            
            #len_pareto_set = len_pareto_set + len(pareto_set)
            #count_stops += 1

            total_time_to_dest = -1           
            total_walk_time = -1
            total_waiting_time = -1 
            total_boarding_count = -1
            total_drive_time = -1
            
            if p_i == 2148:
               print (f'p_i == 2148 pareto_set {pareto_set}')
            
            if pareto_set != (None, None, None, None) and len(pareto_set) > 0:
             #Just one journey with minimal time will be in pareto set
             if call_name == "raptor":
              optimal_pair = get_optimal_journey(pareto_set)
             else:
              optimal_pair = get_rev_optimal_journey(pareto_set) 
             pareto_set = [optimal_pair]
            #*************************
             

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
               current_arrive_time = leg[4].time()                
            else:
               current_arrive_time = leg[3].time()
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

        #print (f'journey {journey}')
        for leg in journey:
            count_leg = count_leg + 1
            if leg[0] == 'walking':
               current_arrive_time = leg[4].time()                
            else:
               current_arrive_time = leg[3].time()
            time_finish = current_arrive_time

        res[item_in_pareto_set] = []
        res[item_in_pareto_set].append((count_leg, time_finish))
   

   # найти в res такой item_in_pareto_set у которого time_start max, 
   # если max несколько то тот у которого меньше count_leg
   # find in res an item_in_pareto_set whose time_start is max, 
   # if there are several minimal ones, then the one with less count_leg
   #print (f'res {res}')
   #min_item = min(res, key=lambda x: (res[x][0][1], -res[x][0][0]))
   #item = max(res, key=lambda x: res[x][0][1])
   item = max(res, key=lambda x: (res[x][0][1], -x))
   transfers, journey = pareto_set[item - 1]
   result = (transfers, journey)
   
   return result  



   """
   result = None
   maximal_time = ""
   cycle = 0
   for transfers, journey in pareto_set:
        cycle += 1
        last_leg = journey[-1]        
        if last_leg[0] == 'walking':
            current_arrive_time = last_leg[4].time()                
        else:
            current_arrive_time = last_leg[3].time()
            
        if cycle == 1:
           maximal_time = current_arrive_time
           transfers_res = transfers
           journey_res = journey
        else:
            if current_arrive_time >  maximal_time:
                maximal_time = current_arrive_time
                transfers_res = transfers
                journey_res = journey

   result = (transfers_res, journey_res)
   return result   
   """
                      

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
    inf_time = pd.to_datetime("today").round(freq='H') - pd.to_timedelta("730 day")
    #    inf_time = pd.to_datetime('2022-01-15 19:00:00')
    roundsCount = MAX_TRANSFER+1
    pi_label = {x: {stop: -1 for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    label = {x: {stop: inf_time for stop in routes_by_stop_dict.keys()} for x in range(0, roundsCount + 1)}
    star_label = {stop: inf_time for stop in routes_by_stop_dict.keys()}

    marked_stop = deque()
    marked_stop_dict = {stop: 0 for stop in routes_by_stop_dict.keys()}
    marked_stop.append(SOURCE)
    marked_stop_dict[SOURCE] = 1
    return marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time

def get_earliest_trip_new(stoptimes_dict: dict, route: int, arrival_time_at_pi, pi_index: int, change_time, max_wait_time, k) -> tuple:

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
    
    
    max_waiting_time = timedelta(seconds = max_wait_time)
    change_time = timedelta(days=change_time.days, seconds=change_time.seconds)
    if k == 1:
        change_time = pd.to_timedelta(0, unit='seconds')
    
    
        
    for trip_idx, trip in (stoptimes_dict[route].items()):

        # ! this error occurs due to the removal of stop_times > 23:59 !
        try:
            t1 = trip[pi_index-1][1] 
        except IndexError:
     #       print ('except -1,-1')
            return -1, -1 
        
        
        #if p_i == 3368:
        #    print (f'p_i = {p_i} t1 = {t1}')
        
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
               total_walk_time = total_walk_time + leg[3].total_seconds() 
               last_arrive_time = leg[4]     
               if not first_leg_found:
                    first_leg_found = True        
             else:               
               total_boarding_count = total_boarding_count + 1
               total_drive_time = total_drive_time + (leg[3] - leg[0]).total_seconds()
               
               if  first_leg_found:  #distract from boarding time previous arrive time
                  if last_arrive_time != 0:
                        total_waiting_time = total_waiting_time + (leg[0] - last_arrive_time).total_seconds() 
               else:
                  total_waiting_time = (leg[0] - D_TIME).total_seconds()  
                  first_leg_found = True                  
               last_arrive_time = leg[3]
            
    total_time_to_dest = total_walk_time + total_waiting_time + total_drive_time

    """

    if len(journey) == 1:
        leg = journey[1]
        if leg_start[0] == 'walking':
            total_time_to_dest = leg_start[3].total_seconds()
        else:     
            total_time_to_dest = (leg_start[3] - leg_start[0]).total_seconds()

        return total_time_to_dest, total_walk_time, total_waiting_time, total_boarding_count, total_drive_time 
    

    leg_start = journey[1]
    if leg_start[0] == 'walking':
        time_start = leg_start[4].total_seconds()
    else:     
        time_start = leg_start[0].total_seconds()

    leg_finish = journey[-1]
    if leg_finish[0] == 'walking':
        time_finish = leg_start[4].total_seconds()
    else:     
        time_finish = leg_start[3].total_seconds()
    
    total_time_to_dest = time_finish- time_start
    """
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
               total_walk_time = total_walk_time + leg[3].total_seconds() 
               last_arrive_time = leg[4]
               if not first_leg_found:
                    first_leg_found = True        
             else:               
               total_boarding_count = total_boarding_count + 1
               total_drive_time = total_drive_time - (leg[3] - leg[0]).total_seconds()
               

               if  first_leg_found:  #distract from boarding time previous arrive time
                  if last_arrive_time != 0:
                   total_waiting_time = total_waiting_time - (leg[0] - last_arrive_time).total_seconds() 
               else:
                  total_waiting_time = - (leg[0] - D_TIME).total_seconds()  
                  first_leg_found = True                  
               last_arrive_time = leg[3]

    
    total_time_to_dest = total_walk_time + total_waiting_time + total_drive_time
    """
    if len(journey) == 1:
        leg = journey[1]
        if leg_start[0] == 'walking':
            total_time_to_dest = leg_start[3].total_seconds()
        else:     
            total_time_to_dest = (leg_start[0] - leg_start[3]).total_seconds()
        return total_time_to_dest, total_walk_time, total_waiting_time, total_boarding_count, total_drive_time 
    

    leg_start = journey[-1]
    if leg_start[0] == 'walking':
        time_start = (leg_start[4]).total_seconds()
    else:     
        time_start = leg_start[3].total_seconds()

    leg_finish = journey[1]
    if leg_finish[0] == 'walking':
        time_finish = leg_start[4].total_seconds()
    else:     
        time_finish = leg_start[3].total_seconds()
    
    total_time_to_dest = time_start- time_finish
    """

    return total_time_to_dest, total_walk_time, total_waiting_time, total_boarding_count, total_drive_time 


def metersToDecimalDegrees( meters):
    return meters / (111.32 * 1000 )
 
        
def get_dist_time(speed,lon1,lat1,lon2,lat2):
    dist=  haversine(lon1, lat1, lon2, lat2)*1000
    time=dist/speed
    return dist,time  
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance (in kilometers) between two points
    on the Earth's surface specified by longitude and latitude (in degrees).
    """
    # Convert degrees to radians
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Radius of the Earth (mean value in kilometers)
    radius = 6371  # Earth's radius in kilometers

    # Calculate the distance
    distance = radius * c

    return distance        