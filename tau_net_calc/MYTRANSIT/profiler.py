import pstats

stats = pstats.Stats(r"C:\Users\geosimlab\Documents\Igor\Protocols\plugin_profile.txt")
stats.sort_stats(pstats.SortKey.TIME)  # Сортируем по времени выполнения
stats.print_stats(10)  # Выводим топ-10 наиболее времязатратных функций