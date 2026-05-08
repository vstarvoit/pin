from createWindowsWindow import AppController
import threading
import time


ac = AppController()
ac.start()
ac.hideTitleBar()
ac.join()