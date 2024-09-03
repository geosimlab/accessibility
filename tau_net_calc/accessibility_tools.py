# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QTreeWidget, 
                             QTreeWidgetItem, 
                             QVBoxLayout, 
                             QWidget
                             )
from qgis.PyQt.QtGui import QIcon, QFont
from .form_settings import Settings
from .form_raptor_detailed import RaptorDetailed
from .form_raptor_summary import RaptorSummary
from .form_car import CarAccessibility
from .form_pkl import form_pkl
from .form_relative import form_relative
from visualization import visualization
import os
import webbrowser



class AccessibilityTools(QWidget):
    def __init__(self):
        super().__init__()
       
        layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()

        self.path_to_pkl = ""
        self.dict_footpath_b_b = {}
        self.dict_footpath = {}

        font = QFont()
        font.setBold(True)               

        self.item1 = QTreeWidgetItem(self.tree_widget, ['Help and Tutorial'])
        self.item1.setFont(0,font)
        # Добавляем группы и элементы
        self.tree_widget.setHeaderHidden(True)    
        group1 = QTreeWidgetItem(self.tree_widget,['General settings'])
        #self.item1 = QTreeWidgetItem(group1, ['Set default folders, databases and parameters '])
        #self.item1.setFont(0,font)
        #group1.setExpanded(True)

        
        group1.setExpanded(True)
            
        #group2 = QTreeWidgetItem(self.tree_widget,['Data preparation'])
        #self.item2 = QTreeWidgetItem(group1, ['Select GTFS dictionary'])
        self.item3 = QTreeWidgetItem(group1, ['Build GTFS dictionary (pkl)'])
        self.item3.setFont(0,font)
        group1.setExpanded(True)

        group3 = QTreeWidgetItem(self.tree_widget,['Public transport accessibility AREA, by origins or destinations'])
        self.item4 = QTreeWidgetItem(group3, ['Forward accessibility AREA, fixed departure time'])
        self.item4.setFont(0,font)
        self.item5 = QTreeWidgetItem(group3, ['Forward accessibility AREA, schedule-based setup'])
        self.item5.setFont(0,font)
        self.item6 = QTreeWidgetItem(group3, ['Backward accessibility AREA, fixed arrival time'])
        self.item6.setFont(0,font)
        self.item7 = QTreeWidgetItem(group3, ['Backward accessibility AREA, schedule-based setup'])
        self.item7.setFont(0,font)
        group3.setExpanded(True)
          
        group4 = QTreeWidgetItem(self.tree_widget,['Public transport accessibility MAP'])
        self.item8 = QTreeWidgetItem(group4, ['Forward accessibility MAP, fixed departure time'])
        self.item8.setFont(0,font)
        self.item9 = QTreeWidgetItem(group4, ['Forward accessibility MAP, schedule-based setup'])
        self.item9.setFont(0,font)
        self.item10 = QTreeWidgetItem(group4, ['Backward accessibility MAP, fixed arrival time'])
        self.item10.setFont(0,font)
        self.item11 = QTreeWidgetItem(group4, ['Backward accessibility MAP, schedule-based setup'])
        self.item11.setFont(0,font)
        group4.setExpanded(True)

        group5 = QTreeWidgetItem(self.tree_widget,['Car accessibility AREA, by origins or destinations'])
        self.item12 = QTreeWidgetItem(group5, ['Forward accessibility'])
        self.item12.setFont(0,font)
        self.item13 = QTreeWidgetItem(group5, ['Backward accessibility'])
        self.item13.setFont(0,font)
        group5.setExpanded(True)

        group6 = QTreeWidgetItem(self.tree_widget,['Car accessibility MAP'])
        self.item14 = QTreeWidgetItem(group6, ['Forward accessibility'])
        self.item14.setFont(0,font)
        self.item15 = QTreeWidgetItem(group6, ['Backward accessibility'])
        self.item15.setFont(0,font)
        group6.setExpanded(True)
        

        group7 = QTreeWidgetItem(self.tree_widget,['Compare accessibility'])
        self.item16 = QTreeWidgetItem(group7, ['Use ready-made protocols'])
        self.item16.setFont(0,font)
        """
        self.item17 = QTreeWidgetItem(group7, ['Forward accessibility'])
        self.item17.setFont(0,font)
        self.item18 = QTreeWidgetItem(group7, ['Backward accessibility'])
        self.item18.setFont(0,font)
        """
        group7.setExpanded(True)


        """
        group8 = QTreeWidgetItem(self.tree_widget,['Tools'])
        self.item19 = QTreeWidgetItem(group8, ['Visualizaton'])
        self.item19.setFont(0,font)
        group8.setExpanded(True)
        """

        icon1 = os.path.join(os.path.dirname(__file__), 'folder.png')
        
        for group_index in range(self.tree_widget.topLevelItemCount()):
              group_item = self.tree_widget.topLevelItem(group_index)
              group_item.setIcon(0, QIcon(icon1)) 
              
        icon2 = os.path.join(os.path.dirname(__file__), 'ring.png')
        for group_index in range(self.tree_widget.topLevelItemCount()):
              group_item = self.tree_widget.topLevelItem(group_index)
              for item_index in range(group_item.childCount()):
                  item = group_item.child(item_index)
                  item.setIcon(0, QIcon(icon2)) 
        
        icon3 = os.path.join(os.path.dirname(__file__), 'help.png')
        self.item1.setIcon(0, QIcon(icon3)) 
        
        # Добавляем QTreeWidget в макет
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)
        # Подключаем обработчик сигнала itemClicked к QTreeWidget
        self.tree_widget.itemDoubleClicked.connect(self.on_tree_item_clicked)

    def on_tree_item_clicked(self, item, column):
        
        if item == self.item1:
          current_dir = os.path.dirname(os.path.abspath(__file__))
          module_path = os.path.join(current_dir, 'help', 'build', 'html')
          file = os.path.join(module_path, 'introduction.html')
          webbrowser.open(f'file:///{file}')

        if item == self.item3:
          pkl = form_pkl(title = "Build GTFS dictionary (pkl)")
          pkl.textInfo.setPlainText("Description process of building GTFS dictionary (pkl)")
          pkl.show()  

        if item == self.item4:
          raptor_detailed = RaptorDetailed(self, mode = 1, 
                                           protocol_type = 2, 
                                           title = "Public transport accessibility AREA, by origins, forward accessibility, fixed departure time", 
                                           timetable_mode = False)
          raptor_detailed.textInfo.setPlainText("Sample description forward raptor")
          raptor_detailed.show()

        if item == self.item5:
          raptor_detailed = RaptorDetailed(self, mode = 1, 
                                           protocol_type = 2, 
                                           title = "Public transport accessibility AREA, by origins, forward accessibility, departure matches the timetable", 
                                           timetable_mode = True)
          raptor_detailed.textInfo.setPlainText("Sample description forward raptor with timetable mode")
          raptor_detailed.show()    

        if item == self.item6:
          raptor_detailed = RaptorDetailed(self, mode = 2, 
                                           protocol_type = 2, 
                                           title = "Public transport accessibility AREA, by destinations, backward accessibility, fixed arrival time", 
                                           timetable_mode = False)
          raptor_detailed.textInfo.setPlainText("Sample description backward raptor")
          raptor_detailed.show() 

        if item == self.item7:
          raptor_detailed = RaptorDetailed(self, mode = 2, 
                                           protocol_type = 2, 
                                           title = "Public transport accessibility AREA, by destinations, backward accessibility, arrival time interval", 
                                           timetable_mode = True)
          raptor_detailed.textInfo.setPlainText("Sample description backward raptor")
          raptor_detailed.show()    



        if item == self.item8:
          raptor_summary = RaptorSummary(self, mode = 1, 
                                         protocol_type = 1, 
                                         title = "Public transport accessibility MAP, forward accessibility, fixed departure time", 
                                         timetable_mode = False
                                         )
          raptor_summary.textInfo.setPlainText("Sample description forward raptor")
          raptor_summary.show()    

        if item == self.item9:
          raptor_summary = RaptorSummary(self, mode = 1, 
                                         protocol_type = 1, 
                                         title = "Public transport accessibility MAP, forward accessibility, departure matches the timetable", 
                                         timetable_mode = True)
          raptor_summary.textInfo.setPlainText("Sample description forward raptor with tametable mode")
          raptor_summary.show()  

        if item == self.item10:
          raptor_summary = RaptorSummary(self, mode = 2, 
                                         protocol_type = 1, 
                                         title = "Public transport accessibility MAP, backward accessibility, fixed arrival time", 
                                         timetable_mode = False)
          raptor_summary.textInfo.setPlainText("Sample description backward raptor")
          raptor_summary.show()

        if item == self.item11:
          raptor_summary = RaptorSummary(self, mode = 2, 
                                         protocol_type = 1, 
                                         title = "Public transport accessibility MAP, backward accessibility, arrival time interval", 
                                         timetable_mode = True)
          raptor_summary.textInfo.setPlainText("Sample description backward raptor")
          raptor_summary.show()  

        if item == self.item12:
          car_accessibility = CarAccessibility(mode = 1, 
                                               protocol_type = 2, 
                                               title = "Car accessibility AREA, by origins or destinations, forward accessibility")
          #car_accessibility.textInfo.setPlainText("Sample description car accessibility")
          car_accessibility.show()

        if item == self.item13:
          car_accessibility = CarAccessibility(mode = 2, 
                                               protocol_type = 2, 
                                               title = "Car accessibility AREA, by origins or destinations, backward accessibility")
          #car_accessibility.textInfo.setPlainText("Sample description car accessibility")
          car_accessibility.show()    

        if item == self.item14:
          car_accessibility = CarAccessibility(mode = 1, 
                                               protocol_type = 1, 
                                               title = "Car accessibility MAP, forward accessibility")
          #car_accessibility.textInfo.setPlainText("Sample description car accessibility")
          car_accessibility.show()
        
        if item == self.item15:
          car_accessibility = CarAccessibility(mode = 1, 
                                               protocol_type = 1, 
                                               title = "Car accessibility MAP, backward accessibility")
          #car_accessibility.textInfo.setPlainText("Sample description car accessibility")
          car_accessibility.show()  
          
        if item == self.item16:
          relative = form_relative(title = "Compare accessibility, use ready-made protocols")
          relative.textInfo.setPlainText("Sample description compare accessibility")
          relative.show()
        
        """
        if item == self.item19:
          visual = visualization(path_protokol = "C:/temp/2024 AREA 20240714_080832",
                                 path_gtfs = "C:/Users/geosimlab/Documents/Igor/israel-public-transportation_gtfs/2024/GTFS", 
                                 layer_buildings_name = "buildings",
                                 time_travel = 60,
                                 time_interval = 5)
        """                         
          

                

    

        
    

        
