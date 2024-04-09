"""
Module contains RAPTOR implementation.
"""
import pandas as pd
from RAPTOR.raptor_functions import *
from datetime import datetime, date
from datetime import timedelta
"""
 Global variables 
"""



def raptor (SOURCE, DESTINATION, D_TIME, MAX_TRANSFER, WALKING_FROM_SOURCE, CHANGE_TIME_SEC, 
           routes_by_stop_dict, stops_dict, stoptimes_dict, 
           footpath_start_dict, footpath_process_dict, footpath_finish_dict,
           idx_by_route_stop_dict: dict, Maximal_travel_time,
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
    
    #print ('working raptor ...')
    #current_date = date.today()
    #D_TIME = datetime.combine(current_date, D_TIME.time())
    D_TIME = pd.Timestamp(D_TIME)
   
    my_name = raptor.__name__
    message = ""
    sep = ","
    out = []
    
    marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time = initialize_raptor(routes_by_stop_dict, SOURCE, MAX_TRANSFER)
    change_time = pd.to_timedelta(CHANGE_TIME_SEC, unit='seconds')
    
    (label[0][SOURCE], star_label[SOURCE]) = (D_TIME, D_TIME)
    Q = {}  # Format of Q is {route:stop index}
    roundsCount = MAX_TRANSFER + 1
    trans_info = -1     
       
    MaxWalkDist1_time = timedelta(seconds=MaxWalkDist1)
    MaxWalkDist2_time = timedelta(seconds=MaxWalkDist2)    
    MaxWalkDist3_time = timedelta(seconds=MaxWalkDist3)  
    
   

    #MaxWalkDist1_time = timedelta(hours=int(MaxWalkDist1_time.split(':')[0]), minutes=int(MaxWalkDist1_time.split(':')[1]), seconds=int(MaxWalkDist1_time.split(':')[2]))
    
    if  WALKING_FROM_SOURCE == 1 :     # and MAX_TRANSFER>0 ?    
        try:
           if trans_info == -1:
            trans_info = footpath_start_dict[SOURCE]

            #print (f' trans_info {trans_info}')
           for i in trans_info:
                
                (p_dash, to_pdash_time) = i
                                
                if not(label[0].get(p_dash)):
                   continue
                
                if to_pdash_time > MaxWalkDist1_time:
                    continue
                
                new_p_dash_time = D_TIME + to_pdash_time
                label[0][p_dash] = new_p_dash_time
                star_label[p_dash] = new_p_dash_time
                pi_label[0][p_dash] = ('walking', SOURCE, p_dash, to_pdash_time, new_p_dash_time)
                                
                if marked_stop_dict[p_dash] == 0:
                    marked_stop.append(p_dash)
                    marked_stop_dict[p_dash] = 1

                #print (f'marked_stop_dict added  ok {p_dash}')    
            
        except  KeyError as e:
           pass
    
    #print (f'pi_label {pi_label}')    
    #print (f'before big cycle {datetime.now()}')    
    
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
            
        #print (f' Q = {Q}')
        #print (f' after part1 {datetime.now()}')    
        #print (f' pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')     

        
        # Main code part 2
        
        #print (f'part 2')
        boarding_time, boarding_point  = -1, -1  

        for route, current_stopindex_by_route in Q.items():
            boarding_time, boarding_point = -1, -1
            current_trip_t = -1

            if not stops_dict.get(route):
               continue
            
            for p_i in stops_dict[route][current_stopindex_by_route-1:]:                

                minbound = star_label[p_i]
                if DESTINATION != 0:
                    minbound= min(minbound,star_label[DESTINATION])   
                
                to_process = True  
                
                # "len(current_trip_t) > current_stopindex_by_route" - some trips shorts others
                #if current_trip_t != -1 and len(current_trip_t) > current_stopindex_by_route - 1:
                if current_trip_t != -1: 
                    
                    arr_by_t_at_pi = current_trip_t[current_stopindex_by_route - 1][1]                  # Igor changed 
                                        
                
                    if D_TIME + Maximal_travel_time < arr_by_t_at_pi: 
                        to_process = False
                    
                    if to_process and boarding_point != p_i and boarding_time <= arr_by_t_at_pi:                                        
                       
                       label[k][p_i], star_label[p_i] = arr_by_t_at_pi, arr_by_t_at_pi
                       pi_label[k][p_i] = (boarding_time, boarding_point, p_i, arr_by_t_at_pi, tid)
                       
                       if marked_stop_dict[p_i] == 0:
                            marked_stop.append(p_i)
                            marked_stop_dict[p_i] = 1


                #if current_trip_t == -1 or (current_stopindex_by_route - 1) < len(current_trip_t) and (not current_trip_t[current_stopindex_by_route - 1] or label[k - 1][p_i] + change_time < current_trip_t[current_stopindex_by_route - 1][1]):
                if current_trip_t == -1 or (label[k - 1][p_i] + change_time < current_trip_t[current_stopindex_by_route-1][1]):
                # current_trip_t[current_stopindex_by_route - 1][1]:  # assuming arrival_time = departure_time # Igor changed
                    #my comment: this condition means that with current trip one is not on time
                    # to next arriving so on need to get more later trip
                    
                    tid, current_trip_t = get_latest_trip_new(stoptimes_dict, route, label[k - 1][p_i], current_stopindex_by_route, change_time, MaxWaitTime, k)
                                    
                    if current_trip_t == -1:
                        boarding_time, boarding_point = -1, -1
                    else:
                        boarding_point = p_i
                       
                        boarding_time = current_trip_t[current_stopindex_by_route-1][1] # Igor changed
                        
                        
                        #if D_TIME + Maximal_travel_time < boarding_time:
                        #  boarding_time = -1
                           
                current_stopindex_by_route = current_stopindex_by_route + 1

        #print (f' pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')
        #print (f' after part2 {datetime.now()}')    
        
        # Main code part 3
        #print (f'part 3')
        
        marked_stop_copy = [*marked_stop]
       
        #footpath_dict_replaced=False   
        #walking_dict = footpath_process_dict
        destination_accessed = False
        
        if not destination_accessed: 
           walking_dict = footpath_process_dict
                      
           if k < roundsCount:
                walking_dict = footpath_process_dict
                save_marked_stop = True
                                
                destination_accessed, marked_stop_dict,marked_stop,marked_stop_copy,label,star_label,pi_label = process_walking_stage(DESTINATION,
                D_TIME, MaxWalkDist2_time,Maximal_travel_time,k, walking_dict,
                marked_stop_dict,marked_stop, marked_stop_copy,label,star_label,pi_label, save_marked_stop) 
           
           
           walking_dict = footpath_finish_dict
           
           save_marked_stop = False
           
           destination_accessed, marked_stop_dict,marked_stop,marked_stop_copy,label,star_label,pi_label = process_walking_stage(DESTINATION,
           D_TIME, MaxWalkDist3_time, Maximal_travel_time, k, walking_dict, 
           marked_stop_dict, marked_stop, marked_stop_copy, label, star_label, pi_label, save_marked_stop) 
           

        #print (f' pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')
        #print (f' after part3 {datetime.now()}')   
        """
        print (f' pi_label[0][3491] {pi_label[0][3491]}')
        print (f' pi_label[1][3491] {pi_label[1][3491]}')
        print (f' pi_label[2][3491] {pi_label[2][3491]}')
        print (f' pi_label[0][1187] {pi_label[0][1187]}')
        print (f' pi_label[1][1187] {pi_label[1][1187]}')
        print (f' pi_label[2][1187] {pi_label[2][1187]}')
        """ 
        

        # Main code End
        if marked_stop == deque([]):
            break
    
    
    #My new output
    rounds_inwhich_desti_reached, trip_set, rap_out,pareto_set = 0, 0, 0, 0
    
    if DESTINATION != 0:
     
     rounds_inwhich_desti_reached, trip_set, rap_out,pareto_set\
     = post_processing(DESTINATION, pi_label, label, MaxWalkDist2, MAX_TRANSFER,ExactTransfersCount, MaxWalkDist3)
     out = [rounds_inwhich_desti_reached, trip_set,rap_out,pareto_set,""]
     message=""
     if rounds_inwhich_desti_reached != [] and rounds_inwhich_desti_reached != None:
      for _, journey in pareto_set:
       total_time_to_dest,total_walk_time,total_waiting_time,total_boarding_count,total_drive_time = \
       post_processing_2(D_TIME, journey)
       message=str(SOURCE)+sep+str(D_TIME)+sep+str(DESTINATION)+sep+str(total_time_to_dest)\
       +sep+str(total_walk_time)+sep+str(total_waiting_time)+sep+str(total_boarding_count)\
       +sep+str(total_drive_time)       
       
      out[4] = message                
    else:      
     
    
     reachedLabels = post_processingAll(my_name, SOURCE, D_TIME, label, pi_label, MAX_TRANSFER, ExactTransfersCount, 
                                        MaxWalkDist2, MaxWalkDist3)
     #print (f' reachedLabels {reachedLabels}')
    

    out = reachedLabels
    #print (f'finish raptor {datetime.now()}')   
    return out


"""
Changed variables:marked_stop_dict,marked_stop,label,star_label,pi_label
"""
def process_walking_stage(DESTINATION, D_TIME, WALKING_LIMIT, Maximal_travel_time, stage,
        footpath_dict, marked_stop_dict, marked_stop, marked_stop_copy, label, star_label, pi_label, save_marked_stop):
    
  destination_accessed = False
  
  if  True :    
         k = stage    
         
         for p in marked_stop_copy:
            
            if pi_label[k][p][0] == 'walking':
                continue
            
            try:
                trans_info = footpath_dict.get(p)
            except:
                continue

            if  not trans_info:                 
                 continue
                
            
            for i in trans_info:
                (p_dash, to_pdash_time) = i

                if not(pi_label[k].get(p_dash)):
                   continue 
    
                new_p_dash_time = label[k][p] + to_pdash_time
                    
                if D_TIME + Maximal_travel_time < new_p_dash_time:
                    continue
                if to_pdash_time > WALKING_LIMIT:
                    continue         
                
                #there are stops that are in stops but not in stoptimes
                #try:
                minbound = star_label[p_dash]
                #except:
                #   continue
                
                if DESTINATION != 0:
                    minbound = min(minbound, star_label[DESTINATION])
                                                                       
                # #### TEST IGOR #########
                # this line is "don't rewrite founded bus trip to footleg"
                if pi_label[k][p_dash] != - 1 and pi_label[k][p_dash][0] != 'walking':
                    continue
                #### TEST IGOR #########       

                # veryfy cause if exist solve for this p_dash (not was better?)
                if pi_label[k][p_dash] != -1 and pi_label[k][p_dash][0] == "walking":
                    if not need_correct(k, pi_label, p_dash, p, to_pdash_time):                                   
                        continue
                    
                    

                if label[k][p_dash] > new_p_dash_time and new_p_dash_time < minbound:                        

                    label[k][p_dash], star_label[p_dash] = new_p_dash_time, new_p_dash_time
                        
                    
                    pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)

                    #if p == 3368:
                    #    print (f' pi_label[{k}][{p_dash}] {pi_label[k][p_dash]}')   
                    
                    #recalculate_pi_label(k, p_dash, label, pi_label, footpath_dict.get(p_dash))

                    if DESTINATION != 0:
                        if p_dash == DESTINATION:
                            destination_accessed = True
                            break #exit from cycle  by destination_accessed
                        if save_marked_stop:  
                             if marked_stop_dict[p_dash] == 0:
                                marked_stop.append(p_dash)
                                marked_stop_dict[p_dash] = 1
                    
            
  return destination_accessed, marked_stop_dict, marked_stop, marked_stop_copy, label, star_label, pi_label       
