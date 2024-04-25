import time
import random

# Создание словаря из миллиона ключей
million_dict = {str(i): random.random() for i in range(10000000)}

# Чтение в цикле миллион раз по последовательным индексам и подсчёт времени
start_time = time.time()
count_over_half = 0
keys = list(million_dict.keys())
for i in range(10000000):
    if million_dict[keys[i]] > 0.5:
        count_over_half += 1
end_time = time.time()

# Время, затраченное на чтение
elapsed_time = end_time - start_time

print("Чтение заняло {:.2f} секунд".format(elapsed_time))
print("Количество значений больше 0.5:", count_over_half)

# Чтение в цикле миллион раз через метод get() и подсчёт времени
start_time = time.time()
count_over_half = 0
for i in range(10000000):
    if million_dict.get(keys[i]) is not None and million_dict.get(keys[i]) > 0.5:
        count_over_half += 1
end_time = time.time()

# Время, затраченное на чтение с использованием метода get()
elapsed_time = end_time - start_time

print("Чтение с использованием метода get() заняло {:.2f} секунд".format(elapsed_time))
print("Количество значений больше 0.5:", count_over_half)
