
import os
import zipfile
from datetime import datetime, date

from PyQt5.QtWidgets import QApplication
from qgis.core import QgsProject, QgsVectorFileWriter
import pickle

from RAPTOR.std_raptor import raptor
from RAPTOR.rev_std_raptor import rev_raptor
from footpath_on_road_b_to_b import footpath_on_road_b_b
from converter_layer import MultiLineStringToLineStringConverter
from visualization import visualization

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
    
    path = PathToNetwork
    
    self.setMessage ("Load footpath ...")        
    QApplication.processEvents()
    with open(path+'/transfers_dict.pkl', 'rb') as file:
        footpath_dict = pickle.load(file)
    
    self.progressBar.setValue(1)

    footpath_dict_b_b = {}
    """
    self.setMessage ("Load footpath building to building ...")        
    QApplication.processEvents()
    with open(path+'/transfers_dict_b_b.pkl', 'rb') as file:
        footpath_dict_b_b = pickle.load(file)
        
    # Получение слоя buildings_jaffa_and_buff
    layer = QgsProject.instance().mapLayersByName('jaffa_buildings_west')[0]

    # Получение значений osm_id из слоя
    osm_ids = set()
    for feature in layer.getFeatures():
      osm_ids.add(int(feature['osm_id']))

    # Фильтрация словаря footpath_dict_b_b по значениям osm_id
    self.setMessage ("Filtering footpath_dict_b_b...")        
    QApplication.processEvents()
    filtered_footpath_dict_b_b = {k: v for k, v in footpath_dict_b_b.items() if k in osm_ids}
    
    footpath_dict_b_b = filtered_footpath_dict_b_b
    self.progressBar.setValue(2)
    """       
    self.setMessage ("Load routes_by_stop ...")
    QApplication.processEvents()
    with open(path+'/routes_by_stop.pkl', 'rb') as file:
        routes_by_stop_dict = pickle.load(file)
    
    self.progressBar.setValue(3)
    
    if mode == 1:
      self.setMessage ("Load stops ...")
      QApplication.processEvents()
      with open(path+'/stops_dict_pkl.pkl', 'rb') as file:
        stops_dict = pickle.load(file)
      
      self.progressBar.setValue(4)

      self.setMessage ("Load stoptimes ...")
      QApplication.processEvents()
      with open(path+'/stoptimes_dict_pkl.pkl', 'rb') as file:
        stoptimes_dict = pickle.load(file)
      
      self.progressBar.setValue(5)

      self.setMessage ("Load idx_by_route_stop ...")
      QApplication.processEvents()
      with open(path+'/idx_by_route_stop.pkl', 'rb') as file:
        idx_by_route_stop_dict = pickle.load(file)
      
      self.progressBar.setValue(6)
          
    else:
     self.setMessage ("Load stops_reversed ...")
     QApplication.processEvents()
     with open(path+'/stops_dict_reversed_pkl.pkl', 'rb') as file:  #reversed
        stops_dict = pickle.load(file)
     
     self.progressBar.setValue(4)   

     self.setMessage ("Load stoptimes_reversed ...")
     QApplication.processEvents()      
     with open(path+'/stoptimes_dict_reversed_pkl.pkl', 'rb') as file: #reversed
        stoptimes_dict = pickle.load(file)
     
     self.progressBar.setValue(5)
     
     
     self.setMessage ("Load rev_idx_by_route_stop ...")
     QApplication.processEvents()   
     with open(path+'/rev_idx_by_route_stop.pkl', 'rb') as file:
        idx_by_route_stop_dict = pickle.load(file) 
     
     self.progressBar.setValue(6)
    
    return (stops_dict, 
            stoptimes_dict, 
            footpath_dict, 
            footpath_dict_b_b, 
            routes_by_stop_dict, 
            idx_by_route_stop_dict)

