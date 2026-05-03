from createWindowsWindow import AppController
import threading
import time


ac = AppController()
ac.start("")
ac.setTransparencyPercent(10)
ac.hideTitleBar()
# ac.showTitleBar()
ac.setTopmost()
    

# ac.join()