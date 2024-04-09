
#from qgis.core import QgsVectorLayer, QgsGraphBuilder, QgsGraphAnalyzer,QgsPointXY
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import *
from qgis.analysis import QgsGraphAnalyzer,QgsGraphBuilder,QgsVectorLayerDirector,QgsNetworkSpeedStrategy,QgsNetworkDistanceStrategy
from qgis.PyQt.QtCore import QVariant
from datetime import datetime, timedelta

def build_graph(vectorLayer,directionFieldId,speedFieldId,points_to_tie,strategy_id): 
 
 # don't use information about road direction from layer attributes,
# all roads are treated as two-way
#  director = QgsVectorLayerDirector(vectorLayer,  -1, '', '', '',
#                                     QgsVectorLayerDirector.DirectionBoth)
 # use field with index directionFieldId as source of information about road direction.
# one-way roads with direct direction have attribute value "yes", My: 1
# one-way roads with reverse direction have the value "1", My:2
# bidirectional roads have "no".  My: 0
# By default roads are treated as two-way.
# This scheme can be used with OpenStreetMap data
 # Default speed value
#  director = QgsVectorLayerDirector(vectorLayer,  directionFieldId, '1', '2', '0',
#                                     QgsVectorLayerDirector.DirectionBoth)
 director = QgsVectorLayerDirector(vectorLayer,  -1, '', '', '',
                                     QgsVectorLayerDirector.DirectionBoth)
 defaultValue = 50
# Conversion from speed to metric units ('1' means no conversion)
# toMetricFactor = 1
#strategy=None
 toMetricFactor=1 #for speed3 m/sec
 if strategy_id==1:
  strategy = QgsNetworkSpeedStrategy(speedFieldId, defaultValue, toMetricFactor)
 else: 
  strategy = QgsNetworkDistanceStrategy()
 #strategy = QgsNetworkDistanceStrategy()
 director.addStrategy(strategy)
 builder = QgsGraphBuilder(vectorLayer.crs()) 
 tiedPoints = director.makeGraph(builder,points_to_tie)
 graph = builder.graph()
 return tiedPoints,graph
 

def find_shortest_paths(road_layer_path,directionFieldId,speedFieldId,points,strategy_id):
 # Load the road network layer
 #road_layer=""
#  if strategy_id==1:
#   road_layer = QgsVectorLayer(path_to_roads_layer_for_speed, 'roads', 'ogr')
#  else:
#    road_layer = QgsVectorLayer(path_to_roads_layer_for_length, 'roads', 'ogr')
 road_layer = QgsVectorLayer(road_layer_path, 'roads', 'ogr')
 
 
 tiedPoints, graph=build_graph(road_layer,directionFieldId,speedFieldId,points,strategy_id)
 pStart = tiedPoints[0]
 idStart = graph.findVertex(pStart)

 (tree, costs) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0)
     
 
 print("Spanning tree nodes count="+str(len(tree)))
 return tree,costs,graph
 pass

def str1(time):   
   output=add_zero(str(time.hour))+":"+add_zero(str(time.minute))+":"+add_zero(str(time.second))
   return output
def add_zero(s):
 if len(s)==1:
    s="0"+s
 return s   


def save_shortest_path_data(SOURCE,PathToProtocols,shortest_path_costs_protocol_name,tree,costs,graph):
  sep=","
  f = PathToProtocols+"\\"+shortest_path_costs_protocol_name+"_"+str(SOURCE)+".csv"  
  radius=100 #meter
  header="index,cost,x,y"+"\n"
  count_not_founded_nodes=0
  count_not_uniquie_founded_nodes=0
  dictNodes=dict()
  with open(f, 'w') as filetowrite:   
    filetowrite.write(header) 
    for i in range(0,len(costs)) :
     tree_ind=tree[i]
     cost= round( costs[i],0)
     vert=graph.vertex(i);
     x=vert.point().x()
     y=vert.point().y()                
     filetowrite.write(str(tree_ind)+sep+ str(cost)+sep+str(x)+sep+str(y)+"\n")  
"""
Input:
 file where saved costs of shortest paths from a source to different nodes
 grades
"""
def makeShortestPathAccessibilityByTimeProtocol(PathToProtocols,shortest_path_costs_protocol_name,
         shortest_path_costs_statistics_name, max_time_minutes,time_step_minutes,SOURCE ):
  sep=","
  table_header,grades =prepare_grades(max_time_minutes, time_step_minutes)
  counts={x: 0 for x in range(0, len(grades))} #counters for grades
  f = PathToProtocols+"\\"+shortest_path_costs_protocol_name+"_"+str(SOURCE)+".csv"
  with open(f, 'r') as filetoread:
   for line in filetoread:
       arr=line.split(sep)
       cost=float(arr[1].strip())     
       num = cost/60
       for i in range(0,len(grades)) :
        grad=grades[i]
        if num>=grad[0] and num<grad[1]:
         counts[i]=counts[i]+1
         break 
    
  row="" 
  f = PathToProtocols+"\\"+shortest_path_costs_statistics_name+"_"+str(SOURCE)+".csv"
  with open(f, 'w') as filetowrite:
   filetowrite.write(table_header)  
   for i in range(0,len(grades)) :  
    row=row+str(counts[i])+sep     
   filetowrite.write(row+"\n")

