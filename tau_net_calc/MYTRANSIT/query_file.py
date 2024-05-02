
import os
import zipfile
from datetime import datetime, timedelta, date

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsProject, QgsVectorFileWriter

from RAPTOR.std_raptor import raptor
from RAPTOR.rev_std_raptor import rev_raptor

# # Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

def time_to_seconds(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    total_seconds = hours * 3600 + minutes * 60 + seconds
    return total_seconds

def seconds_to_time(total_seconds):
    total_seconds = round(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    time_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    return time_str

def myload_all_dict(self, PathToNetwork, mode):
    """
    Args:
        PathToNetwork (str): network NETWORK_NAME.
        

    Returns:
        stops_dict (dict): preprocessed dict. Format {route_id: [ids of stops in the route]}.
        stoptimes_dict (dict): keys: route ID, values: list of trips in the increasing order of start time. Format-> dict[route_ID] = [trip_1, trip_2] where trip_1 = [(stop id, arrival time), (stop id, arrival time)]
        footpath_dict (dict): preprocessed dict. Format {from_stop_id: [(to_stop_id, footpath_time)]}.
        routes_by_stop_dict (dict): preprocessed dict. Format {stop_id: [id of routes passing through stop]}.
        idx_by_route_stop_dict (dict): preprocessed dict. Format {(route id, stop id): stop index in route}.
        
    """
    import pickle
    
    path = PathToNetwork
    
    self.setMessage ("Load transfers ...")        
    with open(path+'/transfers_dict.pkl', 'rb') as file:
        footpath_dict = pickle.load(file)
    QApplication.processEvents()
    self.progressBar.setValue(1)

       
    self.setMessage ("Load routes_by_stop ...")
    with open(path+'/routes_by_stop.pkl', 'rb') as file:
        routes_by_stop_dict = pickle.load(file)
    QApplication.processEvents()
    self.progressBar.setValue(2)
    
    if mode == 1:
      self.setMessage ("Load stops ...")
      with open(path+'/stops_dict_pkl.pkl', 'rb') as file:
        stops_dict = pickle.load(file)
      QApplication.processEvents()
      self.progressBar.setValue(3)

      self.setMessage ("Load stoptimes ...")
      with open(path+'/stoptimes_dict_pkl.pkl', 'rb') as file:
        stoptimes_dict = pickle.load(file)
      QApplication.processEvents()
      self.progressBar.setValue(4)

      self.setMessage ("Load idx_by_route_stop ...")
      with open(path+'/idx_by_route_stop.pkl', 'rb') as file:
        idx_by_route_stop_dict = pickle.load(file)
      QApplication.processEvents()
      self.progressBar.setValue(5)
          
    else:
     self.setMessage ("Load stops_reversed ...")
     with open(path+'/stops_dict_reversed_pkl.pkl', 'rb') as file:  #reversed
        stops_dict = pickle.load(file)
     QApplication.processEvents()
     self.progressBar.setValue(3)   

     self.setMessage ("Load stoptimes_reversed ...")
     with open(path+'/stoptimes_dict_reversed_pkl.pkl', 'rb') as file: #reversed
        stoptimes_dict = pickle.load(file)
     QApplication.processEvents()      
     self.progressBar.setValue(4)
     
     
     self.setMessage ("Load rev_idx_by_route_stop ...")
     with open(path+'/rev_idx_by_route_stop.pkl', 'rb') as file:
        idx_by_route_stop_dict = pickle.load(file) 
     QApplication.processEvents()   
     self.progressBar.setValue(5)
    
    return stops_dict, stoptimes_dict, footpath_dict, routes_by_stop_dict, idx_by_route_stop_dict

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

def verify_break (self, Layer= "", LayerDest= "", curr_getDateTime = "", folder_name = "", ):
  if self.break_on:
            self.setMessage ("Process raptor is break")
            self.textLog.append (f'<a><b><font color="red">Process raptor is break</font> </b></a>')
            if folder_name !="":
              write_info (self,Layer, LayerDest, curr_getDateTime, folder_name)  
            self.progressBar.setValue(0)  
            return True
  return False

def runRaptorWithProtocol(self, sources, raptor_mode, protocol_type)-> tuple:

  
  count = len(sources)
  self.progressBar.setMaximum(count + 5)
  self.progressBar.setValue(0)

  
  PathToNetwork = self.config['Settings']['PathToPKL']
  PathToProtocols = self.config['Settings']['PathToProtocols']
  D_TIME = time_to_seconds(self.config['Settings']['TIME'])
  
  MAX_TRANSFER = int (self.config['Settings']['Max_transfer'])
  MIN_TRANSFER = int (self.config['Settings']['Min_transfer'])
  
  Speed = float(self.config['Settings']['Speed'].replace(',', '.')) * 1000 / 3600                    # from km/h to m/sec

  MaxWalkDist1 = int(self.config['Settings']['MaxWalkDist1'])/Speed          # dist to time
  MaxWalkDist2 = int(self.config['Settings']['MaxWalkDist2'])/Speed          # dist to time
  MaxWalkDist3 = int(self.config['Settings']['MaxWalkDist3'])/Speed          # dist to time

  MaxTimeTravel = float(self.config['Settings']['MaxTimeTravel'].replace(',', '.'))*60           # to sec
  MaxWaitTime = float(self.config['Settings']['MaxWaitTime'].replace(',', '.'))*60               # to sec
  MaxWaitTimeTransfer= float(self.config['Settings']['MaxWaitTimeTranfer'].replace(',', '.'))*60 # to sec 
  
  CHANGE_TIME_SEC = int(self.change_time)
  time_step = int (self.config['Settings']['TimeInterval'])
  Layer = self.config['Settings']['Layer']

  UseField = self.config['Settings']['UseField'] == "True"
  Field = self.config['Settings']['Field']
  LayerDest = self.config['Settings']['LayerDest']

  if protocol_type == 2:
    UseField = False
  
  begin_computation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  
  self.textLog.append(f'<a>Algorithm started at {begin_computation_time}</a>')

  today = date.today()
  
  
  if verify_break(self):
      return 0
  QApplication.processEvents()
  stops_dict, stoptimes_dict, footpath_dict, routes_by_stop_dict,\
              idx_by_route_stop_dict = \
              myload_all_dict (self, PathToNetwork, raptor_mode)
        
  if verify_break(self):
      return 0

  """
  print (f'mode = {raptor_mode}')
  print("stops_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(stops_dict.items())]))
  """
  #print("stoptimes_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(stoptimes_dict.items())]))
  """
  print("routes_by_stop_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(routes_by_stop_dict.items())]))
  print("idx_by_route_stop_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(idx_by_route_stop_dict.items())]))

  print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_start_dict.items())]))
  print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_process_dict.items())]))
  print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_finish_dict.items())]))
  """ 
      
  self.textLog.append(f'<a>Loading dictionary done</a>')
  self.textLog.append(f'<a>Starting calculating</a>')
   
  
  reachedLabels = dict()


  layers_dest = QgsProject.instance().mapLayersByName(LayerDest)
  layer_dest = layers_dest[0]
  
  attribute_dict = {}
  if UseField:
        
    fields = layer_dest.fields()
    first_field_name = fields[0].name()
    
    for feature in layer_dest.getFeatures():
        if isinstance(feature[Field], int) or (isinstance(feature[Field], str) and feature[Field].isdigit()):
          attribute_dict[int(feature[first_field_name])] = int(feature[Field])
        else:
          self.textLog.append (f'<a><b><font color="red"> WARNING: type of field "{Field}" to aggregate  is no digital, aggregate no run</font> </b></a>')
          UseField = False
          break
    
  if protocol_type == 1:
   """Prepare header and time grades  
   statistics_by_accessibility_time_header="Stop_ID,0-10 m,10-20 m,20-30 m,30-40 m,40-50 m,50-60 m"+"\n"+"\n"
   """
   intervals_number = round(MaxTimeTravel/(time_step*60))
   
   protocol_header = "Source_ID"
   time_step_min = time_step
   low_bound_min = 0
   top_bound_min = time_step_min
   grades = []
   for i in range(0, intervals_number):
    protocol_header +=  f',{low_bound_min}-{top_bound_min} m'
    
    if UseField:
      protocol_header += f', sum({Field})'
    grades.append ([low_bound_min,top_bound_min])
    low_bound_min = low_bound_min + time_step_min
    top_bound_min = top_bound_min + time_step_min
   protocol_header += '\n'  
   #increase by one the last top bound
   last_top = grades[intervals_number-1][1] + 1
   grades[intervals_number-1][1] = last_top
   
  if protocol_type==2:   
   
   ss = "Origin_ID,Start_time"
   ss += ",Walk1_time,BStop1_ID,Wait1_time,Bus1_start_time,Line1_ID,Ride1_time,AStop1_ID,Bus1_finish_time"
   ss += ",Walk2_time,BStop2_ID,Wait2_time,Bus2_start_time,Line2_ID,Ride2_time,AStop2_ID,Bus2_finish_time"
   ss += ",Walk3_time,BStop3_ID,Wait3_time,Bus3_start_time,Line3_ID,Ride3_time,AStop3_ID,Bus3_finish_time"
   ss += ",DestWalk_time,Destination_ID,Destination_time"
   if raptor_mode == 2:
     ss += ",Arrives before"
   protocol_header = ss+"\n"  

  curr_getDateTime = getDateTime()
  folder_name = f'{PathToProtocols}//{curr_getDateTime}'

  if not os.path.exists(folder_name):
    os.makedirs(folder_name)
  else:
    return 0
  
    
  f = f'{folder_name}//access_{curr_getDateTime}.csv'
  with open(f, 'w') as filetowrite:
      filetowrite.write(protocol_header)   
        
 
  total_time1 = timedelta()
  total_time2 = timedelta()
  total_time3 = timedelta()
  total_time4 = timedelta()
  total_time5 = timedelta()
  total_time6 = timedelta()
    
  for i in range(0,count):
          
          if verify_break(self, Layer, LayerDest, curr_getDateTime, folder_name):
            return 0
          
          self.progressBar.setValue(i + 6)
          self.setMessage(f'Calc point №{i+1} from {count}')
          QApplication.processEvents()
          SOURCE, D_TIME = sources[i]
         
          
          if raptor_mode == 1:
           
           output, time1, time2, time3, time4, time5, time6  = raptor(SOURCE, D_TIME, MAX_TRANSFER, MIN_TRANSFER, CHANGE_TIME_SEC,
                            routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_dict,  
                            idx_by_route_stop_dict,MaxTimeTravel, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime, MaxWaitTimeTransfer)
           
           total_time1 += time1
           total_time2 += time2
           total_time3 += time3
           total_time4 += time4
           total_time5 += time5
           total_time6 += time6
           
          else:
            
            output = rev_raptor(SOURCE, D_TIME, MAX_TRANSFER, MIN_TRANSFER, CHANGE_TIME_SEC, 
                            routes_by_stop_dict, stops_dict, stoptimes_dict, footpath_dict, 
                            idx_by_route_stop_dict,MaxTimeTravel, MaxWalkDist1, MaxWalkDist2, MaxWalkDist3, MaxWaitTime,MaxWaitTimeTransfer)
            
            
          # !testing -deleting item with None value on end
                 
          keys_to_remove = [key for key, value in output.items() if value[-1] == (None, None, None, None)]

          for key in keys_to_remove:
            del output[key]
          
          reachedLabels = output
          
          # Now write current row   
          if protocol_type == 1:   
            make_protocol_summary(SOURCE, reachedLabels, f, grades, UseField, attribute_dict) 
          if protocol_type == 2 :           
            make_protocol_detailed(raptor_mode, D_TIME, reachedLabels, f)
           
                 
  #print (f'total_time1 {total_time1}')
  #print (f'total_time2 {total_time2}')
  #print (f'total_time3 {total_time3}')
  #print (f'total_time4 {total_time4}')
  #print (f'total_time5 {total_time5}')
  #print (f'total_time6 {total_time6}') 


  

  self.setMessage(f'Calculating done')
  QApplication.processEvents()
  time_after_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  self.textLog.append(f'<a>Time after computation {time_after_computation}</a>')  

  write_info (self, Layer, LayerDest, curr_getDateTime, folder_name)
  

def write_info (self,Layer, LayerDest, curr_getDateTime, folder_name):
  text = self.textLog.toPlainText()
  filelog_name = f'{folder_name}//log_{curr_getDateTime}.txt'
  with open(filelog_name, "w") as file:
    file.write(text)

  zip_filename1 = f'{folder_name}//origins_{Layer}_{curr_getDateTime}.zip'
  filename1 = f'{folder_name}//origins_{Layer}_{curr_getDateTime}.geojson'
  zip_filename2 = f'{folder_name}//destinations_{LayerDest}_{curr_getDateTime}.zip'
  filename2 = f'{folder_name}//destinations_{LayerDest}_{curr_getDateTime}.geojson'
  save_layer_to_zip(Layer, zip_filename1, filename1)
  if Layer != LayerDest: 
    save_layer_to_zip(LayerDest, zip_filename2, filename2)  
  
  self.textLog.append(f'<a href="file:///{folder_name}" target="_blank" >Output in folder</a>')  
  

# for type_protokol = 1 
def make_protocol_summary (SOURCE, dictInput, f, grades, use_fields, attribute_dict):
  
  time_grad = grades
  #[[-1,0], [0,10],[10,20],[20,30],[30,40],[40,50],[50,61] ]
  counts = {x: 0 for x in range(0, len(time_grad))} #counters for grades
  agrregates = {x: 0 for x in range(0, len(time_grad))} #counters for agrregates
  
 
  with open(f, 'a') as filetowrite:
   for dest, info in dictInput.items():

    time_to_dest = int (round(info[2]))
    
    for i in range (0, len(time_grad)) :
     grad = time_grad[i]
     if time_to_dest > grad[0]*60 and time_to_dest <= grad[1]*60:
      counts[i] = counts[i] + 1
      if use_fields:
        
        agrregates[i] = agrregates[i] + attribute_dict.get(int(dest), 0)

      break
     
   row = str(SOURCE)  
   for i in range (0, len (time_grad)) :  
    row = f'{row},{counts[i]}'
    if use_fields:
      row = f'{row},{agrregates[i]}'
   filetowrite.write(row + "\n")
   
 
# for type_protokol =2 
def  make_protocol_detailed(raptor_mode, D_TIME, dictInput, protocol_full_path):
  
  sep=","
  building_symbol = "b"
  stop_symbol = "s"
  f = protocol_full_path   
  stop_max_number = 50000
    
  with open(f, 'a') as filetowrite:
   gcounter = 1 # because header is row number 1
   
   list_gcounter_double_walk_adjacent = []

   

   # dictInput - dict from testRaptor
   # every item dictInput : dest - key, info - value 
   
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
      
      continue
    
   
    '''
    Examle jorney
    [('walking', 2003, 24206.0, Timedelta('0 days 00:02:47'), Timestamp('2023-06-30 08:37:13')), 
    (Timestamp('2023-06-30 08:36:59'), 24206, 14603, Timestamp('2023-06-30 08:33:36'), '3150_67'), 
    ('walking', 14603, 1976.0, Timedelta('0 days 00:02:03.300000'), Timestamp('2023-06-30 08:31:32.700000'))]
    '''
    for _, journey in pareto_set: #each journey is array, legs are its elements
         
         
         gcounter = gcounter+1
         
         
         # run inversion jorney also raptor_mode = 1

         

         if raptor_mode == 2: 
          # inversion row
          journey = journey[::-1]
          # inversion inside every row
          
          #journey = [(tup[0], tup[2], tup[1], tup[3], tup[4]) if tup[0].__class__ != Timestamp else
          #                  tup[:4][::-1] + (tup[4],) if tup[0].__class__ == Timestamp else tup
          #                  for tup in journey
          #                  ]
          
          journey = [(tup[0], tup[2], tup[1], tup[3], tup[4]) if not isinstance(tup[0], int) else
           tup[:4][::-1] + (tup[4],) if isinstance(tup[0], int) else tup
           for tup in journey
          ] 

         if raptor_mode == 1:  
          
          journey = [(tup[0], tup[1], tup[2], tup[3], tup[4] - tup[3]) if tup[0] == 'walking' else tup for tup in journey]
           
                   

         last_bus_leg = None         
         
         last_leg = None  
         
         
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
         
         wait2_time = "" # time between arriving to second bus stop and boarding to the bus
         line2_id = "" # number of second route (or trip)
         ride2_time = ""

         walk3_time = "" # from 2 bus alightning to 3 bus boarding 
         
         wait3_time = "" # time between arriving to 3 bus stop and boarding to the bus
         line3_id = "" # number of 3 route (or trip)
         ride3_time = ""
        
         walk4_time = ""    
         dest_walk_time = "" # walking time  to destination
                 
         legs_counter = 0 
         last_leg_type = ""
         ride_counter = 0
         walking_time_sec = 0 
         

         '''
         Examlpe leg
          ('walking', 2003, 24206.0, Timedelta('0 days 00:02:47'), Timestamp('2023-06-30 08:37:13'))
          or
          (Timestamp('2023-06-30 08:36:59'), 24206, 14603, Timestamp('2023-06-30 08:33:36'), '3150_67')


         ''' 
         start_time = None
         
         for leg in journey:
           
           legs_counter = legs_counter+1                     
           last_leg = leg
           #  here counting walk(n)_time if leg[0] == 'walking
           #  !!!!! why can walk1_time != "" !!!!!!!!!!!! why verify?
           if leg[0] == 'walking': 
             if last_leg_type == "walking":
              # !counting twice on foot!
              list_gcounter_double_walk_adjacent.append(gcounter)
              
             
             walking_time_sec = round(leg[3],1)            
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
             
             if start_time is None:
                 start_time = leg[4]   
             
            # here finish counting walk1_time if leg[0] == 'walking           
           else:                       
             if not first_bus_leg_found:
               # in this leg - first leg is bus, saving params for report
               
               if start_time is None:
                 start_time = leg[0] 
                 SOURCE_REV = leg[1] # for backward algo
               
               first_bus_leg_found = True
               ride_counter = 1
               first_bus_leg=leg
               
                
               first_boarding_time = leg[0]
               first_boarding_stop = leg[1]
               first_bus_arrive_stop = leg[2]
               first_bus_arrival_time = leg[3]
               
               
               ride1_time = round((first_bus_arrival_time - first_boarding_time),1)
                                             
               if last_leg_type == "walking":
                 
                 wait1_time = round((first_boarding_time - walk1_arriving_time),1)
               else:
                 
                 if raptor_mode == 1:
                  
                  wait1_time = round((first_boarding_time - D_TIME),1)
                 else: 
                  
                  wait1_time = round((first_boarding_time - start_time),1)
                 
                 
               line1_id = leg[4]
               
                                        
             elif not second_bus_leg_found:
               # in this leg - second leg is bus, saving params for report              
               if start_time is None:
                 start_time = leg[0]  
               second_bus_leg_found = True
               ride_counter = 2
               second_boarding_time = leg[0]
               ssecond_boarding_time = seconds_to_time(second_boarding_time)
               second_boarding_stop = leg[1]
               
               second_bus_arrive_stop = leg[2]
               second_bus_arrival_time = leg[3]
               ssecond_bus_arrival_time = seconds_to_time(second_bus_arrival_time)               
               
               
               if last_leg_type == "walking":
               
                 wait2_time = round((second_boarding_time - first_bus_arrival_time - walk2_time),1)
               else:
               
                wait2_time = round((second_boarding_time - first_bus_arrival_time),1) 

               line2_id = leg[4]    
               
               ride2_time = round((second_bus_arrival_time - second_boarding_time),1)
               
             else: #3-rd bus found 
               third_bus_leg_found = True
               # in this leg - third leg is bus, saving params for report               
               if start_time is None:
                 start_time = leg[0]  
               ride_counter = 3            
               third_boarding_time = leg[0]
               sthird_boarding_time = seconds_to_time(third_boarding_time) 
               third_boarding_stop = leg[1]               
               third_bus_arrive_stop = leg[2]
               third_bus_arrival_time = leg[3]
               sthird_bus_arrival_time = seconds_to_time (third_bus_arrival_time)
               
               if last_leg_type == "walking":
                 
                 wait3_time = round((third_boarding_time - second_bus_arrival_time - walk3_time),1)               
               else:
                 
                 wait3_time = round((third_boarding_time - second_bus_arrival_time),1)     
                 
               line3_id = leg[4]    
               
               ride3_time = round((third_bus_arrival_time - third_boarding_time),1) 
                 
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
          sfirst_boarding_stop = f'{stop_symbol}{first_boarding_stop_orig}'
          sfirst_arrive_stop = f'{stop_symbol}{first_bus_arrive_stop_orig}'         
          
          
          sfirst_boarding_time = seconds_to_time(first_boarding_time)
          sfirst_arrive_time = seconds_to_time(first_bus_arrival_time)
        
          
          if second_bus_leg_found:
           second_boarding_stop_orig = second_boarding_stop
           second_bus_arrive_stop_orig = second_bus_arrive_stop
           ssecond_boarding_stop = f'{stop_symbol}{second_boarding_stop_orig}'
           ssecond_arrive_stop = f'{stop_symbol}{second_bus_arrive_stop_orig}'
                 

          if third_bus_leg_found:
           third_boarding_stop_orig = third_boarding_stop
           third_bus_arrive_stop_orig = third_bus_arrive_stop
           sthird_boarding_stop = f'{stop_symbol}{third_boarding_stop_orig}'
           sthird_arrive_stop = f'{stop_symbol}{third_bus_arrive_stop_orig}'
                 
         #Define what was mode of the last leg:          
         Destination = leg[2]  #here leg is the last leg that was in previous cycle        
         
        
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
         
         sarrival_time = seconds_to_time(arrival_time)

         if  destination_type == stop_symbol:
          orig_dest = Destination
         else:
          orig_dest = Destination 

        
        
         if walk1_time == "":
             walk1_time = 0 

         if dest_walk_time == "":
             dest_walk_time = 0  
         
         if raptor_mode == 1:
                      
           row = f'{symbol1}{SOURCE}{sep}{seconds_to_time(D_TIME)}{sep}{walk1_time}{sep}{sfirst_boarding_stop}\
            {sep}{wait1_time}{sep}{sfirst_boarding_time}{sep}{line1_id}{sep}{ride1_time}{sep}{sfirst_arrive_stop}{sep}{sfirst_arrive_time}\
            {sep}{walk2_time}{sep}{ssecond_boarding_stop}{sep}{wait2_time}{sep}{ssecond_boarding_time}{sep}{line2_id}{sep}{ride2_time}{sep}{ssecond_arrive_stop}{sep}{ssecond_bus_arrival_time}\
            {sep}{walk3_time}{sep}{sthird_boarding_stop}{sep}{wait3_time}{sep}{sthird_boarding_time}{sep}{line3_id}{sep}{ride3_time}{sep}{sthird_arrive_stop}{sep}{sthird_bus_arrival_time}\
            {sep}{dest_walk_time}{sep}{destination_type}{orig_dest}{sep}{sarrival_time}'
         else:


           
           row = f'{symbol1}{SOURCE_REV}{sep}{seconds_to_time(start_time)}{sep}{walk1_time}{sep}{sfirst_boarding_stop}\
            {sep}{wait1_time}{sep}{sfirst_boarding_time}{sep}{line1_id}{sep}{ride1_time}{sep}{sfirst_arrive_stop}{sep}{sfirst_arrive_time}\
            {sep}{walk2_time}{sep}{ssecond_boarding_stop}{sep}{wait2_time}{sep}{ssecond_boarding_time}{sep}{line2_id}{sep}{ride2_time}{sep}{ssecond_arrive_stop}{sep}{ssecond_bus_arrival_time}\
            {sep}{walk3_time}{sep}{sthird_boarding_stop}{sep}{wait3_time}{sep}{sthird_boarding_time}{sep}{line3_id}{sep}{ride3_time}{sep}{sthird_arrive_stop}{sep}{sthird_bus_arrival_time}\
            {sep}{dest_walk_time}{sep}{destination_type}{SOURCE}{sep}{sarrival_time}{sep}{seconds_to_time(D_TIME)}' 

               
         filetowrite.write(row +"\n")
         
                    

 
def int1(s):
  result = s
  if s == "":
   result = 0
  return result

def save_layer_to_zip(layer_name, zip_filename, filename):
    layer = QgsProject.instance().mapLayersByName(layer_name)[0]
    temp_file = "temp_layer_file.geojson"
    
    QgsVectorFileWriter.writeAsVectorFormat(layer, temp_file, "utf-8", layer.crs(), "GeoJSON")
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
      zipf.write(temp_file, os.path.basename(filename))
    os.remove(temp_file)   
    
    
     
        
    




