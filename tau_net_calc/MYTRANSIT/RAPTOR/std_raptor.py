"""
Module contains RAPTOR implementation.
"""

from RAPTOR.raptor_functions import *
from PyQt5.QtWidgets import QApplication
from datetime import timedelta

def raptor (SOURCE, D_TIME, MAX_TRANSFER, MIN_TRANSFER, change_time, 
           routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_dict, 
           idx_by_route_stop_dict: dict, Maximal_travel_time, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime, MaxWaitTimeTransfer) -> list:
    '''
    Standard Raptor implementation

    Args:
        SOURCE (int): stop id of source stop.
        D_TIME (pandas.datetime): departure time.
        MAX_TRANSFER (int): maximum transfer limit.
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
    
    timeres1 = 0
    timeres2 = 0
    timeres3 = 0
    timeres4 = 0
    timeres5 = 0

    #D_TIME = pd.Timestamp(D_TIME)
   
    my_name = raptor.__name__
    out = []
    
    marked_stop, marked_stop_dict, label, pi_label, star_label, inf_time = initialize_raptor(routes_by_stop_dict, SOURCE, MAX_TRANSFER)
    
    change_time_save = change_time
    
    (label[0][SOURCE], star_label[SOURCE]) = (D_TIME, D_TIME)
    Q = {}  # Format of Q is {route:stop index}
    roundsCount = MAX_TRANSFER + 1
    trans_info = -1     
   
    MaxWalkDist1_time = MaxWalkDist1
    MaxWalkDist2_time = MaxWalkDist2
    MaxWalkDist3_time = MaxWalkDist3
        
    max_time = D_TIME + Maximal_travel_time
        
    if  True:        
        try:
           if trans_info == -1:
            trans_info = footpath_dict[SOURCE]
            

           for i in trans_info:
                
                (p_dash, to_pdash_time) = i
                #print (f'to_pdash_time {to_pdash_time}')
                                
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
        QApplication.processEvents()

        
        if k == 1:
            MaxWaitCurr = MaxWaitTime
            change_time = 0
        else:
            MaxWaitCurr = MaxWaitTimeTransfer 
            change_time = change_time_save
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
            QApplication.processEvents()
            boarding_time, boarding_point = -1, -1
            current_trip_t = -1

            if not stops_dict.get(route):
               continue
            
            for p_i in stops_dict[route][current_stopindex_by_route-1:]:                
                                               
                to_process = True  
                
                if current_trip_t != -1: 
                    
                    try:
                        arr_by_t_at_pi = current_trip_t[current_stopindex_by_route - 1][1]
                    except:
                       continue 
                                        
                
                    if max_time < arr_by_t_at_pi: 
                        to_process = False
                    
                    if to_process and boarding_point != p_i and boarding_time <= arr_by_t_at_pi:                                        
                       
                       label[k][p_i], star_label[p_i] = arr_by_t_at_pi, arr_by_t_at_pi
                       pi_label[k][p_i] = (boarding_time, boarding_point, p_i, arr_by_t_at_pi, tid)
                       
                       if marked_stop_dict[p_i] == 0:
                            marked_stop.append(p_i)
                            marked_stop_dict[p_i] = 1


                
                if current_trip_t == -1 or (label[k - 1][p_i] + change_time < current_trip_t[current_stopindex_by_route-1][1]):
                    #my comment: this condition means that with current trip one is not on time
                    # to next arriving so on need to get more later trip
                    
                    tid, current_trip_t = get_latest_trip_new(stoptimes_dict, route, label[k - 1][p_i], current_stopindex_by_route, change_time, MaxWaitCurr)
                                    
                    if current_trip_t == -1:
                        boarding_time, boarding_point = -1, -1
                    else:
                        boarding_point = p_i
                       
                        boarding_time = current_trip_t[current_stopindex_by_route-1][1] # Igor changed
                        
                                                   
                current_stopindex_by_route = current_stopindex_by_route + 1

        #print (f' pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')
        #print (f' after part2 {datetime.now()}')    
        
        # Main code part 3
        #print (f'part 3')
                      
        if k < roundsCount and MaxWalkDist2_time != MaxWalkDist3_time:
        
                save_marked_stop = True
                                
                process_walking_stage(max_time, MaxWalkDist2_time, k, footpath_dict,
                marked_stop_dict,marked_stop, label,star_label,pi_label, save_marked_stop) 
           
           
        save_marked_stop = False
        
        time1, time2, time3, time4, time5, time6 = process_walking_stage(max_time , MaxWalkDist3_time, k, footpath_dict, 
        marked_stop_dict, marked_stop, label, star_label, pi_label, save_marked_stop)
        
        #print (f' pi_label {pi_label}')
        #print (f' marked_stop {marked_stop}')
        #print (f' after part3 {datetime.now()}')   
        
        # Main code End
        if marked_stop == deque([]):
            break
    
    
    
    
    reachedLabels = post_processingAll (my_name, SOURCE, D_TIME, label, pi_label, MIN_TRANSFER, MaxWalkDist3)
        
    out = reachedLabels
    
    return out, time1, time2, time3, time4, time5, time6



def process_walking_stage(max_time, WALKING_LIMIT, k,
        footpath_dict, marked_stop_dict, marked_stop, label, star_label, pi_label, save_marked_stop):
         time1res = timedelta()
         time2res = timedelta()
         time3res = timedelta()
         time4res = timedelta()
         time5res = timedelta()
         time6res = timedelta()

         marked_stop_copy = [*marked_stop]
         
         for p in marked_stop_copy:
            QApplication.processEvents()
            
            if pi_label[k][p][0] == 'walking':
                continue

            try:
                trans_info = footpath_dict.get(p)
            except:
                continue
    

            if  not trans_info:                 
                 continue
                
            
            for p_dash, to_pdash_time in trans_info:
                
                #start_time6 = datetime.now()

                if p_dash not in pi_label[k]:
                    continue 

                # this line is "don't rewrite founded bus trip to footleg"
                if pi_label[k][p_dash] != - 1 and pi_label[k][p_dash][0] != 'walking':
                    continue

                #end_time6 = datetime.now()
                #time6 = end_time6 - start_time6
                #time6res += time6
                
                
                #start_time1 = datetime.now()
                
                new_p_dash_time = label[k][p] + to_pdash_time
                
                #end_time1 = datetime.now()
                #time1 = end_time1 - start_time1
                #time1res += time1
                
                #start_time2 = datetime.now()
                
                if max_time < new_p_dash_time or to_pdash_time > WALKING_LIMIT:
                    continue

                #end_time2 = datetime.now()
                #time2 = end_time2 - start_time2    
                #time2res += time2

                #start_time3 = datetime.now()
                
                # veryfy cause if exist solve for this p_dash (not was better?)
                if pi_label[k][p_dash] != -1 and pi_label[k][p_dash][0] == "walking":
                    if new_p_dash_time > pi_label[k][p_dash][4]:
                        continue

                #end_time3 = datetime.now()
                #time3 = end_time3 - start_time3        
                #time3res += time3

                #start_time4 = datetime.now()
                
                label[k][p_dash], star_label[p_dash] = new_p_dash_time, new_p_dash_time
                
                pi_label[k][p_dash] = ('walking', p, p_dash, to_pdash_time, new_p_dash_time)
                #end_time4 = datetime.now()
                #time4 = end_time4 - start_time4            
                #time4res += time4

                #start_time5 = datetime.now()                                    
                if save_marked_stop and marked_stop_dict[p_dash] == 0:
                    marked_stop.append(p_dash)
                    marked_stop_dict[p_dash] = 1
                #end_time5 = datetime.now()
                #time5 = end_time5 - start_time5            
                #time5res += time5

         
         return time1res, time2res, time3res, time4res, time5res, time6res

         
     