# return postfix for name of filereport
def getDateTime():
  current_datetime = datetime.now()
  year = current_datetime.year
  month = str(current_datetime.month).zfill(2)
  day = str(current_datetime.day).zfill(2)
  hour = str(current_datetime.hour).zfill(2)
  minute = str(current_datetime.minute).zfill(2)
  second = str(current_datetime.second).zfill(2)
  return f'{year}{month}{day}_{hour}{minute}{second}'

def verify_break (self, 
                  Layer= "", 
                  LayerDest= "", 
                  curr_getDateTime = "", 
                  folder_name = ""):
  
  if self.break_on:
            
            self.textLog.append (f'<a><b><font color="red">Algorithm raptor is break</font> </b></a>')
            time_after_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.textLog.append(f'<a>Time break {time_after_computation}</a>') 
            if folder_name !="":
              write_info (self, 
                          Layer, 
                          LayerDest, 
                          curr_getDateTime, 
                          folder_name, 
                          self.cbSelectedOnly1
                          )  
            self.progressBar.setValue(0)  
            self.setMessage ("Algorithm raptor is break")
            return True
  return False

def runRaptorWithProtocol(self, 
                          sources, 
                          raptor_mode, 
                          protocol_type, 
                          timetable_mode, 
                          selected_only1, 
                          selected_only2)-> tuple:

  
  count = len(sources)
  self.progressBar.setMaximum(count + 5)
  self.progressBar.setValue(0)

  
  PathToNetwork = self.config['Settings']['PathToPKL']
  PathToProtocols = self.config['Settings']['PathToProtocols']
  D_TIME = time_to_seconds(self.config['Settings']['TIME'])
  
  MAX_TRANSFER = int (self.config['Settings']['Max_transfer'])
  MIN_TRANSFER = int (self.config['Settings']['Min_transfer'])

  MaxExtraTime = int (self.config['Settings']['MaxExtraTime'])*60
  DepartureInterval = int (self.config['Settings']['DepartureInterval'])*60
  
  Speed = float(self.config['Settings']['Speed'].replace(',', '.')) * 1000 / 3600                    # from km/h to m/sec

  MaxWalkDist1 = int(self.config['Settings']['MaxWalkDist1'])/Speed          # dist to time
  MaxWalkDist2 = int(self.config['Settings']['MaxWalkDist2'])/Speed          # dist to time
  MaxWalkDist3 = int(self.config['Settings']['MaxWalkDist3'])/Speed          # dist to time

  MaxTimeTravel = float(self.config['Settings']['MaxTimeTravel'].replace(',', '.'))*60           # to sec
  MaxWaitTime = float(self.config['Settings']['MaxWaitTime'].replace(',', '.'))*60               # to sec
  MaxWaitTimeTransfer= float(self.config['Settings']['MaxWaitTimeTransfer'].replace(',', '.'))*60 # to sec 
  
  CHANGE_TIME_SEC = int(self.change_time)
  time_step = int (self.config['Settings']['TimeInterval'])
  Layer = self.config['Settings']['Layer']

  UseField = self.config['Settings']['UseField'] == "True"
  Field = self.config['Settings']['Field']
  LayerDest = self.config['Settings']['LayerDest']

  LayerViz = self.config['Settings']['LayerViz']

  if protocol_type == 2:
    UseField = False
  
  begin_computation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  
  self.textLog.append(f'<a>Algorithm started at {begin_computation_time}</a>')

  today = date.today()
  
  
  if verify_break(self):
      return 0, 0
  QApplication.processEvents()
  (
  stops_dict,
  stoptimes_dict, 
  footpath_dict,
  footpath_dict_b_b, 
  routes_by_stop_dict, 
  idx_by_route_stop_dict
  ) = myload_all_dict (self, PathToNetwork, raptor_mode)
        
  if verify_break(self):
      return 0, 0

  
  #print (f'mode = {raptor_mode}')
  #print("stops_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(stops_dict.items())]))
  
  #print("stoptimes_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(stoptimes_dict.items())]))
  #print("routes_by_stop_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(routes_by_stop_dict.items())]))
  #print("idx_by_route_stop_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(idx_by_route_stop_dict.items())]))

  #print("footpath_dict:\n" + "\n".join([f"{key}: {value}" for key, value in list(footpath_dict.items())]))
  
  
      
  self.textLog.append(f'<a>Loading dictionary done</a>')
  self.textLog.append(f'<a>Starting calculating</a>')
   
  
  reachedLabels = dict()


  layers_dest = QgsProject.instance().mapLayersByName(LayerDest)
  layer_dest = layers_dest[0]
  features_dest = layer_dest.getFeatures() 

  if selected_only2:
    features_dest = layer_dest.selectedFeatures() 
  
  attribute_dict = {}
  if UseField:
    self.setMessage ("Make dictionary for aggregate ...")    
    QApplication.processEvents()          
    fields = layer_dest.fields()
      
    first_field_name = fields[0].name()
    
    for feature in features_dest:
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
   """
   for i in range(0,intervals_number):
            header += f'{low_bound_min}min-{top_bound_min}min,'
            if self.use_aggregate:
                header += f'sum({self.field_aggregate}),'
   """

   for i in range(0, intervals_number):
    protocol_header +=  f',{low_bound_min}min-{top_bound_min}min'
    
    if UseField:
      protocol_header += f',sum({Field})'
    grades.append ([low_bound_min,top_bound_min])
    low_bound_min = low_bound_min + time_step_min
    top_bound_min = top_bound_min + time_step_min
   protocol_header += ',Total\n'  
   #increase by one the last top bound
   #last_top = grades[intervals_number-1][1]
   #grades[intervals_number-1][1] = last_top

  
   
  if protocol_type == 2:   
   
   ss = "Origin_ID,Start_time"
   ss += ",Walk1_time,BStop1_ID,Wait1_time,Bus1_start_time,Line1_ID,Ride1_time,AStop1_ID,Bus1_finish_time"
   ss += ",Walk2_time,BStop2_ID,Wait2_time,Bus2_start_time,Line2_ID,Ride2_time,AStop2_ID,Bus2_finish_time"
   ss += ",Walk3_time,BStop3_ID,Wait3_time,Bus3_start_time,Line3_ID,Ride3_time,AStop3_ID,Bus3_finish_time"
   ss += ",DestWalk_time,Destination_ID,Destination_time"
   if raptor_mode == 2:
     ss = ss.replace("Origin_ID", "TEMP_ORIGIN_ID")
     ss = ss.replace("Destination_ID", "Origin_ID")
     ss = ss.replace("TEMP_ORIGIN_ID", "Destination_ID")
     ss += ",Arrives before"
   ss += ",Duration"  
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

  """
  road_layer = QgsProject.instance().mapLayersByName('roads_israel')[0]
  converter = MultiLineStringToLineStringConverter(self, road_layer)
  road_layer = converter.execute()
  footpath_b_b = footpath_on_road_b_b(self,
                                      road_layer,
                                      layer_dest, 
                                      Speed)
  footpath_b_b.init()
  """
    
  for i in range(0,count):
          
          if verify_break(self, 
                          Layer, 
                          LayerDest, 
                          curr_getDateTime, 
                          folder_name
                          ):
            return 0, folder_name
          
          self.progressBar.setValue(i + 6)
          self.setMessage(f'Calc point №{i+1} from {count}')
          QApplication.processEvents()
          SOURCE, D_TIME = sources[i]

          #b_b = footpath_b_b.calc(str(SOURCE))
               
          if raptor_mode == 1:
           
           output  = raptor(SOURCE, 
                            D_TIME, 
                            MAX_TRANSFER, 
                            MIN_TRANSFER, 
                            CHANGE_TIME_SEC,
                            routes_by_stop_dict, 
                            stops_dict, 
                            stoptimes_dict, 
                            footpath_dict,
                            footpath_dict_b_b,  
                            idx_by_route_stop_dict,
                            MaxTimeTravel, 
                            MaxWalkDist1, 
                            MaxWalkDist2, 
                            MaxWalkDist3, 
                            MaxWaitTime, 
                            MaxWaitTimeTransfer, 
                            timetable_mode, 
                            MaxExtraTime, 
                            DepartureInterval,
                            
                            )
           
           
           
          else:
            
            output = rev_raptor(SOURCE, 
                                D_TIME, 
                                MAX_TRANSFER, 
                                MIN_TRANSFER, 
                                CHANGE_TIME_SEC, 
                                routes_by_stop_dict, 
                                stops_dict, 
                                stoptimes_dict, 
                                footpath_dict,
                                footpath_dict_b_b,  
                                idx_by_route_stop_dict,
                                MaxTimeTravel, 
                                MaxWalkDist1, 
                                MaxWalkDist2, 
                                MaxWalkDist3, 
                                MaxWaitTime,
                                MaxWaitTimeTransfer, 
                                timetable_mode, 
                                MaxExtraTime, 
                                DepartureInterval)
            
            
          # !testing -deleting item with None value on end
                 
          keys_to_remove = [key for key, value in output.items() if value[-1] == (None, None, None, None)]

          for key in keys_to_remove:
            del output[key]
          
          reachedLabels = output
          
          # Now write current row   
          if protocol_type == 1:   
            make_protocol_summary(SOURCE, 
                                  reachedLabels, 
                                  f, 
                                  grades, 
                                  UseField, 
                                  attribute_dict
                                  ) 
          if protocol_type == 2 :           
            make_protocol_detailed (raptor_mode, 
                                    D_TIME, 
                                    reachedLabels, 
                                    f, 
                                    timetable_mode,
                                    )
  if protocol_type == 1:
    vis = visualization (self, f, LayerViz, mode = 1)
  if protocol_type == 2:
    vis = visualization (self, f, LayerViz, mode = 2)
  vis.run()  

  QApplication.processEvents()
  time_after_computation = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  self.textLog.append(f'<a>Time after computation {time_after_computation}</a>')  

  write_info (self, 
              Layer, 
              LayerDest, 
              curr_getDateTime, 
              folder_name, 
              selected_only1
              )
  self.setMessage(f'Calculating done')
  return 1, folder_name
  

