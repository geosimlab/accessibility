"""
Module contains RAPTOR implementation.
"""

from RAPTOR.raptor_functions import *
from datetime import datetime, date


def rev_raptor(SOURCE, DESTINATION, D_TIME, MAX_TRANSFER, WALKING_FROM_SOURCE,
                CHANGE_TIME_SEC, routes_by_stop_dict, stops_dict, stoptimes_dict, 
                footpath_start_dict,footpath_process_dict,footpath_finish_dict,
                idx_by_route_stop_dict,Maximal_travel_time,
                ExactTransfersCount, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime) -> list:
    '''
    Standard Raptor implementation

    Args:
        SOURCE (int): stop id of source stop.
        DESTINATION (int): stop id of destination stop.
        D_TIME (pandas.datetime): departure time.
        MAX_TRANSFER (int): maximum transfer limit.
        WALKING_FROM_SOURCE (int): 1 or 0. 1 indicates walking from SOURCE is allowed.
        CHANGE_TIME_SEC (int): change-time in seconds.
        routes_by_stop_dict (dict): preprocessed dict. Format {stop_id: [id of routes passing through stop]}.
        stops_dict (dict): preprocessed dict. Format {route_id: [ids of stops in the route]}.
        stoptimes_dict (dict): preprocessed dict. Format {route_id: [[trip_1], [trip_2]]}.
        footpath_dict (dict): preprocessed dict. Format {from_stop_id: [(to_stop_id, footpath_time)]}.
        idx_by_route_stop_dict (dict): preprocessed dict. Format {(route id, stop id): stop index in route}.

    Returns:
        out (list): list of pareto-optimal arrival timestamps.

    Examples:
        >>> output = raptor(36, 52, pd.to_datetime('2022-06-30 05:41:00'), 4, 1, 0, 1, routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_dict, idx_by_route_stop_dict)
        >>> print(f"Optimal arrival time are: {output}")

    See Also:
        HypRAPTOR, Tip-based Public Transit Routing (TBTR)
    '''

    #print (f'stops_dict[19630] {stops_dict[19630]}')
    #print (f'stops_dict[19625] {stops_dict[19625]}')    
    #print ('working rev raptor ...')
    #current_date = date.today()
    #D_TIME = datetime.combine(current_date, D_TIME.time())
    D_TIME = pd.Timestamp(D_TIME)
    
    my_name=rev_raptor.__name__
    message=""
    sep=","
    out = []
    marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time = initialize_rev_raptor(routes_by_stop_dict, SOURCE, MAX_TRANSFER)
    change_time = pd.to_timedelta(CHANGE_TIME_SEC, unit='seconds')
    

    (label[0][SOURCE], star_label[SOURCE]) = (D_TIME, D_TIME)
    Q = {}  # Format of Q is {route:stop index}
    roundsCount = MAX_TRANSFER + 1
    trans_info = -1     
    
    MaxWalkDist1_time = timedelta(seconds=MaxWalkDist1)
    MaxWalkDist2_time = timedelta(seconds=MaxWalkDist2)    
    MaxWalkDist3_time = timedelta(seconds=MaxWalkDist3) 

    if WALKING_FROM_SOURCE == 1 :
        try:
            if trans_info == -1:
             trans_info = footpath_finish_dict[SOURCE]

             #print (f' trans_info {trans_info}')
            for i in trans_info:
                
                (p_dash, to_pdash_time) = i

                if not(label[0].get(p_dash)):
                    continue    

                if to_pdash_time > MaxWalkDist3_time:
                   continue
                new_p_dash_time = D_TIME - to_pdash_time
                label[0][p_dash] = new_p_dash_time
                star_label[p_dash] = new_p_dash_time
                pi_label[0][p_dash] = ('walking', SOURCE, p_dash, to_pdash_time, new_p_dash_time)
                                    
                if marked_stop_dict[p_dash] == 0:
                    marked_stop.append(p_dash)
                    marked_stop_dict[p_dash] = 1
        except  KeyError as e:
            pass
        #print ('walk friom source')
        #print (f' pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')   

    # Main Code
    # Main code part 1
    
    for k in range(1, roundsCount + 1):
        #print (f'round {k}')
        #print (f'part 1') 
        
        Q.clear()
        while marked_stop:
            p = marked_stop.pop()
            marked_stop_dict[p] = 0
            
            # may by stop exist in layer but not exist in PKL
            try:
               routes_serving_p = routes_by_stop_dict[p]
            except:
               continue

            for route in routes_serving_p:
                stp_idx = idx_by_route_stop_dict[(route, p)]
                try:
                    Q[route] = min(stp_idx, Q[route])
                except  KeyError as e:
                    Q[route] = stp_idx
            
        

        #print (f'part 2')
        # Main code part 2
        
        boarding_time, boarding_point = -1, -1,
        #print (f' stops_dict [14213_1] {stops_dict["14213_1"]}')
        
        for route, current_stopindex_by_route in Q.items():
            boarding_time, boarding_point = -1, -1           
            current_trip_t = -1

            if not stops_dict.get(route):
               continue

            for p_i in stops_dict[route][current_stopindex_by_route - 1:]:  #changed Igor

                #if p_i == 1718:
                #   print (f'p_i == 1718 stops_dict [14213] {stops_dict[14213]}')
                                
                maxbound = star_label[p_i]
                if DESTINATION != 0:
                    maxbound = max(maxbound,star_label[DESTINATION]) 
                
                to_process = True
                
                
                #if current_trip_t != -1 and len(current_trip_t) > current_stopindex_by_route - 1:    
                if current_trip_t != -1:
                    
                    
                    arr_by_t_at_pi = current_trip_t[current_stopindex_by_route-1][1]  #changed Igor
                    
                
                      #print (f'begin_time_for_p_i {begin_time_for_p_i} Maximal_travel_time {Maximal_travel_time}  arr_by_t_at_pi {arr_by_t_at_pi}') 
                    if D_TIME - Maximal_travel_time > arr_by_t_at_pi: 
                        to_process=False
                                              
                    if to_process and boarding_point != p_i: #and boarding_time >= arr_by_t_at_pi :
                     #print ('to_process!')
                     label[k][p_i], star_label[p_i] = arr_by_t_at_pi, arr_by_t_at_pi

                     
                     pi_label[k][p_i] = (boarding_time, boarding_point, p_i, arr_by_t_at_pi, tid)
                                          
                     """
                     корректировка времени завершения, если последний шаг - пешая прогулка
                     (использую информацию о приезде на последнюю остановку, 
                     так чтобы не ждать, сразу идти в точку назначения)

                     adjustment completion time, if the last step is walking
                     (use information about arrival at the last stop,
                     so don’t wait, go straight to your destination).
                     """
                     """
                     if k == 1 and pi_label[0][boarding_point] !=  -1:
                        
                        current_tuple = pi_label[k-1][boarding_point]
                        new_tuple = (current_tuple[0], current_tuple[1], current_tuple[2], current_tuple[3], boarding_time)
                        pi_label[k-1][boarding_point] = new_tuple
                        print (f'correct new_tuple {new_tuple}')
                     """   
                        
    
                     if marked_stop_dict[p_i] == 0:
                        marked_stop.append(p_i)
                        marked_stop_dict[p_i] = 1
                       
                #if current_trip_t == -1 or (current_stopindex_by_route - 1) < len(current_trip_t) and (not current_trip_t[current_stopindex_by_route - 1] or label[k - 1][p_i] - change_time > current_trip_t[current_stopindex_by_route - 1][1]):     
                if current_trip_t == -1 or (label[k - 1][p_i] - change_time > current_trip_t[current_stopindex_by_route-1][1]):     
                #what means the last condition: we found new arrive time label[k - 1][p_i] to current stop
                # and if we subtract from it change_time that still it will be greater than
                #current_trip_t[current_stopindex_by_route][1] - so we need to find a trip
                # with more later arrive time but the erliest from them, and it is what
                # function get_earliest_trip_new returns
                    
                    
                    #My comment : his condition means that current trip arrives too early
                     # assuming arrival_time = departure_time
                    
                       
                    tid, current_trip_t = get_earliest_trip_new(stoptimes_dict, route, label[k - 1][p_i], current_stopindex_by_route, change_time, MaxWaitTime, k)
                    
                    if current_trip_t == -1:
                        boarding_time, boarding_point = -1, -1
                    else: 
                        boarding_point = p_i
                        boarding_time = current_trip_t[current_stopindex_by_route-1][1]                           
                        

                        #if D_TIME - Maximal_travel_time > boarding_time:
                        #  boarding_time = -1
                current_stopindex_by_route = current_stopindex_by_route + 1

        #print (f' part 2 pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')

        # Main code part 3
        #print (f'part 3')
        marked_stop_copy = [*marked_stop]
        destination_accessed=False
    
        if not destination_accessed: 
           walking_dict = footpath_process_dict
           
           if k < roundsCount:
                walking_dict = footpath_process_dict
                save_marked_stop = True

                destination_accessed, marked_stop_dict,marked_stop,marked_stop_copy,label,star_label,pi_label = process_walking_stage(DESTINATION,
                D_TIME, MaxWalkDist2_time, Maximal_travel_time, k, walking_dict,
                marked_stop_dict, marked_stop, marked_stop_copy,label,star_label,pi_label, save_marked_stop) 


           walking_dict = footpath_start_dict

           save_marked_stop = False

           destination_accessed, marked_stop_dict,marked_stop,marked_stop_copy,label,star_label,pi_label = process_walking_stage(DESTINATION,
           D_TIME,MaxWalkDist1_time,Maximal_travel_time,k, walking_dict, 
           marked_stop_dict,marked_stop, marked_stop_copy,label,star_label,pi_label, save_marked_stop) 

           
        #print (f' finish revpaptor pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')
        # Main code End
        if marked_stop == deque([]):
            break
   
    #My new output   

    rounds_inwhich_desti_reached, trip_set, rap_out, pareto_set = 0, 0, 0, 0
    if DESTINATION!=0:
     rounds_inwhich_desti_reached, trip_set, rap_out,pareto_set\
     = post_processing(DESTINATION, pi_label, label,MaxWalkDist2,MAX_TRANSFER,ExactTransfersCount)
     out = [rounds_inwhich_desti_reached, trip_set,rap_out,pareto_set,""]
     message=""
     if rounds_inwhich_desti_reached!=[] and rounds_inwhich_desti_reached!=None:
      for _, journey in pareto_set:
       total_time_to_dest,total_walk_time,total_waiting_time,total_boarding_count,total_drive_time=\
       post_processing_2(D_TIME, journey, MaxWalkDist2)
       message=str(SOURCE)+sep+str(D_TIME)+sep+str(DESTINATION)+sep+str(total_time_to_dest)\
       +sep+str(total_walk_time)+sep+str(total_waiting_time)+sep+str(total_boarding_count)\
       +sep+str(total_drive_time)       
       
      out[4]=message                
    else:      
     
     #print (f'!before postprocesiing pi_label {pi_label}')
     reachedLabels = post_processingAll(my_name, SOURCE, D_TIME, label, pi_label, MAX_TRANSFER, ExactTransfersCount, MaxWalkDist2, MaxWalkDist1)
     out=reachedLabels    
    return out

