from PyQt5.QtWidgets import QDialogButtonBox
from .form_raptor_summary import RaptorSummary

class Settings(RaptorSummary):
    def __init__(self, 
                 mode=1, 
                 protocol_type=1, 
                 title = "Settings", 
                 timetable_mode = True):
            super().__init__(mode, protocol_type, title, timetable_mode = True )
            
            self.progressBar.setVisible(False)
            self.btnBreakOn.setVisible(False)
            self.tabWidget.removeTab(1)
                        
            self.buttonBox.clear()

            
            ok_button = self.buttonBox.addButton("Ok", QDialogButtonBox.ActionRole)
            save_button = self.buttonBox.addButton("Save", QDialogButtonBox.ActionRole)
            close_button = self.buttonBox.addButton("Close", QDialogButtonBox.RejectRole)
            
            ok_button.clicked.connect(self.on_ok)
            save_button.clicked.connect(self.on_save)
            close_button.clicked.connect(self.on_close)
    
    def on_close(self):
        self.reject()
        
    def on_ok(self):
            

        if not (self.check_folder_and_file()):
           return 0
        
        self.saveParameters()
        
   
        self.reject()

    def on_save(self):
                
        if not (self.check_folder_and_file()):
           return 0
        self.saveParameters()

        self.setMessage("Saved")