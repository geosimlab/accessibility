import pandas as pd
import time

start_time = time.time()

# Начальная дата и время
start_timestamp = pd.Timestamp.now()

# Timedelta для добавления к Timestamp
delta = pd.Timedelta(seconds=1)

# Цикл для сложения Timestamp и Timedelta 1000 раз
for _ in range(10000000):
    start_timestamp += delta

end_time = time.time()

# Время выполнения
execution_time = end_time - start_time
print("Время выполнения date:", execution_time, "секунд")


start_time = time.time()

x1 = 45000
x2 = 54000
# Цикл для сложения Timestamp и Timedelta 1000 раз
for _ in range(10000000):
    x3= x1 + x2

end_time = time.time()

# Время выполнения
execution_time = end_time - start_time
print("Время выполнения int:", execution_time, "секунд")