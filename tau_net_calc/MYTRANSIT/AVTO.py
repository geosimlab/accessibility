
#from qgis.core import QgsVectorLayer, QgsGraphBuilder, QgsGraphAnalyzer,QgsPointXY
from qgis.PyQt.QtWidgets import QApplication
from qgis.core import *
from qgis.analysis import QgsGraphAnalyzer,QgsGraphBuilder,QgsVectorLayerDirector,QgsNetworkSpeedStrategy,QgsNetworkDistanceStrategy
from qgis.PyQt.QtCore import QVariant
from datetime import datetime, timedelta

def build_graph(vectorLayer, points_to_tie, strategy_id): 
 
    # object для интерпретации и управления направлением движения по дорогам, представленным в векторном слое (vectorLayer).
    director = QgsVectorLayerDirector(vectorLayer,  -1, '', '', '',
                                     QgsVectorLayerDirector.DirectionBoth)
 
    defaultValue = 50
    toMetricFactor = 1 #for speed3 m/sec
    if strategy_id == 1:
        strategy = QgsNetworkSpeedStrategy(-1, defaultValue, toMetricFactor)
    else: 
        strategy = QgsNetworkDistanceStrategy()

    # добавляет выбранную стратегию (strategy) к объекту 
    director.addStrategy(strategy)

    builder = QgsGraphBuilder(vectorLayer.crs()) 
    # созданиe графа дорожной сети на основе данных из векторного слоя и указанных точек привязки.
    # результатом будет список узлов графа, которые были связаны с этой точкой привязки
    tiedPoints = director.makeGraph(builder, points_to_tie)

    #получениe построенного графа из объекта builder.
    graph = builder.graph()

    return tiedPoints, graph
 

def find_shortest_paths(road_layer_path, points, strategy_id):
 
    road_layer = QgsVectorLayer(road_layer_path, 'roads', 'ogr')
  
    tiedPoints, graph = build_graph(road_layer, points, strategy_id)
    pStart = tiedPoints[0]
    idStart = graph.findVertex(pStart)

    """
    tree = {
    'A': None,
    'B': 'A',
    'C': 'B',
    'D': 'A',
    'E': 'B',
    'F': 'C'
        }

    
    costs = {
    'A': 0,
    'B': 3,
    'C': 8,
    'D': 2,
    'E': 7,
    'F': 9
    }
    """
    (tree, costs) = QgsGraphAnalyzer.dijkstra(graph, idStart, 0)
     
 
    print("Spanning tree nodes count="+str(len(tree)))
    return tree, costs, graph
 

def str1(time):   
   output=add_zero(str(time.hour))+":"+add_zero(str(time.minute))+":"+add_zero(str(time.second))
   return output
def add_zero(s):
 if len(s)==1:
    s="0"+s
 return s   


def save_shortest_path_data(SOURCE, PathToProtocols, tree, costs, graph):
  sep=","
  f = f'{PathToProtocols}//{SOURCE}.csv'  
  header = "index,cost,x,y"+"\n"
  with open(f, 'w') as filetowrite:   
    filetowrite.write(header) 
    for i in range(0,len(costs)) :
        tree_ind = tree[i]
        cost = round( costs[i],0)
        vert =graph.vertex(i);
        x = vert.point().x()
        y = vert.point().y()                
        filetowrite.write(f'{tree_ind},{cost},{x},{y}\n')  
"""
Input:
 file where saved costs of shortest paths from a source to different nodes
 grades
"""
def makeShortestPathAccessibilityByTimeProtocol(PathToProtocols,shortest_path_costs_protocol_name,
         shortest_path_costs_statistics_name, max_time_minutes,time_step_minutes,SOURCE ):
  sep=","
  table_header, grades = prepare_grades(max_time_minutes, time_step_minutes)
  counts = {x: 0 for x in range(0, len(grades))} #counters for grades
  f = f'{PathToProtocols}//{SOURCE}.csv'
  with open(f, 'r') as filetoread:
   for line in filetoread:
       arr = line.split(sep)
       cost = float(arr[1].strip())     
       num = cost/60
       for i in range(0,len(grades)) :
        grad = grades[i]
        if num >= grad[0] and num < grad[1]:
         counts[i] = counts[i]+1
         break 
    
  row = "" 
  f = PathToProtocols+"\\"+shortest_path_costs_statistics_name+"_"+str(SOURCE)+".csv"
  with open(f, 'w') as filetowrite:
    filetowrite.write(table_header)  
    for i in range(0,len(grades)) :  
        row = row + str(counts[i]) + sep     
        filetowrite.write(row+"\n")

def prepare_grades(max_time_minutes, time_step_minutes): 
    intervals_number= round(max_time_minutes/time_step_minutes)
    grades = []
    header = ""
    time_step_min = time_step_minutes
    low_bound_min = 0
    top_bound_min = time_step_min
    for i in range(0,intervals_number):
        header = header + str(low_bound_min)+"-"+str(top_bound_min)+" m,"
        grades.append([low_bound_min,top_bound_min])
        low_bound_min = low_bound_min+time_step_min
        top_bound_min = top_bound_min+time_step_min
    header = header+"\n" 
    #increase by one the last top bound
    last_top = grades[intervals_number-1][1] + 1
    grades[intervals_number-1][1] = last_top
    return header,grades

def main_shortest_paths_utils():

    path_to_vectorLayer = ""
    PathToProtocols = ""
    
    
    strategy_id = 1 #speed
    SOURCE = "322756135"
    x1 = 177021.757305
    y1 = 662029.492182
    points = [QgsPointXY(x1,y1)]
    
    tree, costs ,graph  = find_shortest_paths(path_to_vectorLayer, points, strategy_id)
    save_shortest_path_data (SOURCE, PathToProtocols, tree, costs, graph)
