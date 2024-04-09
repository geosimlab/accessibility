import csv

def compare_csv_files_and_get_differences(file1, file2):
    # Считываем содержимое файлов в множества строк
    set1 = set()
    with open(file1, 'r') as csv_file1:
        reader1 = csv.reader(csv_file1)
        for row in reader1:
            set1.add(tuple(row))
    
    set2 = set()
    with open(file2, 'r') as csv_file2:
        reader2 = csv.reader(csv_file2)
        for row in reader2:
            set2.add(tuple(row))
    
    # Находим различия между множествами строк
    differences = set1.symmetric_difference(set2)
    
    # Выводим различающиеся строки
    if differences:
        print("Различающиеся строки:")
        for diff in differences:
            print(diff)
    else:
        print("Файлы идентичны")


# Пример использования
file1 = r'C:\Users\geosimlab\Documents\Igor\Protocols\data1.csv'
file2 = r'C:\Users\geosimlab\Documents\Igor\Protocols\data2.csv'
compare_csv_files_and_get_differences(file1, file2)
