"""
Runs the query algorithm
"""
from datetime import datetime, timedelta, date
#import datetime

from pandas import Timestamp
import pandas as pd
from qgis.core import QgsProject
from qgis.PyQt.QtCore import Qt
from PyQt5.QtWidgets import QApplication


from RAPTOR.std_raptor import raptor
from RAPTOR.rev_std_raptor import rev_raptor

import os

from shapely.geometry import Point
import math
# # Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def getParameters(settings):
  """Get some parameters from file parameters.txt and others from the list of paramters
  """
  PathToNetwork,PathToProtocols, NETWORK_NAME, SOURCE, DESTINATION, DESTARR, D_TIME,\
   MAX_TRANSFER, WALKING_FROM_SOURCE, CHANGE_TIME_SEC,\
   MaxTimeTravel, time_step, ExactTransfersCount, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime\
    =0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
  for key in settings:
      #print(key) 
      if key=="PathToNetwork":
         PathToNetwork = settings[key]
      if key=="PathToProtocols":
         PathToProtocols=settings[key]   
      if key=="NETWORK_NAME":
       NETWORK_NAME = settings[key]
      elif key == "SOURCE": 
       SOURCE = int(settings[key])
      elif key == "DESTINATION":
       DESTINATION = int(settings[key])
      elif key == "DESTARR":
       DESTARR =  settings[key] 
      elif key == "D_TIME": 
       D_TIME = pd.to_datetime (settings[key])
      elif key ==  "MAX_TRANSFER":       
       MAX_TRANSFER = int(settings[key])
      elif key == "WALKING_FROM_SOURCE": 
       WALKING_FROM_SOURCE = int (settings[key])
      elif key == "CHANGE_TIME_SEC":
       CHANGE_TIME_SEC =  int(settings[key])
      elif key == "MaxTimeTravel":
       MaxTimeTravel =  settings[key]       
      elif key == "time_step":
       time_step =  settings[key] 
      elif key == "ExactTransfersCount" :
        ExactTransfersCount = int( settings[key]) 
      elif key == "MaxWalkDist1" :
        MaxWalkDist1 = int( settings[key])
      elif key == "MaxWalkDist2" :
        MaxWalkDist2 = int( settings[key])   
      elif key == "MaxWalkDist3" :
        MaxWalkDist3 = int( settings[key])
      elif key == "MaxWaitTime" :
        MaxWaitTime = int( settings[key])     

  return PathToNetwork,PathToProtocols,NETWORK_NAME,SOURCE,DESTINATION,DESTARR,D_TIME,MAX_TRANSFER,\
    WALKING_FROM_SOURCE, CHANGE_TIME_SEC, MaxTimeTravel, time_step, ExactTransfersCount,\
   MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime

def str1(time):   
   output = add_zero(str(time.hour)) + ":" + add_zero(str(time.minute))+":" + add_zero(str(time.second))
   return output

def add_zero(s):
 if len(s) == 1:
    s = "0" + s
 return s   

def prepare_time_string(dtime):
  smin= str(dtime.minute)
  if len(smin)==1:
    smin="0"+smin
  shour= str(dtime.hour)
  if len(shour)==1:
    shour="0"+shour  
  str_d_time=shour+"_"+smin
  return str_d_time

def getRaptorDestinationTime(raptorOut):
  output=raptorOut
  journey_time ,begin_time,end_time=0,0,0
  rounds_inwhich_desti_reached=output[0]
  if rounds_inwhich_desti_reached is None:
      return -1,-1,-1  # destination cannot be reached
  trip_set=output[1]
  rap_out=output[2]
  pareto_journeys =output[3]
  for _, journey in pareto_journeys:
         accumulated_time_delta=0
         first_stop_found=False
         begin_time=0
         end_time= 0  #journey[-1][3].time()
         lastBusLegIndex=-1
         lastWalkingIndex=-1
         currentIndex=-1
         for leg in journey:
           currentIndex=currentIndex+1
           if leg[0] == 'walking':
             if  not first_stop_found:
              accumulated_time_delta=accumulated_time_delta+leg[3].total_seconds()
             lastWalkingIndex=currentIndex
           else:
              if  not first_stop_found:
                first_stop_found=True
                begin_time=leg[0]+ timedelta(accumulated_time_delta)
                #accumulated_time_delta=0 # all accumulated_time_delta before first stop was added
                # all accumulated_time_delta after that will be summed and added to end_tiime
              lastBusLegIndex =currentIndex
         end_time= journey[lastBusLegIndex][3]
         if lastWalkingIndex>lastBusLegIndex:
          end_time=end_time+journey[lastWalkingIndex][3]
         journey_time=(end_time-begin_time).total_seconds() 
         return [journey_time ,begin_time,end_time  ]
         

