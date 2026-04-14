from createWindowsWindow import CreateWindow
import threading

def task():
    window = CreateWindow()
    
t1 = threading.Thread(target=task)
t2 = threading.Thread(target=task)

t1.start()
t2.start()

t1.join()
t2.join()
