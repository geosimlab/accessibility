import gspread
from oauth2client.service_account import ServiceAccountCredentials

class FileScenario ():
      
    def __init__(self, path_to_file, ):
    
        # Укажите путь к вашему файлу JSON с ключами доступа
        credentials = ServiceAccountCredentials.from_json_keyfile_name('path/to/your/json/file.json')

        # Подключитесь к Google Sheets
        gc = gspread.authorize(credentials)

        # Укажите имя вашего файла Google Sheets
        spreadsheet_name = 'Your Spreadsheet Name'
        sh = gc.open(spreadsheet_name)

        # Получите доступ к нужному листу в файле
        worksheet = sh.sheet1  # Можно также указать название листа

    def save(self):
        pass

if __name__ == "__main__":
    path_to_file = r'C:\Users\geosimlab\Documents\Igor\sample_gtfs\from_gtft_cut3\\'
    path_to_GTFS = r'C:\Users\geosimlab\Documents\Igor\israel-public-transportation_gtfs\\'
    
    fs = FileScenario(path_to_file)
    fs.save()
