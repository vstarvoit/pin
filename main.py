from createWindowsWindow import AppController
import threading
import time


ac = AppController()
ac.start("images.bmp")



while(True):
    time.sleep(1)
    if not ac.isAlive():
        break
    ac.loadBitmap("images2.bmp")
    time.sleep(1)
    if not ac.isAlive():
        break
    ac.loadBitmap("images.bmp")


ac.join()