def compareMethods(settings)  -> tuple:
    """
    Get some parameters from file parameters.txt and others from the list of paramters
    1.In original main firstly work metod take_inputs() that returns algorithm, variant. We need only algorithm=RAPTOR and variant is one of
     0,1,2,3 - types of RAPTOR
    """
    PathToNetwork,PathToProtocols,NETWORK_NAME,SOURCE,DESTINATION,DESTARR,D_TIME,\
    MAX_TRANSFER,WALKING_FROM_SOURCE,CHANGE_TIME_SEC,Maximal_travel_time_int=\
    getParameters(settings)
    Maximal_travel_time=timedelta(seconds=Maximal_travel_time_int)
    stops_file, trips_file, stop_times_file, transfers_file, stops_dict, stoptimes_dict, footpath_dict, routes_by_stop_dict, idx_by_route_stop_dict, routesindx_by_stop_dict \
         = read_testcase(PathToNetwork, NETWORK_NAME)
    f = current_dir+"/accessedStops.txt" 
    count=len(DESTARR)
    reachedDest=[]
    reachedLabels=dict()
    with open(f, 'w') as filetowrite:
        filetowrite.write("Work begin time:"+ str(datetime.now())+"\n")
        filetowrite.write("Source stop:"+ str(SOURCE)+"\n")
        filetowrite.write("Maximal time: "+str(Maximal_travel_time_int)+" sec\n")
        for i in range(0,count):
          DESTINATION  =DESTARR[i]
          output = raptor(SOURCE, DESTINATION, D_TIME, MAX_TRANSFER, WALKING_FROM_SOURCE,WALKING_LIMIT, CHANGE_TIME_SEC, 
                            routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_dict, 
                            idx_by_route_stop_dict,Maximal_travel_time)
          reachedLabels=output[4]
          destTime=getRaptorDestinationTime(output)    
          if destTime < Maximal_travel_time_int and destTime!=-1:
           reachedDest.append(DESTINATION)
           filetowrite.write(str(DESTINATION)+","+str(destTime)
                           +"," + str(datetime.now()) +", reached lab count: "+str(len(reachedLabels))+ '\n')
        filetowrite.write("Reached destinations count:" + str(len(reachedDest)) +'\n')    
        filetowrite.write("Work end time:" + str(datetime.now()) +'\n') 

    return output  


def get_path_to_pkl (PathToNetwork, NETWORK_NAME):  
  return PathToNetwork+ f"/dict_builder/{NETWORK_NAME}"


def myload_all_dict(self, PathToNetwork, NETWORK_NAME, mode, today):
    """
    Args:
        NETWORK_NAME (str): network NETWORK_NAME.
        selected_layerName : use for filter stops_dict, remain only stop from current project 

    Returns:
        stops_dict (dict): preprocessed dict. Format {route_id: [ids of stops in the route]}.
        stoptimes_dict (dict): keys: route ID, values: list of trips in the increasing order of start time. Format-> dict[route_ID] = [trip_1, trip_2] where trip_1 = [(stop id, arrival time), (stop id, arrival time)]
        footpath_dict (dict): preprocessed dict. Format {from_stop_id: [(to_stop_id, footpath_time)]}.
        routes_by_stop_dict (dict): preprocessed dict. Format {stop_id: [id of routes passing through stop]}.
        idx_by_route_stop_dict (dict): preprocessed dict. Format {(route id, stop id): stop index in route}.
        
    """
    import pickle
    path = get_path_to_pkl (PathToNetwork, NETWORK_NAME)
    
    self.setMessage ("Load transfers_start_dict ...")
    QApplication.processEvents()
    
    with open(path+'/transfers_start_dict.pkl', 'rb') as file:
        footpath_start_dict = pickle.load(file)
    self.setMessage ("Load transfers_process_dict ...")    
    QApplication.processEvents()
    
    with open(path+'/transfers_process_dict.pkl', 'rb') as file:
        footpath_process_dict = pickle.load(file)
    self.setMessage ("Load transfers_finish_dict ...")
    QApplication.processEvents()    
    
    with open(path+'/transfers_finish_dict.pkl', 'rb') as file:
        footpath_finish_dict = pickle.load(file)
    self.setMessage ("Load routes_by_stop ...")
    QApplication.processEvents()
    
    with open(path+'/routes_by_stop.pkl', 'rb') as file:
        routes_by_stop_dict = pickle.load(file)
    
    if mode == 1:
      with open(path+'/stops_dict_pkl.pkl', 'rb') as file:
        stops_dict = pickle.load(file)

      self.setMessage ("Load stoptimes_dict ...")
      QApplication.processEvents()
    
      print ("start load stoptimes_dict")  
      with open(path+'/stoptimes_dict_pkl.pkl', 'rb') as file:
        stoptimes_dict = pickle.load(file)
      print ("finish load stoptimes_dict_pkl.pkl")  

      self.setMessage ("Load idx_by_route_stop.pkl ...")
      QApplication.processEvents()
    
      with open(path+'/idx_by_route_stop.pkl', 'rb') as file:
        idx_by_route_stop_dict = pickle.load(file)
          
    else:
     self.setMessage ("Load stops_dict_reversed ...")
     QApplication.processEvents()
    
     with open(path+'/stops_dict_reversed_pkl.pkl', 'rb') as file:  #reversed
        stops_dict = pickle.load(file)
     self.setMessage ("Load stoptimes_dict_reversed ...")
     QApplication.processEvents()   
    
     with open(path+'/stoptimes_dict_reversed_pkl.pkl', 'rb') as file: #reversed
        stoptimes_dict = pickle.load(file)
     self.setMessage ("Load rev_idx_by_route_stop ...")
     QApplication.processEvents()   
    
     with open(path+'/rev_idx_by_route_stop.pkl', 'rb') as file:
        idx_by_route_stop_dict = pickle.load(file) 

    
    # для обновления дат в словаре
    #today = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    #today = date.today()
    self.setMessage ("Refreshing date in PKL  ...")   
    QApplication.processEvents()
    
    for key, value in stoptimes_dict.items():
        for subkey, sublist in value.items():
            for index, (number, old_date) in enumerate(sublist):
                updated_date = old_date.replace(year=today.year, month=today.month, day=today.day)
                stoptimes_dict[key][subkey][index] = (number, updated_date)
    
    return stops_dict, stoptimes_dict, footpath_start_dict, footpath_process_dict, footpath_finish_dict, routes_by_stop_dict, \
     idx_by_route_stop_dict




