import ctypes
from ctypes import wintypes
from typing import Final
import winStructures
from winStructures import *
import uuid
import threading


user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

WM_DESTROY: Final[int] = 0x0002
WM_PAINT: Final[int] = 0x000F
WM_SIZE: Final[int] = 0x0005
SRCCOPY: Final[int] = 0x00CC0020
IMAGE_BITMAP: Final[int] = 0
LR_LOADFROMFILE: Final[int] = 0x00000010
WS_OVERLAPPEDWINDOW: Final[int] = 0x10CF0000
WM_APP: Final[int] = 0x8000

class WindowHolder:
    def __init__(self):
        self.window = None
        self.loadBitmap = None
        self.thread:threading.Thread = None

class CreateWindow:
    class_name:str = None
    windowName:str = "Window"
    bitmap = None
    hInstance = kernel32.GetModuleHandleW(None)
    hwnd = None

    @staticmethod
    def task(holder, ready_event, image, width, height):
        window = object.__new__(CreateWindow)
        CreateWindow.__init__(window, image, width, height)

        holder.window = window
        holder.loadBitmap = window.loadBitmap

        ready_event.set()
        window.messageLoop()

    def loadBitmap(self, filename:str):
        if self.bitmap != None:
            gdi32.DeleteObject(self.bitmap)
        bitmap = user32.LoadImageW(
            None,
            filename,  
            IMAGE_BITMAP,
            0,
            0,
            LR_LOADFROMFILE
        )
        if not bitmap:
            raise RuntimeError("Failed to load bitmap")
        self.bitmap = bitmap
        user32.PostMessageW(self.hwnd, WM_APP + 1, 0, 0)
        return bitmap
    
    def windowProcedure(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        elif msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

            mem_dc = gdi32.CreateCompatibleDC(hdc)

            old_obj = gdi32.SelectObject(mem_dc, self.bitmap)

            bmp = BITMAP()
            gdi32.GetObjectW(self.bitmap, ctypes.sizeof(bmp), ctypes.byref(bmp))
            gdi32.SetStretchBltMode(hdc, 0x0003)
            # gdi32.BitBlt(
            #     hdc,
            #     0, 0,
            #     bmp.bmWidth,
            #     bmp.bmHeight,
            #     mem_dc,
            #     0, 0,
            #     SRCCOPY
            # )
            rect = RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))

            width = rect.right - rect.left
            height = rect.bottom - rect.top
            gdi32.StretchBlt(
                hdc,
                0, 0,
                width,
                height,
                mem_dc,
                0, 0,
                bmp.bmWidth,
                bmp.bmHeight,
                SRCCOPY
            )

            gdi32.SelectObject(mem_dc, old_obj)
            gdi32.DeleteDC(mem_dc)
            user32.EndPaint(hwnd, ctypes.byref(ps))
            return 0
        elif msg == WM_SIZE:
            user32.InvalidateRect(hwnd, None, True)
            return 0
        elif msg == WM_APP + 1:
            user32.InvalidateRect(hwnd, None, True)
            return 0
        # self.printError()

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def createWindowClass(self):
        wndclass = WNDCLASS()   
        self.wnd_proc = WNDPROCTYPE(self.windowProcedure)
        wndclass.lpfnWndProc = self.wnd_proc
        wndclass.lpszClassName = self.class_name
        wndclass.hInstance = self.hInstance
        wndclass.hCursor = user32.LoadCursorW(None, 32512)
        wndclass.hbrBackground = ctypes.c_void_p(5)  # COLOR_WINDOW + 1

        atom = user32.RegisterClassW(ctypes.byref(wndclass))
        if not atom:
            raise RuntimeError(ctypes.FormatError(kernel32.GetLastError()))

        return wndclass

    def createWindow(self, width:int, height:int):
        menu = user32.CreateMenu()
        
        X: Final[int] = 100
        Y: Final[int] = 100
        
        hwnd = user32.CreateWindowExW(
        0, 
        self.class_name,
        self.windowName,
        WS_OVERLAPPEDWINDOW,
        X, Y, width, height,
        None,
        menu,
        self.hInstance,
        None
        )
        if not hwnd:
            raise RuntimeError("CreateWindowEx failed: " + ctypes.FormatError(kernel32.GetLastError()))
        self.hwnd = hwnd
        return hwnd

    def messageLoop(self):
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        self.createWindowClassCleanup(self.class_name)
        
    
    def setTypes(self):
        user32.DefWindowProcW.argtypes = (
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

    def printError(self):
        error_code = kernel32.GetLastError()
        message = ctypes.FormatError(error_code)

        print(f"Error {error_code}: {message}")

    def createWindowClassCleanup(self, className:str):
        user32.UnregisterClassW(className, self.hInstance)

    

    def _init(self, width, height):
        self.setTypes()
        user32.DefWindowProcW.restype = LRESULT
        self.class_name = uuid.uuid4().hex
        wndclass = self.createWindowClass()
       
        # self.printError()

        hwnd = self.createWindow(width, height)

        user32.ShowWindow(hwnd, 1)
        user32.UpdateWindow(hwnd)

    def __init__(self, image: str, width: int = 800, height: int = 600): # make later image size scaled to monitor size 
        self.bitmap = self.loadBitmap(image)
        self._init(width, height) 
    
    def __new__(cls, image: str, width: int = 800, height: int = 600) -> WindowHolder:
        holder = WindowHolder()
        ready = threading.Event()

        t1 = threading.Thread(target=cls.task, args=(holder, ready, image, width, height))
        t1.start()
        holder.thread = t1
        ready.wait()
        return holder
    

if __name__ == "__main__":
    window = CreateWindow("images.bmp")
    window.messageLoop()
    window = CreateWindow("images.bmp", 500, 500)
    window.messageLoop()
