from BitmapRenderer import BitmapRenderer
import ctypes
from ctypes import wintypes
from typing import Final
import winStructures
from winStructures import *

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

WM_DESTROY: Final[int] = 0x0002
WM_PAINT: Final[int] = 0x000F
SRCCOPY: Final[int] = 0x00CC0020
IMAGE_BITMAP: Final[int] = 0
LR_LOADFROMFILE: Final[int] = 0x00000010

class CreateWindow:
    class_name:str = "WindowClass"
    windowName:str = "Window"
    bitmap = None
    hInstance = kernel32.GetModuleHandleW(None)

    def loadBitmap(self, filename:str):
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
            gdi32.SetStretchBltMode(hdc, 0x0000)
            # gdi32.BitBlt(
            #     hdc,
            #     0, 0,
            #     bmp.bmWidth,
            #     bmp.bmHeight,
            #     mem_dc,
            #     0, 0,
            #     SRCCOPY
            # )

            gdi32.StretchBlt(
                hdc,
                0, 0,
                800,
                600,
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
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def createWindowClass(self):
        wndclass = WNDCLASS()   
        # wnd_proc = WNDPROCTYPE(self.windowProcedure)
        
        wndclass.lpfnWndProc = WNDPROCTYPE(self.windowProcedure) #wnd_proc
        wndclass.lpszClassName = self.class_name
        wndclass.hInstance = self.hInstance
        wndclass.hCursor = user32.LoadCursorW(None, 32512)
        wndclass.hbrBackground = ctypes.c_void_p(5)  # COLOR_WINDOW + 1

        atom = user32.RegisterClassW(ctypes.byref(wndclass))
        if not atom:
            raise RuntimeError(ctypes.FormatError(kernel32.GetLastError()))

        return wndclass

    def createWindow(self):
        menu = user32.CreateMenu()
        
        WS_OVERLAPPEDWINDOW: Final[int] = 0x10CF0000
        X: Final[int] = 100
        Y: Final[int] = 100
        width: Final[int] = 800
        height: Final[int] = 600
        
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

        return hwnd

    def messageLoop(self):
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    
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

    def __init__(self):
        
        self.bitmap = self.loadBitmap("images.bmp")
        self.setTypes()
        user32.DefWindowProcW.restype = LRESULT
        wndclass = self.createWindowClass()

        # self.printError()

        hwnd = self.createWindow()

        user32.ShowWindow(hwnd, 1)
        user32.UpdateWindow(hwnd)
        self.messageLoop()

if __name__ == "__main__":
    window = CreateWindow()