# return postfix for name of filereport
def getDateTime():
  current_datetime = datetime.now()
  year = current_datetime.year
  month = current_datetime.month
  day = current_datetime.day
  hour = current_datetime.hour
  minute = current_datetime.minute
  second = current_datetime.second
  return f'{year}_{month}_{day}_{hour}_{minute}_{second}'

def verify_break (self):
  if self.break_on:
            self.setMessage ("Process raptor is break")
            self.dlg.progressBar.setValue(0)  
            return 1
  return 0

def runRaptorWithProtocol(self, settings, sources, raptor_mode, protocol_type)-> tuple:
  
  count = len(sources)
  self.dlg.progressBar.setMaximum(count + 1)
  self.dlg.progressBar.setValue(0)

  #Maximal_travel_time_int,time_step in seconds
  PathToNetwork,PathToProtocols,NETWORK_NAME,SOURCE,DESTINATION,DESTARR,D_TIME,\
  MAX_TRANSFER,WALKING_FROM_SOURCE, CHANGE_TIME_SEC,\
  MaxTimeTravel,time_step,ExactTransfersCount, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime = \
    getParameters(settings)
  
  
  
  
 
  MaxTimeTravel = timedelta(seconds = int(MaxTimeTravel))
  
  begin_computation_time = datetime.now()
  print(f'begin_computation_time = {begin_computation_time}')

  today = date.today()
  """

  """
  
  if verify_break(self):
      return 0
  QApplication.processEvents()
  stops_dict, stoptimes_dict, footpath_start_dict, footpath_process_dict, footpath_finish_dict,routes_by_stop_dict,\
              idx_by_route_stop_dict = \
              myload_all_dict (self, PathToNetwork, NETWORK_NAME, raptor_mode, today)
  
  
  self.dlg.progressBar.setValue(1)
  
  if verify_break(self):
      return 0


  """
  print (f'mode = {raptor_mode}')
  print("stops_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(stops_dict.items())]))
  
  print("stoptimes_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(stoptimes_dict.items())]))
  
  print("routes_by_stop_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(routes_by_stop_dict.items())]))
  print("idx_by_route_stop_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(idx_by_route_stop_dict.items())]))

  print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_start_dict.items())]))
  print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_process_dict.items())]))
  print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_finish_dict.items())]))
  """ 
   
  time_after_dict_loading = datetime.now()
  print(f'time_after_dict_loading = {time_after_dict_loading}')
  data_retrieving_time = (time_after_dict_loading-begin_computation_time).seconds 

  
  
  reachedLabels = dict()
    
  if protocol_type == 1:
   """Prepare header and time grades  
   statistics_by_accessibility_time_header="Stop_ID,0-10 m,10-20 m,20-30 m,30-40 m,40-50 m,50-60 m"+"\n"+"\n"
   """
   time_step = 300
   intervals_number = round((MaxTimeTravel.total_seconds())/time_step)
   statistics_by_accessibility_time_header = "Source_ID"
   time_step_min = round(time_step/60)
   low_bound_min = 0
   top_bound_min = time_step_min
   grades = []
   for i in range(0, intervals_number):
    statistics_by_accessibility_time_header = statistics_by_accessibility_time_header + ","\
      +str(low_bound_min) + "-" + str(top_bound_min) + " m"
    grades.append ([low_bound_min,top_bound_min])
    low_bound_min = low_bound_min + time_step_min
    top_bound_min = top_bound_min + time_step_min
   statistics_by_accessibility_time_header = statistics_by_accessibility_time_header+"\n"  
   #increase by one the last top bound
   last_top = grades[intervals_number-1][1] + 1
   grades[intervals_number-1][1] = last_top
   
     

  if protocol_type==2:   
   
   ss = "Origin_ID,Start_time"
   ss = ss+",Walk1_time,BStop1_ID,Wait1_time,Bus1_start_time,Line1_ID,Ride1_time,AStop1_ID,Bus1_finish_time"
   ss = ss+",Walk2_time,BStop2_ID,Wait2_time,Bus2_start_time,Line2_ID,Ride2_time,AStop2_ID,Bus2_finish_time"
   ss = ss+",Walk3_time,BStop3_ID,Wait3_time,Bus3_start_time,Line3_ID,Ride3_time,AStop3_ID,Bus3_finish_time"
   ss = ss+",DestWalk_time,Destination_ID,Destination_time"
   if raptor_mode == 2:
     ss = ss+",Arrives before"
   protocol_header = ss+"\n"  

  if protocol_type == 3:
    protocol_header = "Source,Boarding stop,Destination,Boarding,Arrive by bus,Arrival to destination"+"\n"
  protocolExist = False
  #rev_dict=dict() #key: destionation, value: array of sources
  raptor_statistics_from = ""
  
    
  if not protocolExist:
           protocolExist = True
           
           if protocol_type == 1: 
            f = f'{PathToProtocols}\\access_{raptor_mode}_data_{getDateTime()}.csv'
            with open(f, 'w') as filetowrite:
             filetowrite.write(statistics_by_accessibility_time_header)
           if protocol_type == 2:
             f = f'{PathToProtocols}\\access_{raptor_mode}_data_{getDateTime()}.csv'
             with open(f, 'w') as filetowrite:
              filetowrite.write(protocol_header)   
           if protocol_type == 3:  
              f = f'{PathToProtocols}\\raptor_board_arrive_protocol_from_{SOURCE}_maxtime_{MaxTimeTravel/60:.0f}_{getDateTime()}.csv'
              with open(f, 'w') as filetowrite:
               filetowrite.write(protocol_header)  
  
    
 
  

  for i in range(0,count):
          
          print (f'self.break_on {self.break_on}')

          if verify_break(self):
            return 0
          
          self.dlg.progressBar.setValue(i+2)
          self.setMessage(f'Calc {i+1} point from {count}')
          QApplication.processEvents()
          SOURCE, D_TIME = sources[i]

          
          #print(f'runRaptorWithProtocol SOURCE = {SOURCE}')
          if raptor_mode == 1:
           
           output = raptor(SOURCE, DESTINATION, D_TIME, MAX_TRANSFER, WALKING_FROM_SOURCE, CHANGE_TIME_SEC,
                            routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_start_dict, footpath_process_dict, footpath_finish_dict, 
                            idx_by_route_stop_dict,MaxTimeTravel, ExactTransfersCount, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime)
              
           
          else:
            
            output = rev_raptor(SOURCE, DESTINATION, D_TIME, MAX_TRANSFER, WALKING_FROM_SOURCE, CHANGE_TIME_SEC, 
                            routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_start_dict, footpath_process_dict, footpath_finish_dict,
                            idx_by_route_stop_dict,MaxTimeTravel, ExactTransfersCount, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime)
            
            
          # !testing -deleting item with None value on end
            
          #print (f'output {output}')          
          keys_to_remove = [key for key, value in output.items() if value[-1] == (None, None, None, None)]
          #print (f'keys to remove {keys_to_remove}')

          for key in keys_to_remove:
            del output[key]
          
          reachedLabels = output

          #print (f' reachedLabels before report{reachedLabels}')

          #self.setMessage('Creating protokol ...')
          
          # Now write current row   
          if protocol_type == 1:   
            makeRaptorAccessibilityByTimeProtocol(SOURCE, reachedLabels, f, grades) 
          if protocol_type == 2 :           
            make_raptor_statistics_protocol_ext3(raptor_mode, D_TIME, reachedLabels, f)
            
          if protocol_type == 3:
            saveRaptorBoardArriveProtocol(SOURCE, reachedLabels,f)  
          
  
  self.setMessage(f'Calculating done')
  QApplication.processEvents()
  time_after_computation = datetime.now()
  processing_time = (time_after_computation - time_after_dict_loading).seconds
  print(f'time_after_computation = {time_after_computation}')    

 

