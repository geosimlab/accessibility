.. _timetable_mode:

Public transport: Forward/backward accessibility AREA/MAP, Timetable mode
=========================================================================

Данный режим является расширением режимов

*Forward/backward accessibility Area, fixed departure/arrived time* (Смотрите :doc:`раздел <raptor_area>`.)

*Forward/backward accessibility MAP, fixed departure/arrived time* (Смотрите :doc:`раздел <raptor_map>`.)

Вычисление
----------

#. Открыть плагин и выбрать пункт меню 

Для режима **Forward accessibility AREA**

*Public transport accessibility AREA -> Forward accessibility AREA, departure matches the table*.

Для режима **Backward accessibility AREA**

*Public transport accessibility AREA -> Backward accessibility MAP, arrival time interval*.

Для режима **Forward accessibility MAP**

*Public transport accessibility MAP -> Forward accessibility AREA, departure matches the table*.

Для режима **Backward accessibility MAP**

*Public transport accessibility MAP -> Backward accessibility MAP, arrival time interval*.


   .. image:: ./img/mainwindow.png
      :class: inline, border

#. Откроется диалоговое окно настроек параметров.

   .. image:: ./img/pt-tt.png
      :class: inline, border

#. Для данного режима дополнительно необходимо указать:
   
   Для режима **Forward accessibility**:

   - :guilabel:`Maximal waiting time at transfer stop, min`: Максимальное время ожидания начала поездки

   - :guilabel:`Departure interval earlist, min`: Промежуток времени, за который нужно быть на первой остановке до посадки на транспорт

   Для режима **Backward accessibility**:

   - :guilabel:`Maximal waiting time at transfer stop, min`: Максимально раннее время прибытия в конечную точку

   - :guilabel:`Departure interval latest, min`: Промежуток времени, за который нужно быть на последней остановке (здании) до заданного времени завершения поездки

Структура отчета
----------------
В зависимости от выбранного режима формируется отчет :ref:`AREA <raptor_area_structure_rep>` или :ref:`MAP <raptor_map_structure_rep>`

Диаграмма потоков данных
------------------------
Смотрите :ref:`раздел <raptor_area_flowchart>`.