def write_info (self,Layer, 
                LayerDest, 
                curr_getDateTime, 
                folder_name, 
                selected_only1
                ):
  text = self.textLog.toPlainText()
  filelog_name = f'{folder_name}//log_{curr_getDateTime}.txt'
  with open(filelog_name, "w") as file:
    file.write(text)

  zip_filename1 = f'{folder_name}//origins_{Layer}_{curr_getDateTime}.zip'
  filename1 = f'{folder_name}//origins_{Layer}_{curr_getDateTime}.geojson'

  self.setMessage(f'Compressing layer ...')
  QApplication.processEvents()
  
  save_layer_to_zip(Layer, zip_filename1, filename1, selected_only1)
  
  """
  if Layer != LayerDest: 
    zip_filename2 = f'{folder_name}//destinations_{LayerDest}_{curr_getDateTime}.zip'
    filename2 = f'{folder_name}//destinations_{LayerDest}_{curr_getDateTime}.geojson'
    save_layer_to_zip(LayerDest, zip_filename2, filename2)  
  """
  
  self.textLog.append(f'<a href="file:///{folder_name}" target="_blank" >Output in folder</a>')  
  

# for type_protokol = 1 
def make_protocol_summary (SOURCE, 
                           dictInput, 
                           f, 
                           grades, 
                           use_fields, 
                           attribute_dict
                           ):
    
  time_grad = grades
  #[[-1,0], [0,10],[10,20],[20,30],[30,40],[40,50],[50,61] ]
  counts = {x: 0 for x in range(0, len(time_grad))} #counters for grades
  agrregates = {x: 0 for x in range(0, len(time_grad))} #counters for agrregates

  #f1 = r'c:/temp/rep.txt'

  with open(f, 'a') as filetowrite:
   #with open(f1, 'a') as rep:
    for dest, info in dictInput.items():
       
       if int(dest) <= 50585 or int(dest) >= 10000000000: # exclude bus stops from protokol
        continue

       time_to_dest = int (round(info[2]))
    
       for i in range (0, len(time_grad)) :
        grad = time_grad[i]
        if time_to_dest > grad[0]*60 and time_to_dest <= grad[1]*60:
         counts[i] = counts[i] + 1
      
       #if i == 1:
       #      rep.write(str(dest) + "\n")  
       #      print ('str(dest)')
         if use_fields:
           agrregates[i] = agrregates[i] + attribute_dict.get(int(dest), 0)
         break
     
    row = str(SOURCE)
    Total = 0   
    for i in range (0, len (time_grad)) :  
     row = f'{row},{counts[i]}'
     if not use_fields:
      Total += counts[i]
     if use_fields:
       row = f'{row},{agrregates[i]}'
       Total += agrregates[i]
    filetowrite.write(f'{row},{Total}\n')
  
 