# for type_protokol = 1 
def makeRaptorAccessibilityByTimeProtocol (SOURCE, dictInput, protocol_full_path, grades):
  
  time_grad = grades
  #[[-1,0], [0,10],[10,20],[20,30],[30,40],[40,50],[50,61] ]
  counts = {x: 0 for x in range(0, len(time_grad))} #counters for grades
  f = protocol_full_path

  #f_verify = "C:/Users/geosimlab/Documents/Igor/Protocols/30-40 135410151.csv"
  #file_verify = open(f_verify, 'w')
  #SOURCE = ""
  with open(f, 'a') as filetowrite:
   for dest, info in dictInput.items():
    #SOURCE = info[0]
    
    #SOURCE = source_inp
    
    #time_to_dest = math.ceil (info[2])
    time_to_dest = int (round(info[2]))
    
    for i in range (0, len(time_grad)) :
     grad = time_grad[i]
     if time_to_dest > grad[0]*60 and time_to_dest <= grad[1]*60:
   #   if i == 0:
   #     file_verify.write(f'{dest}\n')
        
      counts[i] = counts[i] + 1
      break
     
   row = str(SOURCE)  
   for i in range (0, len (time_grad)) :  
    row = f'{row},{counts[i]}'
    #print (f'row {row}')    
   filetowrite.write(row + "\n")
   
  #file_verify.close()
 
