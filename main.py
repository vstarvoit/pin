from createWindowsWindow import CreateWindow, WindowHolder
import threading
import time


holder:WindowHolder = CreateWindow("images2.bmp")

bmp:CreateWindow.loadBitmap = holder.loadBitmap
time.sleep(3)
bmp("images.bmp")

t1 = holder.thread
t1.join()

# git commit -m "Decouple window handling from main thread"