"""
def process_final_walking_stage(D_TIME, Maximal_travel_time, stage,
        footpath_dict, marked_stop_copy, label, star_label, pi_label ):

        

        for p in marked_stop_copy:   
            k = stage
            begin_time_for_p = D_TIME
            trans_info = footpath_dict.get(p)
            for i in trans_info:
                (p_dash, to_pdash_time) = i
                new_p_dash_time = label[k][p] + to_pdash_time
                if begin_time_for_p != -1 and begin_time_for_p + Maximal_travel_time < new_p_dash_time:
                    minbound = star_label[p_dash]
                                                            
                    if label[k][p_dash] > new_p_dash_time and new_p_dash_time < minbound:                        
                        label[k][p_dash], star_label[p_dash] = new_p_dash_time, new_p_dash_time
                        pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)
                                     
        return marked_stop_copy, label, star_label, pi_label
"""     
  
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
  if pi_label[k][p] != - 1 and pi_label[k][p][0] != "walking":
      if pi_label[k][p][3] + to_pdash_time_new < pi_label[k][p_dash][4]:
        result = True

  return result
   
def recalculate_pi_label(k, p, label, pi_label, trans_info):
   for i in trans_info:
     (p_dash, to_pdash_time) = i

     if pi_label[k][p_dash] != -1 and pi_label[k][p_dash][0] == 'walking' and pi_label[k][p_dash][1] == p:
       
       new_p_dash_time = label[k][p] + to_pdash_time
       pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)      
   