# for type_protokol =2 
def  make_raptor_statistics_protocol_ext3(raptor_mode, D_TIME, dictInput, protocol_full_path):
  
  #current_date = date.today()
  #D_TIME = datetime.combine(current_date, D_TIME.time())
  D_TIME = pd.Timestamp(D_TIME)
  
  sep=","
  building_symbol = "b"
  stop_symbol = "s"
  f = protocol_full_path   
  stop_max_number = 50000
  
   
  
  with open(f, 'a') as filetowrite:
   gcounter = 1 # because header is row number 1
   wrong_rows_counter = 0
   list_gcounter_double_walk_adjacent = []

   

   # dictInput - dict from testRaptor
   # every item dictInput : dest - key, info - value 
   #print (f' dictInput.items() {dictInput}')
   for dest, info in dictInput.items():    
    
    SOURCE =  info[0]
    '''
    Examle info[7] = pareto_set =
    [(0, [('walking', 2003, 24206.0, Timedelta('0 days 00:02:47'),Timestamp('2023-06-30 08:37:13')), 
    (Timestamp('2023-06-30 08:36:59'), 24206, 14603, Timestamp('2023-06-30 08:33:36'), '3150_67'), 
    ('walking', 14603, 1976.0, Timedelta('0 days 00:02:03.300000'), Timestamp('2023-06-30 08:31:32.700000'))])]    
    '''
    pareto_set = info[7]
    
    if pareto_set is None or dest is None:
      #print("saveRaptorBoardArriveProtocol dest="+str(dest)+", pareto_set is None ")
      continue
    dest_bus = -1
   
    '''
    Examle jorney
    [('walking', 2003, 24206.0, Timedelta('0 days 00:02:47'), Timestamp('2023-06-30 08:37:13')), 
    (Timestamp('2023-06-30 08:36:59'), 24206, 14603, Timestamp('2023-06-30 08:33:36'), '3150_67'), 
    ('walking', 14603, 1976.0, Timedelta('0 days 00:02:03.300000'), Timestamp('2023-06-30 08:31:32.700000'))]
    '''
    for _, journey in pareto_set: #each journey is array, legs are its elements
         
         # print (f'journey  {journey} ')
         gcounter = gcounter+1
         
         
         # run inversion jorney also raptor_mode = 1

         #print (f'journey {journey}')

         if raptor_mode == 2: 
          # inversion row
          journey = journey[::-1]
          # inversion inside every row
          
          journey = [(tup[0], tup[2], tup[1], tup[3], tup[4]) if tup[0].__class__ != Timestamp else
                            tup[:4][::-1] + (tup[4],) if tup[0].__class__ == Timestamp else tup
                            for tup in journey
                            ]
          """

          for tup in journey:
            if tup[0].__class__ != Timestamp:  # walkikg
              tup = (tup[0], tup[2], tup[1], tup[3], tup[4])
            elif tup[0].__class__ == Timestamp:  # no walking
              tup = tup[:4][::-1] + (tup[4],)
          """
         #print (f'journey {journey}') 

         if raptor_mode == 1:  
          
          journey = [(tup[0], tup[1], tup[2], tup[3], tup[4] - tup[3]) if tup[0] == 'walking' else tup for tup in journey]
           
         #if gcounter == 1:
         #  print (f'journey 1 {journey}')
         #print(f'journey {gcounter-1} {journey} \n')
                   

        #  if gcounter>2:
        #    return
         #print("gcounter="+str(gcounter))
         last_bus_leg = None         
         last_walking_leg = None
         last_leg = None  
         total_walk_time = 0
         
         first_boarding_stop = "" #BStop1_ID
         first_boarding_time = ""         
         first_bus_arrive_stop = "" #AStop1_ID
         first_bus_arrival_time = ""

         second_boarding_stop = ""  #BStop2_ID
         second_boarding_time = ""
         second_bus_arrive_stop = "" #AStop2_ID
         second_bus_arrival_time = ""

         third_boarding_stop = ""  #BStop3_ID
         third_boarding_time = ""
         third_bus_arrive_stop = "" #AStop3_ID
         third_bus_arrival_time = ""

         sfirst_boarding_time = " "
         sfirst_arrive_time = " "
         ssecond_boarding_time = ""
         ssecond_bus_arrival_time = ""
         sthird_boarding_time = ""
         sthird_bus_arrival_time = ""

         first_bus_leg_found = False
         second_bus_leg_found = False
         third_bus_leg_found = False
        
         walk1_time = "" #walk time from orgin to first bus stop or to destination if no buses
         walk1_arriving_time = "" # I need it to compute wait1_time        
         wait1_time = 0         
         line1_id = "" # number of first route (or trip)  
         ride1_time = ""       

         walk2_time = "" # from 1 bus alightning to second bus boarding 
         walk2_arriving_time = ""       
         wait2_time = "" # time between arriving to second bus stop and boarding to the bus
         line2_id = "" # number of second route (or trip)
         ride2_time = ""

         walk3_time = "" # from 2 bus alightning to 3 bus boarding 
         walk3_arriving_time = ""       
         wait3_time = "" # time between arriving to 3 bus stop and boarding to the bus
         line3_id = "" # number of 3 route (or trip)
         ride3_time = ""
        
         walk4_time = ""    
         dest_walk_time = "" # walking time  to destination
         
        
         legs_counter = 0 
         last_leg_type = ""
         walking_counter = 0 # that is what was counter of last walking time (1 for walk1_time..,) 
         ride_counter = 0
         journey_len = len(journey)  
         walking_time_sec = 0 
         #_print_Journey_legs(pareto_set)

         '''
         Examlpe leg
          ('walking', 2003, 24206.0, Timedelta('0 days 00:02:47'), Timestamp('2023-06-30 08:37:13'))
          or
          (Timestamp('2023-06-30 08:36:59'), 24206, 14603, Timestamp('2023-06-30 08:33:36'), '3150_67')


         ''' 
         start_time = None
         
         for leg in journey:
           #if journey[-1][2] == 72011800:
           #  print (f'journey 72011800 {journey}')
         
           # print (f'leg {leg}')            
           legs_counter = legs_counter+1                     
           last_leg = leg
           #  here counting walk(n)_time if leg[0] == 'walking
           #  !!!!! why can walk1_time != "" !!!!!!!!!!!! why verify?
           if leg[0] == 'walking': 
             if last_leg_type == "walking":
              # !counting twice on foot!
              list_gcounter_double_walk_adjacent.append(gcounter)
              #print (journey)
             walking_time_sec = round(leg[3].total_seconds(),1)            
             if ride_counter == 0:
              SOURCE_REV = leg[1] # for backward algo
              if walk1_time == "":
                walk1_time = walking_time_sec
              else:
                 walk1_time = walk1_time + walking_time_sec
                 
              # print (f'leg[4] {leg[4]} leg[3] {leg[3]} ')   
              walk1_arriving_time = leg[4] + leg[3]
             elif ride_counter == 1:
              if walk2_time == "":
                walk2_time= walking_time_sec
              else:
                 walk2_time = walk2_time + walking_time_sec 
                 
              #walk2_arriving_time = leg[4] + leg[3]
              walk2_arriving_time = leg[4] 
              
              
             elif ride_counter == 2:
              if walk3_time == "":
                walk3_time = walking_time_sec 
              else:
                 walk3_time = walk3_time + walking_time_sec 
                 
              walk3_arriving_time = leg[4] - leg[3]
              
             elif ride_counter == 3:
              if walk4_time == "":
                walk4_time = walking_time_sec
              else:
                 walk4_time = walk4_time + walking_time_sec 
                 
              walk4_arriving_time=leg[4] + leg[3]
             # print (f'start_time0 {start_time}')
             if start_time is None:
                 start_time = leg[4]   
             #print (f'start_time0 {start_time}')   
            # here finish counting walk1_time if leg[0] == 'walking           
           else:                       
             if not first_bus_leg_found:
               # in this leg - first leg is bus, saving params for report
               #print (f'start_time1 {start_time}') 
               if start_time is None:
                 start_time = leg[0] 
                 SOURCE_REV = leg[1] # for backward algo
               #print (f'start_time1 {start_time}')   
               first_bus_leg_found = True
               ride_counter = 1
               first_bus_leg=leg
               #if gcounter == 2:
               # print (f'journey {journey}') 
               # print (f'leg {leg}') 
               # print (f'leg[0] {leg[0]}') 
               # print (f'first_boarding_time {first_boarding_time}') 
                
               first_boarding_time = leg[0]
               first_boarding_stop = leg[1]
               first_bus_arrive_stop = leg[2]
               first_bus_arrival_time = leg[3]
               
               ride1_time = round((first_bus_arrival_time - first_boarding_time).total_seconds(),1)
                                             
               if last_leg_type == "walking":
                 wait1_time = round((first_boarding_time - walk1_arriving_time).total_seconds(),1)
               else:
                 #print ('no walking!')
                 #print (f'first_boarding_time {first_boarding_time} start_time {start_time}')

                 if raptor_mode == 1:
                  wait1_time = round((first_boarding_time - D_TIME).total_seconds(),1)
                 else: 
                  wait1_time = round((first_boarding_time - start_time).total_seconds(),1)
                 
                 
               line1_id = leg[4]
               
                                        
             elif not second_bus_leg_found:
               # in this leg - second leg is bus, saving params for report              
               if start_time is None:
                 start_time = leg[0]  
               second_bus_leg_found = True
               ride_counter = 2
               second_boarding_time = leg[0]
               ssecond_boarding_time = str1(second_boarding_time)
               second_boarding_stop = leg[1]
               
               second_bus_arrive_stop = leg[2]
               second_bus_arrival_time = leg[3]
               ssecond_bus_arrival_time = str1(second_bus_arrival_time)               
               
               
               if last_leg_type == "walking":
                 wait2_time = round((second_boarding_time - first_bus_arrival_time - timedelta(seconds=walk2_time)).total_seconds(),1)
               else:
                wait2_time = round((second_boarding_time - first_bus_arrival_time).total_seconds(),1) 

              



               line2_id = leg[4]    
               ride2_time = round((second_bus_arrival_time - second_boarding_time).total_seconds(),1)
               
             else: #3-rd bus found 
               third_bus_leg_found = True
               # in this leg - third leg is bus, saving params for report               
               if start_time is None:
                 start_time = leg[0]  
               ride_counter = 3            
               third_boarding_time = leg[0]
               sthird_boarding_time = str1(third_boarding_time) 
               third_boarding_stop = leg[1]               
               third_bus_arrive_stop = leg[2]
               third_bus_arrival_time = leg[3]
               sthird_bus_arrival_time = str1 (third_bus_arrival_time)
               #print (f' third_boarding_time {third_boarding_time} second_bus_arrival_time {second_bus_arrival_time} walk3_time {walk3_time}')
               if last_leg_type == "walking":
                 wait3_time = round((third_boarding_time - second_bus_arrival_time - timedelta(seconds=walk3_time)).total_seconds(),1)               
               else:
                 wait3_time = round((third_boarding_time - second_bus_arrival_time).total_seconds(),1)     
                 
               line3_id = leg[4]    
               ride3_time = round((third_bus_arrival_time - third_boarding_time).total_seconds(),1) 
                 
             last_bus_leg = leg

           last_leg_type = leg[0] #in current journey
           
           # this legs finish, postprocessing this journey
         if last_leg_type == "walking":
            if walk4_time != "":
             dest_walk_time = walk4_time
             walk4_time = ""
            elif walk3_time != "":
             dest_walk_time = walk3_time
             walk3_time = ""
            elif walk2_time != "":
             dest_walk_time = walk2_time
             walk2_time="" 
            elif walk1_time != "":
             dest_walk_time = walk1_time
             walk1_time="" 
         
           
        #end of cycle by legs
        # Calculate waiting time before boarding
          
        #If first_bus_leg and last_bus_leg are found
        #they may be the same leg
        #get boarding_time from first_bus_leg         
         sfirst_boarding_stop = ""
         sfirst_arrive_stop = ""            
         sline1_id = ""        
         sride1_time = ""

         ssecond_boarding_stop = ""                  
         ssecond_arrive_stop = ""
         sline2_id = ""
         sride2_time = ""

         sthird_boarding_stop = ""                  
         sthird_arrive_stop = ""
         sline3_id = ""
         sride3_time = ""

         # last_bus_leg - last leg of current jorney
         if not last_bus_leg is None: # work forever?                    
          first_boarding_stop_orig = first_boarding_stop
          first_bus_arrive_stop_orig = first_bus_arrive_stop
          sfirst_boarding_stop = stop_symbol + str(first_boarding_stop_orig)
          sfirst_arrive_stop = stop_symbol+ str(first_bus_arrive_stop_orig)          
          sline1_id = str(line1_id)
          sride1_time = str(ride1_time)
          sfirst_boarding_time = str1(first_boarding_time)
          sfirst_arrive_time = str1(first_bus_arrival_time)
        
          
          if second_bus_leg_found:
           second_boarding_stop_orig = second_boarding_stop
           second_bus_arrive_stop_orig = second_bus_arrive_stop
           ssecond_boarding_stop = stop_symbol + str(second_boarding_stop_orig)
           ssecond_arrive_stop = stop_symbol+ str(second_bus_arrive_stop_orig)          
           sline2_id = str(line2_id)
           sride2_time = str(ride2_time)         
          if third_bus_leg_found:
           third_boarding_stop_orig = third_boarding_stop
           third_bus_arrive_stop_orig = third_bus_arrive_stop
           sthird_boarding_stop = stop_symbol + str(third_boarding_stop_orig)
           sthird_arrive_stop = stop_symbol+ str(third_bus_arrive_stop_orig)          
           sline3_id = str(line3_id)
           sride3_time = str(ride3_time)      
         #Define what was mode of the last leg:          
         Destination = leg[2]  #here leg is the last leg that was in previous cycle        
         
         #if gcounter == 2:
         # print (f'first_boarding_time {first_boarding_time} sfirst_boarding_time {sfirst_boarding_time}')
         # print (f'ssecond_boarding_time {second_boarding_time} ssecond_boarding_time {ssecond_boarding_time}')
         # print (f'third_boarding_time {third_boarding_time} sthird_boarding_time {sthird_boarding_time}')

         #destination_type = "S"
         if Destination > stop_max_number:
           destination_type = building_symbol
         else:
           destination_type = stop_symbol  


         if SOURCE > stop_max_number:
           symbol1 = building_symbol
         else:
           symbol1 = stop_symbol

         
         if raptor_mode == 1:
            if SOURCE > stop_max_number:
              symbol1 = building_symbol
            else:
              symbol1 = stop_symbol   
              
         if raptor_mode == 2:
            if SOURCE_REV > stop_max_number:
              symbol1 = building_symbol
            else:
              symbol1 = stop_symbol   
          

         if last_leg[0] == 'walking':
          
          arrival_time = last_leg[4] + last_leg[3]
         else:       
          
          arrival_time = last_leg[3]
          
         sarrival_time = str1(arrival_time)

         if  destination_type == stop_symbol:
          orig_dest = Destination
         else:
           orig_dest = Destination 

        
         #check destination time vs wait, walking and ride times
         total_journey_time1 = int1(walk1_time) + int1(wait1_time) + int1(ride1_time) + int1(walk2_time)+\
         int1(wait2_time) + int1(ride2_time) + int1(wait3_time) + int1(ride3_time) + int1(walk3_time) + int1(dest_walk_time)
         total_journey_time2 = (arrival_time - D_TIME).total_seconds()
                  
         difference =  math.fabs(total_journey_time1 - total_journey_time2) 
         if  difference > 10:
            #print(f'wrong gcounter {gcounter} difference={difference}')
            #print(f'orig_dest = {destination_type}{orig_dest}')
            #_print_Journey_legs (pareto_set)
            wrong_rows_counter = wrong_rows_counter+1
         #_print_Journey_legs(pareto_set)   
        
         if walk1_time == "":
             walk1_time = 0 

         if dest_walk_time == "":
             dest_walk_time = 0  
         
         if raptor_mode == 1:
                      
           row = f'{symbol1}{SOURCE}{sep}{str1(D_TIME)}{sep}{walk1_time}{sep}{sfirst_boarding_stop}\
            {sep}{wait1_time}{sep}{sfirst_boarding_time}{sep}{sline1_id}{sep}{sride1_time}{sep}{sfirst_arrive_stop}{sep}{sfirst_arrive_time}\
            {sep}{walk2_time}{sep}{ssecond_boarding_stop}{sep}{wait2_time}{sep}{ssecond_boarding_time}{sep}{sline2_id}{sep}{sride2_time}{sep}{ssecond_arrive_stop}{sep}{ssecond_bus_arrival_time}\
            {sep}{walk3_time}{sep}{sthird_boarding_stop}{sep}{wait3_time}{sep}{sthird_boarding_time}{sep}{sline3_id}{sep}{sride3_time}{sep}{sthird_arrive_stop}{sep}{sthird_bus_arrival_time}\
            {sep}{dest_walk_time}{sep}{destination_type}{orig_dest}{sep}{sarrival_time}'
         else:


           
           row = f'{symbol1}{SOURCE_REV}{sep}{str1(start_time)}{sep}{walk1_time}{sep}{sfirst_boarding_stop}\
            {sep}{wait1_time}{sep}{sfirst_boarding_time}{sep}{sline1_id}{sep}{sride1_time}{sep}{sfirst_arrive_stop}{sep}{sfirst_arrive_time}\
            {sep}{walk2_time}{sep}{ssecond_boarding_stop}{sep}{wait2_time}{sep}{ssecond_boarding_time}{sep}{sline2_id}{sep}{sride2_time}{sep}{ssecond_arrive_stop}{sep}{ssecond_bus_arrival_time}\
            {sep}{walk3_time}{sep}{sthird_boarding_stop}{sep}{wait3_time}{sep}{sthird_boarding_time}{sep}{sline3_id}{sep}{sride3_time}{sep}{sthird_arrive_stop}{sep}{sthird_bus_arrival_time}\
            {sep}{dest_walk_time}{sep}{destination_type}{SOURCE}{sep}{sarrival_time}{sep}{str1(D_TIME)}' 

               
         filetowrite.write(row +"\n")
         
  print(f'wrong rows counter = {wrong_rows_counter}')
  if len(list_gcounter_double_walk_adjacent) > 0: 
   print("Numbers of lines with 2 adjacent walks") 
   for i in list_gcounter_double_walk_adjacent:
    print(f'gcounter = {i}')
                  