def process_walking_stage(DESTINATION, D_TIME, WALKING_LIMIT, Maximal_travel_time, stage,
        footpath_dict, marked_stop_dict, marked_stop, marked_stop_copy,label,star_label,pi_label, save_marked_stop):
  
  destination_accessed=False

  if  True:
         k=stage 

         for p in marked_stop_copy:

            #if p == 3368:
            #    print (f'p == 3368 trans_info={footpath_dict[p]}')

            if pi_label[k][p][0] == 'walking':
                continue

            try:
                trans_info = footpath_dict[p]
            except:
                continue
            
            
            if  not trans_info:                 
                 continue


            for i in trans_info:
                (p_dash, to_pdash_time) = i

                if not(pi_label[k].get(p_dash)):
                   
                   continue 

                new_p_dash_time = label[k][p] - to_pdash_time #changed + to -

                if D_TIME - Maximal_travel_time > new_p_dash_time:
                    
                    continue
                if to_pdash_time > WALKING_LIMIT:
                      
                    continue

                #there are stops that are in stops but not in stoptimes
                maxbound = star_label[p_dash]
                
                if DESTINATION != 0:
                    maxbound= max(maxbound,star_label[DESTINATION])

                # #### TEST IGOR #########
                # this line is "don't rewrite founded bus trip to footleg"
                if pi_label[k][p_dash] != - 1 and pi_label[k][p_dash][0] != 'walking':
                     
                       
                    continue
                #### TEST IGOR #########     
                
                # veryfy cause if exist solve for this p_dash (not was better?)
                if pi_label[k][p_dash] != -1 and pi_label[k][p_dash][0] == "walking":
                    if not need_correct(k, pi_label, p_dash, p, to_pdash_time):                                   
                        
                        continue



                if label[k][p_dash] < new_p_dash_time and new_p_dash_time > maxbound:
                         
                    label[k][p_dash], star_label[p_dash] = new_p_dash_time, new_p_dash_time

                    pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)
                                           
                    # recalculate_pi_label(k ,p_dash, label, pi_label,footpath_dict.get(p_dash))
                       
                    if DESTINATION != 0:
                        if p_dash == DESTINATION:
                            destination_accessed = True
                            break #exit from cycle  by destination_accessed
                        if save_marked_stop:  
                          if marked_stop_dict[p_dash] == 0:
                            marked_stop.append(p_dash)
                            marked_stop_dict[p_dash] = 1
                    
            
  return destination_accessed, marked_stop_dict,marked_stop, marked_stop_copy,label,star_label,pi_label       
  """
  Input:
  get  pi_label[k][p_dash]  = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)   
  that is not -1.
  also get its possible new state: pnew, p_dash, to_pdash_time_new,
   Get pi_label[k][p]. If it is not in walking mode then get it arrive time: time1= pi_label[k][p][3]
   Then check that time1+to_pdash_time_new >= new_p_dash_time: if not that not change pi_label

   
  """
def need_correct(k, pi_label, p_dash, p, to_pdash_time_new)  :

  result = False  
  if pi_label[k][p] != -1 and pi_label[k][p][0] != "walking":
    if pi_label[k][p][3] - to_pdash_time_new > pi_label[k][p_dash][4]:
        result = True

  return result
"""
def recalculate_pi_label(k,p,label, pi_label,trans_info):
   for i in trans_info:
     (p_dash, to_pdash_time) = i
     if pi_label[k][p_dash]!=-1 and pi_label[k][p_dash][0]=='walking' and pi_label[k][p_dash][1]==p:
       new_p_dash_time = label[k][p] - to_pdash_time
       pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)      
"""               