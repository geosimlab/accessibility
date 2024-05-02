# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
from qgis.PyQt.QtGui import QIcon, QFont
from .form_settings import Settings
from .form_raptor_detailed import RaptorDetailed
from .form_raptor_summary import RaptorSummary
import os

class AccessibilityTools(QWidget):
    def __init__(self):
        super().__init__()
       
        layout = QVBoxLayout()
        self.tree_widget = QTreeWidget()

        
        font = QFont()
        font.setBold(True)               

        # Добавляем группы и элементы
        self.tree_widget.setHeaderHidden(True)    
        group1 = QTreeWidgetItem(self.tree_widget,['General settings'])
        self.item1 = QTreeWidgetItem(group1, ['Set default folders, databases and parameters '])
        self.item1.setFont(0,font)
        group1.setExpanded(True)
            
        group2 = QTreeWidgetItem(self.tree_widget,['Data preparation'])
        self.item2 = QTreeWidgetItem(group2, ['Build a GTFS dictionary'])
        self.item3 = QTreeWidgetItem(group2, ['Download GTFS dictionary '])
        group2.setExpanded(True)

        group3 = QTreeWidgetItem(self.tree_widget,['Public transport accessibility, by origins or destinations'])
        self.item4 = QTreeWidgetItem(group3, ['Forward accessibility, fixed start time'])
        self.item4.setFont(0,font)
        self.item5 = QTreeWidgetItem(group3, ['Forward accessibility, follow timetable'])
        self.item6 = QTreeWidgetItem(group3, ['Backward accessibility, fixed final time'])
        self.item6.setFont(0,font)
        self.item7 = QTreeWidgetItem(group3, ['Backward accessibility, follow timetable'])
        group3.setExpanded(True)
          
        group4 = QTreeWidgetItem(self.tree_widget,['Public transport accessibility map'])
        self.item8 = QTreeWidgetItem(group4, ['Forward accessibility, fixed start time'])
        self.item8.setFont(0,font)
        self.item9 = QTreeWidgetItem(group4, ['Forward accessibility, follow timetable'])
        self.item10 = QTreeWidgetItem(group4, ['Backward accessibility, fixed final time'])
        self.item10.setFont(0,font)
        self.item11 = QTreeWidgetItem(group4, ['Backward accessibility, follow timetable'])
        group4.setExpanded(True)

        group5 = QTreeWidgetItem(self.tree_widget,['Car accessibility, by origins or destinations'])
        self.item12 = QTreeWidgetItem(group5, ['Forward accessibility'])
        self.item13 = QTreeWidgetItem(group5, ['Backward accessibility'])
        group5.setExpanded(True)

        group6 = QTreeWidgetItem(self.tree_widget,['Car accessibility map'])
        self.item14 = QTreeWidgetItem(group6, ['Forward accessibility'])
        self.item15 = QTreeWidgetItem(group6, ['Backward accessibility'])
        group6.setExpanded(True)

        group7 = QTreeWidgetItem(self.tree_widget,['Relative accessibility, PT versus Car'])
        self.item16 = QTreeWidgetItem(group7, ['Forward accessibility'])
        self.item17 = QTreeWidgetItem(group7, ['Backward accessibility'])
        group7.setExpanded(True)

        icon1 = os.path.join(os.path.dirname(__file__), 'folder.png')
        
        for group_index in range(self.tree_widget.topLevelItemCount()):
              group_item = self.tree_widget.topLevelItem(group_index)
              group_item.setIcon(0, QIcon(icon1)) 
              
        icon2 = os.path.join(os.path.dirname(__file__), 'app.png')
        for group_index in range(self.tree_widget.topLevelItemCount()):
              group_item = self.tree_widget.topLevelItem(group_index)
              for item_index in range(group_item.childCount()):
                  item = group_item.child(item_index)
                  item.setIcon(0, QIcon(icon2)) 
        
        # Добавляем QTreeWidget в макет
        layout.addWidget(self.tree_widget)

        self.setLayout(layout)
        # Подключаем обработчик сигнала itemClicked к QTreeWidget
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)

    def on_tree_item_clicked(self, item, column):
        # Создаем и отображаем диалоговое окно DialogTools
        if item == self.item1:
          dialog = Settings()
          dialog.textInfo.setPlainText("Sample description tool")
          dialog.exec_()

        if item == self.item4:
          raptor_detailed = RaptorDetailed(mode = 1, protocol_type = 2, title = "Public transport accessibility, by origins or destinations (forward accessibility, fixed start time)")
          raptor_detailed.textInfo.setPlainText("Sample description forward raptor")
          raptor_detailed.exec_()

        if item == self.item6:
          raptor_detailed = RaptorDetailed(mode = 2, protocol_type = 2, title = "Public transport accessibility, by origins or destinations (backward accessibility, fixed final time)")
          raptor_detailed.textInfo.setPlainText("Sample description backward raptor")
          raptor_detailed.exec_()  

        if item == self.item8:
          raptor_summary = RaptorSummary(mode = 1, protocol_type = 1, title = "Public transport accessibility map (forward accessibility, fixed final time)")
          raptor_summary.textInfo.setPlainText("Sample description forward raptor")
          raptor_summary.exec_()    

        if item == self.item10:
          raptor_summary = RaptorSummary(mode = 2, protocol_type = 1, title = "Public transport accessibility map (backward accessibility, fixed final time)")
          raptor_summary.textInfo.setPlainText("Sample description backward raptor")
          raptor_summary.exec_()      

    

        
    

        
