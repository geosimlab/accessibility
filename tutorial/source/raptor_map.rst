.. _raptor_map:

Public transport: Forward/backward accessibility MAP, fixed time
================================================================
Данный режим использует для вычислений accessibility алгоритмы RAPTOR Forward and RAPTOR Backward

Предварительная подготовка
--------------------------
Необходимо предварительно подготовить следующие данные:

- GTFS словарь (Смотрите раздел :doc:`loading_data`)
- слой зданий

Слой зданий должен быть загружен в текущий проект QGIS.

Вычисление
----------
#. Открыть плагин и выбрать пункт меню 

Для режима **Forward accessibility**

*Public transport accessibility MAP -> Forward accessibility MAP, fixed departure time*.

Для режима **Backward accessibility**

*Public transport accessibility MAP -> Backward accessibility MAP, fixed arrival time*.


   .. image:: ./img/mainwindow.png
      :class: inline, border

#. Откроется диалоговое окно настроек параметров.

   .. image:: ./img/pt-fr-m.png
      :class: inline, border

#. В окне настроек необходимо указать следующие параметры:

   - :guilabel:`Dataset folder`: Выбор папки, в которой расположены файлы GTFS dictionary. В папке должны находиться файлы ``stops.pkl``, ``stoptimes.pkl``, ``transfers_dict.pkl``, ``idx_by_route_stop.pkl``, ``routes_by_stop.pkl`` и др.
   - :guilabel:`Output folder`: Выбор папки для вывода протокола работы алгоритма. Необходимо, чтобы были права на запись на данную папку.
   - :guilabel:`Layer of origins`: Выбор слоя стартовых точек из текущего проекта.

   Также необходимо указать прочие параметры в диалоговом окне.
   
   Дополнительно необходимо указать:
   
   - :guilabel:`Run aggregate`: Включение чекбокса означает, что в отчете необходимо выполнить аггрегирование по выбранному полю.
   - :guilabel:`Field to aggregate`: Имя поля для аггрегирования.
   - :guilabel:`Time interval between stored maps`: Интервал времени для группирования результатов расчетов.

   
#. Нажмите кнопку **Run** для запуска алгоритма.

#. В процессе работы алгоритма отображается информация о ходе вычислений на вкладке **Log**, в строке состояния и progressbar.

#. Процесс вычислений можно прервать, нажав на кнопку **Break**.

.. note:: Если выбрано более 10 зданий в слое :guilabel:`buildings` вычисления могут занять много времени. Отображается диалоговое окно c предупреждением.

.. _raptor_map_structure_rep:

Структура отчета
----------------
+---------------------------+------------------+
| Attribute                 | Value            |
+===========================+==================+
| Source_ID                 |                  |
+---------------------------+------------------+
| Time_interval\ :sub:`n`\  |                  |
+---------------------------+------------------+
| Value_aggr\ :sub:`n`\     |                  |
+---------------------------+------------------+

Диаграмма потоков данных
------------------------

    .. image:: ./img/flowchart4.jpg
      :class: inline, border
