from datetime import datetime, timedelta
import os
import pyproj
# constants
rides_file_name="rides.csv"
rides_header="RideId,Leg,JType,TimeDeparture,TimeArrival,Timedelta,stop_from,stop_to,trip_id"


"""
This function saves output of raptor or revraptor in a file with fields
 Source,Destination,Time in a bus,Transfers,Waiting time
It is used only in a case when  SOURCE and DESTINATION are defined
"""

def checkFileExist(path):
   isExist = os.path.exists(path)
   return isExist
"""
This function is not in use now
"""
def getRaptorDestinationTime(raptorOut):
  output=raptorOut
  rounds_inwhich_desti_reached=output[0]
  if rounds_inwhich_desti_reached is None:
      return -1  # destination cannot be reached
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
         return journey_time 
         #print("journey_time="+str(journey_time)+" seconds")

def get_feature_coordinates_with_conversions(feature):
   original_crs="EPSG:2039"
   target_crs="EPSG:4326"
   transformer = pyproj.Transformer.from_crs(original_crs, target_crs, always_xy=True)
   coordinates = [feature.geometry().asPoint()]
   point_coordinates = coordinates[0]
   x = point_coordinates[0]  # X-coordinate
   y = point_coordinates[1]   
   lon, lat = transformer.transform(x, y)
   return lon,lat     
  
def get_feature_coordinates(feature):
   coordinates = [feature.geometry().asPoint()]
   point_coordinates = coordinates[0]
   lon = point_coordinates[0]  # X-coordinate
   lat = point_coordinates[1]
   return lon,lat 