# for type_protokol =2 
def  make_protocol_detailed(raptor_mode, 
                            D_TIME, 
                            dictInput, 
                            protocol_full_path, 
                            timetable_mode,
                            ):
  
  
  sep=","
  building_symbol = "b"
  stop_symbol = "s"
  f = protocol_full_path   
  stop_max_number = 50585
  stop_newnumber_startnumber = 10000000000

  write_first_line = False
  write_b_b = False
    
  with open(f, 'a') as filetowrite:
   gcounter = 1 # because header is row number 1
   
   list_gcounter_double_walk_adjacent = []

   

   # dictInput - dict from testRaptor
   # every item dictInput : dest - key, info - value 

   
   
   for dest, info in dictInput.items():    
    
    SOURCE =  info[0]

    if not write_first_line:
      if raptor_mode == 1:
        row = f'{SOURCE}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}\
          {sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{SOURCE}{sep}{sep}0'
      else:
        row = f'{SOURCE}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}\
          {sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{SOURCE}{sep}{sep}{sep}0'
      filetowrite.write(row +"\n")
      write_first_line = True
    """
    if not write_b_b:
      for building, duration in b_b.items():
        if str(SOURCE) != str(building):
          if raptor_mode == 1:
            
            row = f'{SOURCE}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}\
              {sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{building}{sep}{sep}{duration}'
            
          else:
            
            row = f'{building}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}\
              {sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{SOURCE}{sep}{sep}{sep}{duration}'
              
          filetowrite.write(row +"\n")
      write_b_b = True
    """    
    
    
    '''
    Examle info[3] = pareto_set =
    [(0, [('walking', 2003, 24206.0, Timedelta('0 days 00:02:47'),Timestamp('2023-06-30 08:37:13')), 
    (Timestamp('2023-06-30 08:36:59'), 24206, 14603, Timestamp('2023-06-30 08:33:36'), '3150_67'), 
    ('walking', 14603, 1976.0, Timedelta('0 days 00:02:03.300000'), Timestamp('2023-06-30 08:31:32.700000'))])]    
    '''
    pareto_set = info[3]
    
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
        
         #if SOURCE > stop_max_number and SOURCE < stop_newnumber_startnumber:
         #  symbol1 = building_symbol
         #else:
         #  symbol1 = stop_symbol

         if last_leg[0] == 'walking':
          
          arrival_time = last_leg[4] + last_leg[3]
         else:       
          
          arrival_time = last_leg[3]
         
         sarrival_time = seconds_to_time(arrival_time)
         
         orig_dest = Destination 
        
         if walk1_time == "":
             walk1_time = 0 

         if walk2_time == "" and ssecond_boarding_stop != "":
             walk2_time = 0     

         if walk3_time == "" and sthird_boarding_stop != "":
             walk3_time = 0     

         if dest_walk_time == "":
             dest_walk_time = 0  
         
         #if timetable_mode and len(journey) > 1:
         #  D_TIME = journey[0][4]
         if timetable_mode and raptor_mode == 1: 
           D_TIME = journey[0][4] 

         #if timetable_mode and raptor_mode == 2: 
         if raptor_mode == 2:   
           if len(journey) > 1:
            sarrival_time = seconds_to_time(journey[-2][3] + journey[-1][3])
           else: 
            
            if journey[0][0] == "walking":
              sarrival_time = seconds_to_time(journey[0][3] + journey[0][4])
            else:
              sarrival_time = seconds_to_time(journey[0][3])
              
         if raptor_mode == 1:
            duration =  time_to_seconds(sarrival_time) - D_TIME
         else:
            duration =  time_to_seconds(sarrival_time) - start_time

         
         if raptor_mode == 1:
              if orig_dest <= stop_max_number or orig_dest >= stop_newnumber_startnumber:
                  continue 
              row = f'{SOURCE}{sep}{seconds_to_time(D_TIME)}{sep}{walk1_time}{sep}{sfirst_boarding_stop}\
{sep}{wait1_time}{sep}{sfirst_boarding_time}{sep}{line1_id}{sep}{ride1_time}{sep}{sfirst_arrive_stop}{sep}{sfirst_arrive_time}\
{sep}{walk2_time}{sep}{ssecond_boarding_stop}{sep}{wait2_time}{sep}{ssecond_boarding_time}{sep}{line2_id}{sep}{ride2_time}{sep}{ssecond_arrive_stop}{sep}{ssecond_bus_arrival_time}\
{sep}{walk3_time}{sep}{sthird_boarding_stop}{sep}{wait3_time}{sep}{sthird_boarding_time}{sep}{line3_id}{sep}{ride3_time}{sep}{sthird_arrive_stop}{sep}{sthird_bus_arrival_time}\
{sep}{dest_walk_time}{sep}{orig_dest}{sep}{sarrival_time}{sep}{duration}'
           
         else:
              if SOURCE_REV <= stop_max_number or SOURCE_REV >= stop_newnumber_startnumber:
                  continue 
          
              row = f'{SOURCE_REV}{sep}{seconds_to_time(start_time)}{sep}{walk1_time}{sep}{sfirst_boarding_stop}\
{sep}{wait1_time}{sep}{sfirst_boarding_time}{sep}{line1_id}{sep}{ride1_time}{sep}{sfirst_arrive_stop}{sep}{sfirst_arrive_time}\
{sep}{walk2_time}{sep}{ssecond_boarding_stop}{sep}{wait2_time}{sep}{ssecond_boarding_time}{sep}{line2_id}{sep}{ride2_time}{sep}{ssecond_arrive_stop}{sep}{ssecond_bus_arrival_time}\
{sep}{walk3_time}{sep}{sthird_boarding_stop}{sep}{wait3_time}{sep}{sthird_boarding_time}{sep}{line3_id}{sep}{ride3_time}{sep}{sthird_arrive_stop}{sep}{sthird_bus_arrival_time}\
{sep}{dest_walk_time}{sep}{SOURCE}{sep}{sarrival_time}{sep}{seconds_to_time(D_TIME)}{sep}{duration}' 

               
         filetowrite.write(row +"\n")
                    

 
def int1(s):
  result = s
  if s == "":
   result = 0
  return result

def save_layer_to_zip(layer_name, 
                      zip_filename, 
                      filename, 
                      selected_only1
                      ):
    try:
      layer = QgsProject.instance().mapLayersByName(layer_name)[0]
      temp_file = "temp_layer_file.geojson"
      QApplication.processEvents()  
      QgsVectorFileWriter.writeAsVectorFormat(layer, temp_file, "utf-8", layer.crs(), "GeoJSON")
      QApplication.processEvents()  
      with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(temp_file, os.path.basename(filename))
      QApplication.processEvents()    
      os.remove(temp_file)   
    except:
      return 0  
    
    
     
        
    