# def is_stop_id(id):
#   result=False
#   stop_max_number=2000
#   special_ids=[654,659,759]
#   if id<stop_max_number or id in special_ids:
#    result=True
#   return result 
def int1(s):
  result = s
  if s == "":
   result = 0
  return result 

"""
Here we get output from raptor from one source and many destinations.
We want to save in protocol only such destinations that were arrived by bus
"""
def saveRaptorBoardArriveProtocol(Source, dictInput,PathToProtocols):
    sep=","        
    #header="Source,Destination,Boarding time,Arrive by bus time"+"\n"
    boarding_stop=""
    Destination=""
    with open(PathToProtocols, 'a') as filetowrite:
      #filetowrite.write(header)
     dictDestinations=dict()
     for dest, info in dictInput.items():
      
      pareto_set=info[7]
      if pareto_set is None or dest is None:
        #print("saveRaptorBoardArriveProtocol dest="+str(dest)+", pareto_set is None ")
        continue
      dest_bus=-1
      for transfers, journey in pareto_set: #each journey is array, legs are its elements
         first_bus_leg=None
         last_bus_leg=None
         last_walking_leg=None
         boarding_time=-1
         boarding_stop=-1
         bus_arrive_time=-1
         bus_arrive_stop=-1
         arrival_time=-1
         first_bus_leg_found=False
         last_walking_leg_found=False
         
         for leg in journey:
           #search last bus leg 
           if leg[0] == 'walking':
             if not last_walking_leg_found:
               last_walking_leg_found=True
             last_walking_leg=leg           
           else:
             if not first_bus_leg_found:
               first_bus_leg_found=True
               first_bus_leg=leg                             
             last_bus_leg=leg
            
        #now we suppose that first_bus_leg and last_bus_leg are found
        #It may be the same leg
        #get boarding_time from first_bus_leg
         if not last_bus_leg is None:
          boarding_stop=first_bus_leg[1]
          Destination=last_bus_leg[2]
          boarding_time=first_bus_leg[0]
          bus_arrive_time=last_bus_leg[3]
          bus_arrive_stop=last_bus_leg[4]
          sboarding_stop=str(boarding_stop)
          sbus_arrive_stop=str(bus_arrive_stop)
          sboarding_time=str1(boarding_time)
          sbus_arrive_time=str1(bus_arrive_time)
         else:         
          Destination= last_walking_leg[2]
          sboarding_time="" 
          sbus_arrive_time=""
          sboarding_stop=""
         #Define what was mode of the last leg:          
         if leg[0] == 'walking':
          arrival_time= str1(leg[4])
         else:
          arrival_time= str1(leg[3])
        
         row=str(Source)+sep+sboarding_stop+sep+str(Destination)+sep+ sboarding_time\
         +sep+sbus_arrive_time+sep+arrival_time+"\n"
         filetowrite.write(row)     



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

"""
Goal: check that revraptor gives the same time of drive as raptor gives
for some sources and destinations
Input: file raptor_board_arrive_protocol.csv that contains rows with fields
Source,	Destination,	Boarding time,	Arrive by bus time
computing by raptor for som max travel time
Algorithm:
 for each row with (Source,	Destination,Boarding time,	Arrive by bus time) in the file 
 run revraptor for (Destination,Source) and boarding time=Arrive by bus time and check
 that arrive time = Boarding time
"""
