import pandas as pd

# Чтение файла CSV
file1 = r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\full gtfs rev\stop_times.txt'
file2 = r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\full gtfs rev\trips.txt'
df = pd.read_csv(file1)
trips_file = pd.read_csv(file2)

df[['hour', 'minute', 'second']] = df['arrival_time'].str.split(':', expand=True)
df['hour'] = df['hour'].astype(int)
df = df[df['hour'] <= 23]
df.arrival_time = pd.to_datetime(df.arrival_time, format='%H:%M:%S')

df = pd.merge(df, trips_file, on='trip_id')

#print (f' df {df.head()}')

# Выбор строк с route_id = 19630
filtered_df = df[df['route_id'] == 19630]

# Группировка по trip_id и подсчет количества элементов в каждой группе
trip_count = filtered_df.groupby('trip_id').size()

# Вывод результатов на экран
print(trip_count)

"""
# Фильтрация данных для поиска нужной информации
filtered_trips = df[(df['stop_id'] == 1849) & (df['arrival_time'] == '08:12:31')]


# Вывод номеров поездок, удовлетворяющих условиям
print("Номера поездок с остановкой 1849 и временем прибытия 08:12:31:")
print(filtered_trips['trip_id'].unique())
"""
"""
# Сравнение времени между строками и подсчет возрастающих и убывающих значений
# Инициализация переменных для подсчета возрастающих и убывающих значений
increasing_count = 0
decreasing_count = 0

# Переменная для отслеживания обработанных строк
processed_rows = 0

# Перебор по каждому trip_id
for trip_id, group in df.groupby('trip_id'):
    # Сортировка данных по stop_sequence внутри каждого trip_id
    group = group.sort_values('stop_sequence')
    
    # Проверка на возрастание и убывание stop_sequence внутри trip_id
    for i in range(1, len(group)):
        if group['stop_sequence'].iloc[i] > group['stop_sequence'].iloc[i-1]:
            increasing_count += 1
        elif group['stop_sequence'].iloc[i] < group['stop_sequence'].iloc[i-1]:
            decreasing_count += 1
        
        # Увеличение счетчика обработанных строк
        processed_rows += 1
        
        # Вывод промежуточной информации после каждых 1000 обработанных строк
        if processed_rows % 1000 == 0:
            print(f"Обработано {processed_rows} строк...")
        
print("Количество строк, в которых stop_sequence возрастает:", increasing_count)
print("Количество строк, в которых stop_sequence убывает:", decreasing_count)
"""
"""
# Создание столбца с предыдущим временем прибытия
df['prev_arrival_time'] = df['arrival_time'].shift(1)


# Фильтрация строк с одинаковым временем прибытия в двух подряд идущих строках
filtered_df = df[(df['arrival_time'] == df['prev_arrival_time'])]

# Удаление столбца с предыдущим временем прибытия
filtered_df = filtered_df.drop(columns=['prev_arrival_time'])


# Отфильтровать данные для stop_id 1849 и 3367
filtered_df = df[(df['stop_id'].isin([1849, 3367]))]

# Сгруппировать данные по trip_id и получить списки stop_id и время для каждого trip_id
grouped = filtered_df.groupby('trip_id')[['stop_id', 'arrival_time']].apply(lambda x: list(zip(x['stop_id'], x['arrival_time'])))

# Найти trip_id, содержащие обе остановки в нужном порядке и правильной последовательности времени
matching_trip_ids = set()
for trip_id, stops in grouped.items():
    stop1849_idx = [i for i, (stop_id, _) in enumerate(stops) if stop_id == 1849]
    stop3367_idx = [i for i, (stop_id, _) in enumerate(stops) if stop_id == 3367]
    for idx1849 in stop1849_idx:
        for idx3367 in stop3367_idx:
            
                time1849 = stops[idx1849][1]
                time3367 = stops[idx3367][1]
                if time1849 < time3367:
                    matching_trip_ids.add((trip_id, '1849 -> 3367'))
                else:
                    matching_trip_ids.add((trip_id, '3367 -> 1849'))
                    print ('!!!!!!!!!!')

# Вывести результат
for trip_id, order in matching_trip_ids:
    print(f"Trip ID: {trip_id}, Order: {order}")
"""



# Вывод результата
#print(filtered_df)