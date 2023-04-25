# -*- coding: utf-8 -*-
"""
Created on Tue Mar 21 17:59:07 2023

@author: rasin
"""

import networkx as nx
import math
import numpy as np
from numpy.linalg import norm
import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString

#некоторые константы
Lmin =800



    
    

class GraphRadialCity:
    
    _MinDistRadial = 100#расстояние между городами на одном радиусе
    _Lmin =800#наименьшая длина главной окружности
    _min_dist_between_circles = 10  # расстяоние между окружностями, чтобы не налезали друг на друга
    
    _zero = 1.e-10

    '''Массивы, которые ниже в предыдущей реализации массивы с суффиком sec использовалсь 
    для вершин промежуточных слоев, для главных слоев без суффикса. Сводный массив с суффиком All.
    Сейчас временно используются только массивы, в котоырх нет разделения на основные и вспомогательные'''
    
    _nodesID_All = []
    _nodesID = []#использовалось для вершин главного слоя
    _nodesID_sec = []#использовалось для вспомогательных вершин
    ###позиции
    _pos_All=[]
    _pos =[]
    _pos_x_All = []
    _pos_y_All = []
    _pos_x = [] 
    _pos_y = []
    _pos_sec_x = []
    _pos_sec_y = []
    _pos_sec = []
    ####характеристики вершин
    _azimuth_nodes_All = []
    _azimuth_nodes = []
    _azimuth_nodes_sec = []
    _distance_nodes_All = []
    _distance_nodes = []
    _distance_nodes_sec = []
    _radiuses_main_circles = []  # радиусы основных окружностей
    _nNodes_In_main_circles = []  # количество вершин в основных окружностях
    ####ребра
    ###радиальные
    _edgesID_All = []
    _edges_All = []
    _edges = []
    _edges_from_sec=[]
    _typeOfRadialLinks = []

    #####круговые
    _circular_edges = []
    _circular_edges_sec = []
    _azimuth_edges = []
    _azimuth_edges_All = []

    _azimuth_edges_sec = []
    _distance_edges = []
    _distance_edges_All = []
    _typeOfCircularLinks = []
    _typeOfLinks_All = []


    
    _Path ="..\\ShapeFiles\\"

    _nRadialEdges = 0

    def setPath(self, path):
        self._Path = path


    
    def __init__(self, nCircles, minDistRadial):
        self._NCircles = nCircles
        N = self._NCircles  # для более короткого обращения
        self._MinDistRadial = minDistRadial
        self._Lmin = 8 * self._MinDistRadial
        '''_PowerOfTwo --- массив степеней двойки, тут хранятся все степени,
                до N включительно, здесь нам понадобятся начиная с 3. При этом на последней
                окужности мы имеем 2^{N+2} вершин'''

        self._PowerOfTwo = 2 ** np.arange(N + 3)
        self._PowerOfTwo = self._PowerOfTwo.astype(int)  # было странное поведение (тип intc)
        ####################################################################################################

        #следующий аттрибут --- шаг между вспомогательными кругами
        #self._stepOfRadiusOfSecCircles = (self._Lmin) / (4 * math.pi)  # надо поделить еще на 2
        self._stepOfRadiusOfSecCircles = self._MinDistRadial/(4*np.sin(math.pi/self._PowerOfTwo[3]))#случай если расстояние не радиус, а длина промежутка


        '''Для более эффективного выделения памяти под массивы полезно вычислить разные количественные характеристики.
                Например, все вершины в графе, все вершины основного слоя. Аналогично радиальные ребра'''
        self._nMainNodes = 2 * self._PowerOfTwo[N + 2] - 7
        self._nSecondaryNodes =4*(4 * (4 ** (N - 1) - 1) // 3 - 2 * (self._PowerOfTwo[N-1] - 1) + 1)
        self._nAllNodes = self._nMainNodes + self._nSecondaryNodes
        self._nRadialEdges = self._nMainNodes + 3 - self._PowerOfTwo[N + 2]
        # радиальных ребер столько же сколько вершин основных слоев минус последний уровень +7 (потому что у (0, 0))
        self._nCircularEdges = self._nAllNodes - 1#ребер на кругах столько же сколько вершин, и вычитаем 1(для центральной)
        self._nAllEdges = self._nRadialEdges + self._nCircularEdges



        ###############################################################
        ###############################################################
        ###############################################################
        '''Массив self._allangels используется для более эффективного
        вычиcления значений при использовании python'''
        start_angle = math.pi/(2 ** (N+1))
        all_angles = np.arange(0, 2**(N+2))#все числа, соотвествующие точкам последней окружности
        self._arr_angles = all_angles * start_angle#получается массив  точек с равным шагом
        #также удобно сразу посчитать все cos и sin
        self._cos_arr = np.cos(self._arr_angles)
        self._sin_arr = np.sin(self._arr_angles)

        self._nodesID_All = np.empty(self._nAllNodes, dtype= int)
        self._pos_x_All= np.empty(self._nAllNodes)
        self._pos_y_All = np.empty(self._nAllNodes)
        self._distance_nodes_All = np.empty(self._nAllNodes)
        self._azimuth_nodes_All = np.empty(self._nAllNodes)
        self._edges_All = [None] * self._nAllEdges
        self._edgesID_All = np.empty(self._nAllEdges, dtype= int)
        self._distance_edges_All = np.empty(self._nAllEdges)
        self._azimuth_edges_All = np.empty(self._nAllEdges)
        self._typeOfLinks_All = [None] * self._nAllEdges
        
    def CreateRadialGraph(self):   
        N = self._NCircles
        nMainNodes = (2 * self._PowerOfTwo[N+2] - 7)#количество элементов 
        #в основном слое
        radiuses = (self._MinDistRadial/(2*np.sin(math.pi/self._PowerOfTwo[3:N+3])))
        '''Массив radiuses хранит радиусы всех основных кругов. При вычислении
        используется broadcasting. Радиус начального нулевого круга мы не храним'''


        #self.CreateRadialGraphWithGivenRadiuses(radiuses)#радиусы уже подобраны
        #self.AddSecondaryLayers()
        '''Рисуем вершины основного слоя.'''
        #сначала нулевую вершину
        self._pos_x_All[0] = self._pos_y_All[0] = 0.0
        self._distance_nodes_All[0] = self._azimuth_nodes_All[0] = 0.0
        self._nodesID_All[0] = 0
        #индексация идет подряд
        stopNodeID = 0
        startNodeID = 1
        for i in range(N):
            #для передачи диапазона индексов надо знать число вершин в слое
            nNodes = self._PowerOfTwo[i+3]
            stopNodeID = startNodeID +nNodes
            indexes = np.arange(startNodeID, stopNodeID)
            self.CreateEqualiteralNodesOnCircle(radiuses[i], i+3, indexes, indexes)
            startNodeID =stopNodeID
            #первый элемент соответствует 3-й степени
        
        #строим радиусы для промежуточных слоев

        '''Количество промежуточных кругов. Всего кругов внутри большого круга 2^N. Выбрасываем
         все степени 2 (их N штук)'''
        #radiusesSec = np.arange(nSecondaryCircles)
        #чтобы узнавать количество кругов данного радиуса, достаточно выичтать соседние степени
        #двойки
        #самый внутрений круг мы вычисляем отдельно
        #startNodeID = stopNodeID
        nNodes = 4#на самом маленьком промежуточном круге 4 вершины
        stopNodeID = startNodeID +nNodes
        indexes = np.arange(startNodeID, stopNodeID)
        stepSecCircles = self._stepOfRadiusOfSecCircles
        radius =stepSecCircles
        #radiusSec[0] = radius
        self.CreateEqualiteralNodesOnCircle(radius, 2, indexes, indexes)
        radius += stepSecCircles#сейчас на втором круге, но там основной 
        #и он не рисуется
        startNodeID = stopNodeID
        for i in range(3, N+2):#вершин столько же сколько на меньшем круге
            #количество промежуточных кругов в слое между двумя главными кругами
            nSecCircles = (self._PowerOfTwo[i+1] - self._PowerOfTwo[i])//self._PowerOfTwo[2]-1#
            ###################################################################
            ###################################################################
            #########Следующее --- радиусы дополнительных кругов
            #делаем так, чтобы шаг был равным между кругами
            stepSecCircles = (radiuses[i -2] - radiuses[i - 3])/(nSecCircles+1)#равный шаг между большими окружностями
            radius = radiuses[i - 3]#можно сделать поакуратнее (это вынести перед циклом, а прибавка будет потом)
            ###################################################################
            ###################################################################
            nNodes = self._PowerOfTwo[i]
            #пробегаем по дополнительным кругам
            for j in range(nSecCircles):
                stopNodeID = startNodeID + nNodes
                indexes = np.arange(startNodeID, stopNodeID)
                radius += stepSecCircles
                self.CreateEqualiteralNodesOnCircle(radius, i, indexes, indexes)
                startNodeID = stopNodeID
            #здесь проходим основной круг
            radius += stepSecCircles
        #лучше сохранять как массив numpy координат, чтобы можно было выполнять арифметические дейситвия как с векторами
        self._pos_All = np.column_stack([ self._pos_x_All, self._pos_y_All])

        #добавляем радиальные ребра
        startEdgeID = 0
        startEdgeID = self.AddRadialEdgesWithSecondary(startEdgeID)
        '''stopEdgeID = 0
        startEdgeID = 0
        self.AddRadialEdge(1, 0, 0, 0)
        self.AddRadialEdge(3, 0, 1, 1)
        self.AddRadialEdge(5, 0, 2, 2)
        self.AddRadialEdge(7, 0, 3, 3)
        #elf._distance_nodes_All[0] =
        startSmaller = 1
        startBigger = 9
        nSmaller = self._PowerOfTwo[3]#количество вершин в меньшем слое
        startEdgeID = 4
        for i in range(4, N+3):
            #находим индексы слоев (в данном случсае файл создается и мы знаем, что они идут подряд)
            nBigger = self._PowerOfTwo[i]
            indSmaller = np.arange(startSmaller, startBigger)
            indBigger = np.arange(startBigger, startBigger + nBigger)
            stopEdgeID = startEdgeID + nSmaller

            self.AddRadialEdgesBetweenCircles(indBigger, indSmaller, startEdgeID, stopEdgeID)
            startSmaller = startBigger
            startBigger +=nBigger
            nSmaller = nBigger
            startEdgeID = stopEdgeID'''


        #Осталось добавить круговые ребра
        #ОСНОВНОй СЛОЙ
        nCircularEdges = len(self._nodesID_All) - 1
        startNodeID = 1
        stopNodeID = 1
        for i in range(3, N + 3):
            nNodes = self._PowerOfTwo[i]
            stopEdgeID = startEdgeID + nNodes
            indLinks= np.arange(startEdgeID, stopEdgeID)
            stopNodeID = startNodeID + nNodes
            indNodes = np.arange(startNodeID, stopNodeID)
            self.AddCircularEdges(indNodes,  startEdgeID, stopEdgeID, "mc")
            startNodeID = stopNodeID
            startEdgeID = stopEdgeID

        #ДОПОЛНИТЕЛЬНЫЕ
        nNodes = 4
        startNodeID = nMainNodes
        stopNodeID = startNodeID + nNodes
        indNodes = np.arange(startNodeID, stopNodeID)
        stopEdgeID = startEdgeID + nNodes
        indLinks = np.arange(startEdgeID, stopEdgeID)
        self.AddCircularEdges(indNodes,  startEdgeID, stopEdgeID, "nc")
        startNodeID = stopNodeID
        startEdgeID = stopEdgeID
        for i in range(3, N+2):
            nSecCircles = (self._PowerOfTwo[i+1] - self._PowerOfTwo[i])//self._PowerOfTwo[2]-1#
            nNodes = self._PowerOfTwo[i]
            #пробегаем по дополнительным кругам
            for j in range(nSecCircles):
                stopNodeID = startNodeID + nNodes
                stopEdgeID = startEdgeID + nNodes
                indNodes = np.arange(startNodeID, stopNodeID)
                indLinks = np.arange(startEdgeID, stopEdgeID)
                self.AddCircularEdges(indNodes,  startEdgeID, stopEdgeID, "nc")
                startNodeID = stopNodeID
                startEdgeID = stopEdgeID


    """Метод def CreateEqualiteralNodesOnCircles(self, radius, powerOfTwo):  
    вычисляет координаты и аттрибуты вершин расположенных на окружности радиуса radius.
    По умолчанию количество точек на круге --- степень двойки, поэтому передается не само
    количество, а степень powerOfTwo.
    
    indexes --- массив индексов, в который записываем данные элементы.
    
    Внутри метода для повышения эффективности используется массив всех углов.
    
    """

    def CreateEqualiteralNodesOnCircle(self, radius, powerOfTwo, indexes, arrID):
        '''добавить проверку
        1) что степень не может быть больше количества кругов.
        2)  что количество индексов равно 2^{powerOfTwo}
        3) проверка, что длины массивов indexes и arrID равны
        '''
        N = self._NCircles
        stepInArrAngles = self._PowerOfTwo[N+2 - powerOfTwo]#это и есть искомый шаг
        self._pos_x_All[indexes] = self._cos_arr[::stepInArrAngles] * radius
        self._pos_y_All[indexes] = self._sin_arr[::stepInArrAngles] * radius
        self._nodesID_All[indexes] = arrID
        #сразу вычисляем расстояния и азимуты
        self._distance_nodes_All[indexes] = radius#можно так, просто присваиваем эти значения
        #метод fill не работал (возможно он только со срезами)
        self._azimuth_nodes_All[indexes] = self._arr_angles[::stepInArrAngles]
    """
        AddRadialEdgesWithoutSecondary(self, start):
        добавляет радиальные ребра в случае, если мы рассматриваем их как линки
        между вершинами основных слоев. В базе их концы --- вершины основных слоев.
        
        Метод .AddRadialEdgesWithoutSecondary(self, start): делает аналогичные действия,
        но там концами link могут быть соответствующие вершины дополнительных слоев.
        
        Параметр start используется для передачи номеров ребер, с которых продолжается
        нумерация. 
        
        Не очень хорошо, что в зависимости от того какой метод используется, мы не можем 
        заранее предсказать кол-во ребер, поэтому внутрь процедуры загнали методы для
        выделения памяти и подсчета количество ребер, хотя возможно это лучше делать в основной
        программе (вариант решения проблемы выделить память под максимально возможный случай, а потом
        удалить).
        
        Методы возвращает идентификатор номер ребра, с которого можно продолжать нумерацию в основную программу.  
    """
    def AddRadialEdgesWithoutSecondary(self, start):
        #для более эффективного расходования памяти пересчитываем
        #количество ребер
        self._nRadialEdges = self._nMainNodes + 3 - self._PowerOfTwo[self._NCircles + 2]
        self._nAllEdges = self._nRadialEdges + self._nCircularEdges
        self._edges_All = [None] * self._nAllEdges
        self._distance_edges_All = np.empty(self._nAllEdges)
        self._azimuth_edges_All = np.empty(self._nAllEdges)
        self._lenght_edges_All = np.empty(self._nAllEdges)
        self._typeOfLinks_All = [None] * self._nAllEdges
        self._edges_All = [None] * self._nAllEdges
        self._edgesID_All = np.empty(self._nAllEdges, dtype= int)
        
        stopEdgeID = 0
        startEdgeID = 0
        self.AddRadialEdge(1, 0, 0, 0, "mr")
        self.AddRadialEdge(3, 0, 1, 1, "mr")
        self.AddRadialEdge(5, 0, 2, 2, "mr")
        self.AddRadialEdge(7, 0, 3, 3, "mr")
        #elf._distance_nodes_All[0] =
        startSmaller = 1
        startBigger = 9
        nSmaller = self._PowerOfTwo[3]#количество вершин в меньшем слое
        startEdgeID = 4
        for i in range(4, self._NCircles+3):
            #находим индексы слоев (в данном случсае файл создается и мы знаем, что они идут подряд)
            nBigger = self._PowerOfTwo[i]
            indSmaller = np.arange(startSmaller, startBigger)
            indBigger = np.arange(startBigger, startBigger + nBigger)
            stopEdgeID = startEdgeID + nSmaller

            self.AddRadialEdgesBetweenCircles(indBigger, indSmaller, startEdgeID, stopEdgeID, "mr")
            startSmaller = startBigger
            startBigger +=nBigger
            nSmaller = nBigger
            startEdgeID = stopEdgeID
        return startEdgeID
    
    def AddRadialEdgesWithSecondary(self, start):
        #для более эффективного расходования памяти пересчитываем
        #количество ребер
        self._nRadialEdges = self._nAllNodes + 3 - self._PowerOfTwo[self._NCircles + 2]
        self._nAllEdges = self._nRadialEdges + self._nCircularEdges
        self._edges_All = [None] * self._nAllEdges
        self._distance_edges_All = np.empty(self._nAllEdges)
        self._azimuth_edges_All = np.empty(self._nAllEdges)
        self._lenght_edges_All = np.empty(self._nAllEdges)
        self._typeOfLinks_All = [None] * self._nAllEdges
        self._edges_All = [None] * self._nAllEdges
        self._edgesID_All = np.empty(self._nAllEdges, dtype= int)
        
        stopEdgeID = 0
        startEdgeID = start
        startNodeID = 0
        stopNodeID = 0
        startNodeID_Sec = self._nMainNodes #номер начальной вспомогательной вершины
        stopNodeID_Sec = self._nMainNodes #номер начальной вспомогательной вершины
        #соединяем вершины первого промежуточного слоя с нулевой вершиной 
        self.AddRadialEdge(startNodeID_Sec, 0, startEdgeID, startEdgeID, "mr")
        startEdgeID += 1
        self.AddRadialEdge(startNodeID_Sec+1, 0, startEdgeID, startEdgeID, "mr")
        startEdgeID += 1
        
        self.AddRadialEdge(startNodeID_Sec+2, 0, startEdgeID, startEdgeID, "mr")
        startEdgeID += 1
        
        self.AddRadialEdge(startNodeID_Sec+3, 0, startEdgeID, startEdgeID, "mr")
        startEdgeID += 1
        
        #elf._distance_nodes_All[0] =
        nSmaller = 4#количество вершин в меньшем слое (в принципе можно вычислять, просто делить пополам)
        
        startNodeID_Sec = self._nMainNodes
        stopNodeID_Sec = startNodeID_Sec + nSmaller
        startNodeID = 1#нумерация вершин 1-го основного круга
        stopNodeID = 9
        nNodes = 4
        for i in range(3, self._NCircles +2):
            '''каждая итерация --- просмотр кругов с верщинами 2^i,
            первый круг основной, оставшиеся --- второстепенные'''
            nNodes = self._PowerOfTwo[i]#кол-во вершин во всех кругах данной итерации
            #сначала соединяем основной с предыдущим вспомогательным
            stopNodeID = startNodeID + nNodes
            indexesOfBigger = np.arange(startNodeID, stopNodeID)#индексы вершин основного
            indexesOfSmaller =  np.arange(startNodeID_Sec, stopNodeID_Sec)
            stopEdgeID = startEdgeID + nSmaller
            
            self.AddRadialEdgesBetweenCircles(indexesOfBigger, indexesOfSmaller, startEdgeID, stopEdgeID, "mr")
            startEdgeID += nSmaller
            #nSecCircles --- кол-во второстепенных кругов на данной итерации цикла
            #содиняем первый вспомогательный с основным
            
            startNodeID_Sec += nSmaller
            stopNodeID_Sec = startNodeID_Sec + nNodes 
            indexesOfBigger = np.arange(startNodeID_Sec, stopNodeID_Sec)#индексы вершин основного
            indexesOfSmaller =  np.arange(startNodeID, stopNodeID)
            stopEdgeID = startEdgeID + nNodes
            self.AddRadialEdgesBetweenCircles(indexesOfBigger, indexesOfSmaller, startEdgeID, stopEdgeID, "mr")
            startEdgeID += nNodes
            nSecCircles = (self._PowerOfTwo[i+1] - self._PowerOfTwo[i])//self._PowerOfTwo[2]-1
                        
            #пробегаем по дополнительным кругам (первый дополнительный мы уже соединили
            #с предыдущим основным, поэтому начинаем со второго)
            
            for j in range(1, nSecCircles):
                nextStartNodeID_Sec = stopNodeID_Sec
                stopNodeID_Sec = startNodeID_Sec + nNodes
                stopEdgeID = startEdgeID + nNodes
                indBigger = np.arange(nextStartNodeID_Sec, nextStartNodeID_Sec + nNodes)
                indSmaller = np.arange(startNodeID_Sec, stopNodeID_Sec)
                stopEdgeID = startEdgeID + nNodes
                self.AddRadialEdgesBetweenCircles(indBigger, indSmaller, startEdgeID, stopEdgeID, "mr")
                startNodeID_Sec = stopNodeID_Sec
                stopNodeID_Sec += nNodes
                startEdgeID = stopEdgeID
            nSmaller = nNodes
            startNodeID += nNodes 
            startEdgeID = stopEdgeID                
            
        #осталось соединить последний дополнительный круг с последним основным
        stopNodeID_Sec = startNodeID_Sec + nNodes
        stopEdgeID = startEdgeID + nNodes
        indBigger = np.arange(startNodeID, startNodeID + 2 * nNodes)#в большом круге в 2 раза больге вершин
        indSmaller = np.arange(startNodeID_Sec, stopNodeID_Sec)
        stopEdgeID = startEdgeID + nNodes
        self.AddRadialEdgesBetweenCircles(indBigger, indSmaller, startEdgeID, stopEdgeID, "mr")
        startEdgeID = stopEdgeID    
            
        return startEdgeID

    """
            def AddRadialEdgesBetweenCircles(self, indexesOfBigger, indexesOfSmaller, start, stop):
            добавляет ребра между соседними главными окружностями, передаются
            индексы вершин большого слоя и нидексы вершин меньшего слоя

            Поскольку для хранения ребер используются списка, то передававть ребра
            как индексы бесполезно. Дело в том, что при записи в список (а не в массив numpy)
            нельзя использовать хаотично расположенные индексы, можно только срезы.

            indexesOfBigger, indexesOfSmaller --- индексы вершин большего и меньшего слоев.

            start, stop --- границы линков для ID (записываем подряд идущие номера). 
        """

    def AddRadialEdgesBetweenCircles(self, indexesOfBigger, indexesOfSmaller, start, stop, type):
        #проверить, что большой массив в два раза больше
        #у нас два случая (первый --- в большой круге вершин в два раза больше), второй случай  кол-во одинаков
        if (len(indexesOfBigger) == len(indexesOfSmaller)):
            indexes = indexesOfBigger
        else: 
            indexes = indexesOfBigger[::2]
        self._edges_All[start:stop] = zip(indexes, indexesOfSmaller)
        # вычисление расстояния и азимута через среднюю точку
        n = len(indexes)
        dist = np.empty(n)
        az = np.empty(n)
        dist, az= self.getDistAndAzOfMiddlePoints(self._nodesID_All[indexes],
                                                                     self._nodesID_All[indexesOfSmaller])
        self._distance_edges_All[start:stop] = dist
        # хотим привести азимуты к положительным значениям
        mask = (az < 0)
        az[mask] = 2 * math.pi + az[mask]  # имеенно прибавляем, так как число отрицательное
        self._azimuth_edges_All[start:stop] = az

        ##################################################################
        self._lenght_edges_All[start:stop] = self.getDistBetweenPoints(self._nodesID_All[indexes], self._nodesID_All[indexesOfSmaller])
        self._edgesID_All[start:stop] = np.arange(start, stop)
        self._typeOfLinks_All[start:stop] = [type] * (stop - start)

    '''
    Метод def AddRadialEdge(self, ind1, ind2, indexOfLink, linkID):
        добавляет одно ребро и его характеристики
    '''

    def AddRadialEdge(self, ind1, ind2, indexOfLink, linkID, type):
        self._edges_All[indexOfLink] = (ind1, ind2)
        middle_point = self.ComputeMiddlePoint(self._nodesID_All[ind1], self._nodesID_All[ind2])

        self._distance_edges_All[indexOfLink] = np.linalg.norm(middle_point)
        #приводим азимут к положительному значению, если это необходимо
        if (self._azimuth_edges_All[indexOfLink] < 0):
            self._azimuth_edges_All[indexOfLink] = 2 * math.pi + self.getAzimuth(middle_point)
        else:
            self._azimuth_edges_All[indexOfLink] =  self.getAzimuth(middle_point)
        self._lenght_edges_All[indexOfLink] = np.linalg.norm(self._pos_All[ind1] - self._pos_All[ind2])
        #когда используем функцию норма, мы берем разность (у этой функции один аргумент)
        self._edgesID_All[indexOfLink] = linkID
        self._typeOfLinks_All[indexOfLink] = type

    """
            AddCircularEdges(self, indexes, start, stop, typeOfEdge):
            добавляет реадиальные ребра одной окружности. 
            
            Номера элементов окружности передаются через indexes.
            
            Выделение индексов решено поручить основной процедуре, а из нее
            вызывать данный метод.

                  

            start, stop --- границы линков для ID (записываем подряд идущие номера). 
        """
    def AddCircularEdges(self, indexes, start, stop, typeOfEdge):
        #проверить, что большой массив в два раза больше
        n = len(indexes)
        self._edges_All[start:stop-1] = zip(self._nodesID_All[indexes[0:n- 1]], self._nodesID_All[indexes[1:n]])
        self._edges_All[stop-1] = (self._nodesID_All[indexes[n-1]], self._nodesID_All[indexes[0]])
        #вычисление расстояния и азимута через среднюю точку
        dist = np.empty(n)
        az = np.empty(n)
        dist[0:n-1], az[0:n-1] = self.getDistAndAzOfMiddlePoints(self._nodesID_All[indexes[0:n- 1]], self._nodesID_All[indexes[1:n]])
        dist[n-1], az[n-1] = self.getDistAndAzimuth(self.ComputeMiddlePoint(self._nodesID_All[indexes[n-1]], self._nodesID_All[indexes[0]]))
        self._distance_edges_All[start:stop] = dist
        #хотим привести азимуты как положительным значениям
        mask = (az < 0)
        az[mask] = 2 * math.pi + az[mask]#имеенно прибавляем, так как число отрицательное
        self._azimuth_edges_All[start:stop] = az

        ##################################################################
        leng = np.empty(n)
        leng[0:n - 1] = az = self.getDistBetweenPoints(self._nodesID_All[indexes[0:n - 1]],
                                                       self._nodesID_All[indexes[1:n]])
        leng[n - 1] = np.linalg.norm(self._pos_All[indexes[n-1]]-self._pos_All[indexes[0]])
        # когда используем функцию норма, мы берем разность (у этой функции один аргумент)
        self._lenght_edges_All[start:stop] = leng
        self._edgesID_All[start:stop] = np.arange(start, stop)
        self._typeOfLinks_All[start:stop]  = [typeOfEdge] * n

    #######################################################################################
    #######################################################################################
    #######################################################################################
    #ВЫЧИСЛИТЕЛЬНЫЕ ПРОЦЕДУРЫ (ЧАСТЬ ПРОЦЕДУР РАБОТАЕТ С МАССИВАМИ)

    """
        def getAzimuth(self, coord):
        
        Вычисляет азимут точки и приводит его к положительному значению
    """
    def getAzimuth(self, coord):
        #можно использовать функцию arctan2, которая получаем угол со знаком
        ang = np.arctan2(coord[1], coord[0])#это y/x со знаком
        if (ang >= 0):
            return ang
        else:
            return 2 * math.pi + ang#именно + т.к. число отрицательное

    """
            def getDistAndAzimuth(self, coord):

            Вычисляет модуль и азимут точки и приводит его к положительному значению
        """
    def getDistAndAzimuth(self, coord):
        dist = np.linalg.norm(coord)
        az = np.arctan2(coord[1], coord[0])#это y/x со знаком
        return dist, az

    """
                def ComputeCoord(self, radius, azimuth):

                Вычисляет декартовы координаты точки
    """

    def ComputeCoord(self, radius, azimuth):
        return np.array([radius * np.cos(azimuth), radius * np.sin(azimuth)])


    """
        В функции def ComputeMiddlePoint(self, numPoint1, numPoint2)
        предпологается, что точки кортежи длины 2. 
        Вычисляется через исходные координаты. 
        Передаются идентификаторы точек
        Предполагается, что точки лежат на одной окружности.
        
        
    """
    def ComputeMiddlePoint(self, numPoint1, numPoint2):
        coord1 = self._pos_All[numPoint1]
        coord2 = self._pos_All[numPoint2]
        return (coord1 + coord2)/2

    """
           В функции def ComputeMiddlePointOnArc(self, numPoint1, numPoint2)
           предпологается, что точки находятся на равном расстоянии от начала координат.
           Вычисляется точки на окружности соотвествующего радиуса, лежащая на середине дуги.
           
           Алгоритм прост: находим середину отрезка, ее азимут и есть азимут точки на окружности,
           а радиус совпадает с радиусами данных точек.
           
           Точки заданы не координатами, а номерами вершин графа, по этим номерам
           мы получаем координаты.


    """

    def ComputeMiddlePointOnArc(self, numPoint1, numPoint2):
        coord1 = self._pos_All[numPoint1]
        coord2 = self._pos_All[numPoint2]
        middlePoint = (coord1 + coord2)/2
        radius = self._distance_nodes_All[numPoint1]
        return self.ComputeCoord(radius, np.arctan2(middlePoint[1], middlePoint[0]))

    """
               В функции ComputeMiddlePointForArrOfNums(self, arr_num1, arr_num2)
               
               Передаются массивы равных размеров, в каждом из которых значения --- номера точек.
               Вычисляется массив средних точек.

               (По сути векторизация)

    """

    def ComputeMiddlePointForArrOfNums(self, arr_num1, arr_num2):
        arr_coord1 = self._pos_All[arr_num1]
        arr_coord2 = self._pos_All[arr_num2]
        return (arr_coord1 + arr_coord2)/2

    """
                   В функции getDistAndAzOfMiddlePoints(self, arr_num1, arr_num2)

                   Передаются массивы равных размеров, в каждом из которых значения --- номера точек.
                   Вычисляется радиусы и азимуты середин соответствующих отрезков.

                   (По сути векторизация)

        """

    def getDistAndAzOfMiddlePoints(self, arr_num1, arr_num2):
        middle_Points = self.ComputeMiddlePointForArrOfNums(arr_num1, arr_num2)

        x = middle_Points[:, 0]#отделяем координаты точек массивов, чтобы использовать их по отдельности
        y = middle_Points[:, 1]
        arr_dist = np.sqrt(x ** 2 + y ** 2)
        arr_az = np.arctan2(y, x)
        return arr_dist, arr_az

    """
                       В функции getDistBetweenPoints(self, arr_num1, arr_num2)

                       Передаются массивы равных размеров, в каждом из которых значения --- номера точек.
                       Вычисляется расстояния между соотвествующим парами точек

                       (По сути векторизация)

            """

    def getDistBetweenPoints(self, arr_num1, arr_num2):
        points_1 = self._pos_All[arr_num1]
        points_2 = self._pos_All[arr_num2]

        x1 = points_1[:, 0]  # отделяем координаты точек массивов, чтобы использовать их по отдельности
        y1 = points_1[:, 1]
        x2 = points_2[:, 0]  # отделяем координаты точек массивов, чтобы использовать их по отдельности
        y2 = points_2[:, 1]
        arr_dist = np.sqrt((x2-x1) ** 2 + (y2-y1) ** 2)

        return arr_dist


    """
                фУНКЦИЯ azimuthToDegrees(self, arr):
                переводит массив радиан, в массив градусов

                
        """
    def azimuthToDegrees(self, arr):
        return (arr * 180.0)/math.pi

    """
            В функции def MovePoint(self, point, move_x, move_y)
            производим смещение точки. 
            
            Если поумнее все было бы организовано и точки не хранились бы кортежами,
            а массивами, то можно было бы использовавть встроенные операции.
    """

    def MovePoint(self, point, move_x, move_y):
        return point[0] + move_x, point[1] + move_y

    def MovePoint2(self, point, coord):
        return (point[0] + coord[0], point[1] + coord[1])
        









        

    
    def GraphToGeoPandas(self):
        #чтобы вывести на карту сдвигаем все коордианты
        offsetX = 177500.0
        offsetY = 661500.0

        coordOffset_x = self._pos_x_All + offsetX
        coordOffset_y = self._pos_y_All + offsetY
        coordOffset = list(zip(coordOffset_x, coordOffset_y))
        #G = nx.Graph()    
        #G.add_nodes_from(nodes)
        #pd.set_option('display.float_format', '{:.2f}'.format)
        # здесь нужно будет выводить азимуты в градусах, мы переведем азимуты в градуы
        #azimuth_nodes = (self._azimuth_nodes * 180) / (math.pi)
        #azimuth_nodes_sec = (self._azimuth_nodes_sec * 180) / (math.pi)
        azimuth_nodesAll = (self._azimuth_nodes_All * 180) / (math.pi)
        my_columns = {'node_ID', 'x', 'y', 'Distance', 'Azimuth'}
        #выводим информацию о вершинах
        
        df_Nodes = pd.DataFrame({'FID': self._nodesID_All, 'NodeID': self._nodesID_All, 'x': coordOffset_x,
                           'y': coordOffset_y, 'Distance': self._distance_nodes_All, 'Azimuth': azimuth_nodesAll})
        #df_Nodes.style.format('{:.2f}')
        gdf_Nodes = gpd.GeoDataFrame(df_Nodes, geometry=gpd.points_from_xy(df_Nodes.x, df_Nodes.y))
        #gdf_Nodes = gdf_Nodes.set_crs("EPSG:2039 - Israel 1993 / Israeli TM Grid")
        #gdf_Nodes.crs = "EPSG:2039 - Israel 1993 / Israeli TM Grid"
        gdf_Nodes.to_file(self._Path+'Nodes.shp')
        ########################################################
        ###########################################################
        ###########################################################

        ########################################################
        ###########################################################
        ###########################################################
        #информация о ребрах
        my_columns = ['FID' ,'LinkID', 'FNode', 'TNode', 'Distance', 'Azimuth', 'Length', 'LinkType']
        df_edges = pd.DataFrame(columns = my_columns)

        #для более эффективного присваивания в DataFrame делаем unzip списка ребер
        start, terminal = zip(*self._edges_All)
        '''для копирования в столбцы DataFrame
                    ребро удобно разбить на две колонки'''        
        #terminal2, start2 = zip(*self._circularEdges)#считаем, что ребра идут от больших номеров к меньшим


        df_edges['FNode'] = start
        df_edges['TNode'] = terminal
        #считаем расстояние и азимут для радиальных линий
        '''nRadialEdges = self._nRadialEdges
        df1 = df_edges.iloc[0:nRadialEdges]
        df1['Azimuth'] = azimuth_nodesAll[df1['FNode']]
        df1['Distance'] = (self._distance_nodes_All[df1['FNode']]+self._distance_nodes_All[df1['TNode']])/2'''

        df_edges['Distance'] = self._distance_edges_All
        df_edges['Azimuth'] = self.azimuthToDegrees(self._azimuth_edges_All)
        df_edges['Length'] = self._lenght_edges_All
        #считаем расстояние и азимут для круговых линий
        '''df1 = df_edges.iloc[nRadialEdges:df_edges.shape[0]]
        df1['Distance'] = self._distance_nodes_All[df1['FNode']]
        #(df1['FNode']+df1['TNode'])/2
        df1['Azimuth'] = (azimuth_nodesAll[df1['FNode']] + azimuth_nodesAll[df1['FNode']])/2
        df_edges['Distance'].iloc[nRadialEdges:df_edges.shape[0]] = df1['Distance']

        df_edges['Azimuth'].iloc[nRadialEdges:df_edges.shape[0]] = df1['Azimuth']
        df_edges['Distance'] = df_edges['Distance'].astype(float)
        df_edges['Azimuth'] = df_edges['Azimuth'].astype(float)'''
        df_edges['LinkID'] = np.arange(df_edges.shape[0])
        df_edges['LinkType'] = self._typeOfLinks_All
        df_edges['FID'] = df_edges['LinkID']
        #lines =  pd.DataFrame(index=range(df_edges.shape[0]))
        #df_edges['lines'] = df_edges.apply(lambda row: LineString([coordOffset[row['FNode']], coordOffset[row['TNode']]]), axis=1)

        '''ПРИМЕНЕНИЕ apply
        mask = df_edges['LinkType'].isin(['mc', 'nc'])
        #добавляем середину в линию
        df_edges.loc[mask, 'middlepoint'] = df_edges[mask].apply(lambda row: self.ComputeMiddlePointOnArc(row['FNode'], row['TNode']), axis=1)
        #для middlepoint смещение не учтено
        df_edges.loc[mask, 'middlepoint'] = df_edges[mask].apply(lambda row: self.MovePoint(row['middlepoint'], offsetX, offsetY), axis=1)
        df_edges.loc[mask, 'lines'] = df_edges[mask].apply(lambda row: LineString([coordOffset[row['FNode']], row['middlepoint'],
                                                                                                   coordOffset[row['TNode']]]), axis=1)
        df_edges.loc[~mask, 'lines'] = df_edges.loc[~mask].apply(lambda row: LineString([coordOffset[row['FNode']], coordOffset[row['TNode']]]), axis=1)

        lines = df_edges['lines']
        #удаляем столбцы
        df_edges = df_edges.drop(['middlepoint', 'lines'], axis=1)
        ПРИМЕНЕНИЕ apply(конец)'''
        ##################################################
        #типы ребер
        #df_edges['LinkType'][0:nRadialEdges] = self._typeOfRadialLinks
        #df_edges['LinkType'][nRadialEdges:] = self._typeOfCircularLinks
        ###################################################
        lines = df_edges.apply(lambda row: LineString([coordOffset[row['FNode']], coordOffset[row['TNode']]]), axis=1)
        #lines = df_edges['lines']

        gdf_edges = gpd.GeoDataFrame(df_edges, geometry = lines)
        #gdf_edges = gdf_edges.set_crs("EPSG:2039 - Israel 1993 / Israeli TM Grid")
        gdf_edges.to_file(self._Path+'Links.shp')
        #gdf_edges.to_file(self._Path+'my2geo.geojson', driver='GeoJSON')
        '''for i in range(len(self._edges)):
            new_row={'id':i, 'start point':self._pos_int[self._edges[i][0]], 'terminal point': self._pos_int[self._edges[i][1]],
                     'type of edge': 'straight'}
            df_edges=df_edges.append(new_row, ignore_index = True)
        for i in range(len(self._circular_edges)):
            new_row={'id':i, 'start point':self._pos_int[self._circular_edges[i][0]], 'terminal point': self._pos_int[self._circular_edges[i][1]],
                     'type of edge': 'radial'}
            df_edges=df_edges.append(new_row, ignore_index = True)'''   
        
        #df_edges['type of edge'] = 'straight'
        
        #df_edges['start point'].append()
        #df_edges['terminal point'].append(terminal)
        
        
        #lines = df_edges.apply(lambda row: LineString([row['start point'], row['terminal point']]), axis=1)
        #zip(df_edges['start point'], df_edges['terminal point'])
        
        #gdf2.to_file('my2geo.geojson', driver='GeoJSON') 


        

        
       
#Пример дял запуска программы

'''s = GraphRadialCity(4, 50)
s.CreateRadialGraph()
s.GraphToGeoPandas()'''