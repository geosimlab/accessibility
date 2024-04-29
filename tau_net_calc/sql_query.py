import psycopg2

# Установка соединения с базой данных
conn = psycopg2.connect(
    dbname="calc_dist",
    user="postgres",
    password="postgres",
    host="localhost",
    port=5432
)

# Создание курсора
cur = conn.cursor()

# Выполнение SQL-запроса
sql_query = """
    SELECT 
        stop_id,
        building_id,
        distance
    FROM (
        SELECT 
            s.stop_id AS stop_id,
            b.osm_id AS building_id,
            ST_Distance(s.geom::geography, b.geom::geography) AS distance
        FROM 
            stops AS s
        JOIN 
            buildings AS b ON ST_DWithin(s.geom::geography, b.geom::geography, 400)
        UNION ALL
        SELECT 
            b.osm_id AS stop_id,
            s.stop_id AS building_id,
            ST_Distance(b.geom::geography, s.geom::geography) AS distance
        FROM 
            stops AS s
        JOIN 
            buildings AS b ON ST_DWithin(b.geom::geography, s.geom::geography, 400)
    ) AS distances;
"""

cur.execute(sql_query)

# Получение результатов запроса
results = cur.fetchall()

# Закрытие курсора и соединения
cur.close()
conn.close()

# Запись результатов в файл
with open(r'c:\temp\результаты.txt', 'w') as file:
    for result in results:
        file.write(f"{result[0]}, {result[1]}, {result[2]}\n")