def prepare_grades(max_time_minutes, time_step_minutes): 
 intervals_number= round(max_time_minutes/time_step_minutes)
 grades=[]
 header=""
 time_step_min=time_step_minutes
 low_bound_min=0
 top_bound_min=time_step_min
 for i in range(0,intervals_number):
  header = header + str(low_bound_min)+"-"+str(top_bound_min)+" m,"
  grades.append([low_bound_min,top_bound_min])
  low_bound_min=low_bound_min+time_step_min
  top_bound_min=top_bound_min+time_step_min
 header=header+"\n" 
 #increase by one the last top bound
 last_top=grades[intervals_number-1][1]+1
 grades[intervals_number-1][1]= last_top
 return header,grades

def selectFromLayerBycircle(layer,xCenter,yCenter,radius):     
     geometry=QgsGeometry.fromPointXY(QgsPointXY(xCenter,yCenter))
     request = QgsFeatureRequest().setDistanceWithin(geometry,radius)
     return layer.getFeatures(request)

"""
Constants and call of functions
"""
#PathToProtocols="C:\\Users\\eug10\\Documents\\QGIS Projects\\Protocols\\"
# shortest_path_costs_protocol_name="shortest_path_costs"
# shortest_path_costs_statistics_name="shortest_path_costs_statistics"
# path_to_qgis_projects="C:\\Users\\eug10\\Documents\\QGIS Projects\\"
# path_to_roads_layer_for_length=path_to_qgis_projects+"TelAviv_edges_ITM\\TelAviv_edges_ITM.shp"
# path_to_roads_layer_for_speed=path_to_qgis_projects+"TelAviv_edges_ITM_traveltime\\TelAviv_edges_ITM.shp"
# path_to_nodes_layer=path_to_qgis_projects+"TelAviv_nodes_ITM\\TelAviv_nodes_ITM.shp"
# path_to_roads_layer_subset1=path_to_qgis_projects+"Israel_edges_tt_Subset1\\Israel_edges_tt_Subset1.shp"
# path_to_roads_layer_subset2=path_to_qgis_projects+"Israel_edges_tt_Subset2\\Israel_edges_tt_Subset2.shp"
# SOURCE="322756135"
# x1=177021.757305
# y1=662029.492182

#x1=176967.5  #node fid=84155
#y1=662028.6
# x2=176641.867023
# y2=661978.83873

# x3 =176652.24749
# y3 = 662125.91648
# points=[QgsPointXY(x1,y1)]  #,QgsPointXY(x2,y2),QgsPointXY(x3,y3)
# max_time_minutes=360
# time_step_minutes=5
# #makeShortestPathAccessibilityByTimeProtocol()
# #quit()
# directionFieldId=5
# speedFieldId = 21 #speed
# strategy_id=1 #speed
# #build_graph(vectorLayer,directionFieldId,speedFieldId)
# path_to_vectorLayer = path_to_roads_layer_for_speed
# if strategy_id==1:
#   strategy="Strategy by speed"
# else:
#  strategy="Strategy by distance"   
# print("Source point: x="+str(x1)+", y="+str(y1)) 
# print(strategy)
# print("path to network layer: "+ path_to_vectorLayer)

# begin_computation_time = datetime.now()
# print("begin of computation time="+str1(begin_computation_time))
# tree,costs,graph=find_shortest_paths(path_to_vectorLayer,directionFieldId,speedFieldId,points,strategy_id)
# time_after_computation= datetime.now()
# print("end of computation time="+str1(time_after_computation))
# work_time = round((time_after_computation -begin_computation_time).total_seconds(),1)
# print("computation time = " + str(work_time))

# save_shortest_path_data(tree,costs,graph)
# print("Done")

def main_shortest_paths_utils(SOURCE,PathToProtocols,path_to_vectorLayer,directionFieldId,speedFieldId,points,strategy_id):
 shortest_path_costs_protocol_name="shortest_path_costs"
 begin_computation_time = datetime.now()
 print("begin of computation time="+str1(begin_computation_time))
 tree,costs,graph=find_shortest_paths(path_to_vectorLayer,directionFieldId,speedFieldId,points,strategy_id)
 time_after_computation= datetime.now()
 print("end of computation time="+str1(time_after_computation))
 work_time = round((time_after_computation -begin_computation_time).total_seconds(),1)
 print("computation time = " + str(work_time))

 save_shortest_path_data(SOURCE,PathToProtocols,shortest_path_costs_protocol_name,tree,costs,graph)
 print("Done") 

# if __name__ == "__main__":
#    app = QApplication([]) 
#    main()