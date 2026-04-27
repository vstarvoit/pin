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
comdlg32 = ctypes.windll.comdlg32

WM_DESTROY: Final[int] = 0x0002
WM_PAINT: Final[int] = 0x000F
WM_SIZE: Final[int] = 0x0005
SRCCOPY: Final[int] = 0x00CC0020
IMAGE_BITMAP: Final[int] = 0
LR_LOADFROMFILE: Final[int] = 0x00000010
WS_OVERLAPPEDWINDOW: Final[int] = 0x10CF0000
WM_APP: Final[int] = 0x8000
WM_CLOSE: Final[int] = 0x0010
SW_SHOWNORMAL: Final[int] = 0x0001
WM_ERASEBKGND: Final[int] = 0x0014
WM_HOTKEY: Final[int] = 0x0312
GWL_STYLE: Final[int] = -16
WS_SYSMENU: Final[ctypes.c_long] = 0x00080000
WS_CAPTION: Final[ctypes.c_long] = 0x00C00000
WS_THICKFRAME: Final[ctypes.c_long] = 0x00040000
WS_EX_LAYERED: Final[int] = 0x00080000
LWA_ALPHA: Final[int] = 0x00000002
GWL_EXSTYLE: Final[int] = -20
WS_EX_TOPMOST: Final[int] = 0x00000008

class UIThread:
    window = None
    
    def run(self, ready:threading.Event, imagePath:str, windowName:str = "Window", width:int = 800, height:int = 600):
        self.window = Window(imagePath, windowName, width, height)
        ready.set()
        self.window.messageLoop()

    def loadBitmap(self, path:str):
        self.window.loadBitmap(path)

    def setTransparency(self, alpha:ctypes.c_byte):
        if self.window:
            self.window.setTransparency(alpha)
        self.window.refreshWindow()

    def showTitleBar(self):
        self.window.showTitleBar()

    def hideTitleBar(self):
        self.window.hideTitleBar()

    def setTopmost(self):
        self.window.setTopmost()

    def unsetTopmost(self):
        self.window.unsetTopmost()

    def makeClickThrough(self):
        self.window.makeClickThrough()

    def unmakeClickThrough(self):
        self.window.unmakeClickThrough()

    def stop(self):
        if self.window and self.window.hwnd:
            user32.PostMessageW(self.window.hwnd, WM_CLOSE, 0, 0) 

class AppController:
    uithread:UIThread = None
    thread = None

    def __init__(self): 
        self.uithread = UIThread()

    def start(self, imagePath:str, windowName:str = "Window", width:int = 800, height:int = 600):
        ready = threading.Event()
        self.thread = threading.Thread(
            target=self.uithread.run,
            args=(ready, imagePath, windowName, width, height)
        )
        self.thread.start()
        ready.wait()

    def setTransparencyPercent(self, percent: int):
        alpha = int(255 * percent / 100)
        self.uithread.setTransparency(alpha)

    def showTitleBar(self):
        self.uithread.showTitleBar()

    def hideTitleBar(self):
        self.uithread.hideTitleBar()

    def setTransparency(self, alpha:ctypes.c_byte):
        self.uithread.setTransparency(alpha)

    def setTopmost(self):
        self.uithread.setTopmost()

    def unsetTopmost(self):
        self.uithread.unsetTopmost()

    def makeClickThrough(self):
        self.uithread.makeClickThrough()

    def unmakeClickThrough(self):
        self.uithread.unmakeClickThrough()

    def loadBitmap(self, path:str):
        self.uithread.loadBitmap(path)

    def isAlive(self) -> bool:
        return self.thread.is_alive()

    def close(self):
        if self.thread and self.thread.is_alive():
            self.uithread.stop()
            self.thread.join()

    def join(self):
        self.thread.join()


class Window:
    class_name:str = None
    windowName:str = "Window"
    bitmap = None
    hInstance = kernel32.GetModuleHandleW(None)
    hwnd = None
    isTitleBarHidden:bool = True
    button = None
    button_visible:bool = False

    def loadBitmap(self, filename:str):
        bitmap = user32.LoadImageW(
            None,
            filename,  
            IMAGE_BITMAP,
            0,
            0,
            LR_LOADFROMFILE
        )
        # self.printError()

        if not bitmap:
            raise RuntimeError("Failed to load bitmap")
        self.bitmap, bitmap = bitmap, self.bitmap
        if bitmap != None:
            gdi32.DeleteObject(bitmap)
        user32.PostMessageW(self.hwnd, WM_APP + 1, 0, 0)
        
        return self.bitmap
    
    def windowProcedure(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            self.cleanup()
            user32.PostQuitMessage(0)     
            return 0
        elif msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

            mem_dc = gdi32.CreateCompatibleDC(hdc)
            if not self.bitmap:
                user32.EndPaint(hwnd, ctypes.byref(ps))
                return 0
            
            old_obj = gdi32.SelectObject(mem_dc, self.bitmap)
            
            if not old_obj:
                gdi32.DeleteDC(mem_dc)
                user32.EndPaint(hwnd, ctypes.byref(ps))
                return 0

            bmp = BITMAP()
            gdi32.GetObjectW(self.bitmap, ctypes.sizeof(bmp), ctypes.byref(bmp))
            gdi32.SetStretchBltMode(hdc, 0x0003)
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
            user32.InvalidateRect(hwnd, None, False)
            width = lparam & 0xFFFF
            height = (lparam >> 16) & 0xFFFF

            btn_width = width // 4
            btn_height = 40

            x = (width - btn_width) // 2
            y = height - btn_height - 20

            user32.MoveWindow(
                self.button,
                x, y,
                btn_width,
                btn_height,
                True
            )
            return 0
        elif msg == WM_HOTKEY:
            if wparam == 1:
                if self.isTitleBarHidden == True:
                    self.showTitleBar()
                    self.unmakeClickThrough()
                elif self.isTitleBarHidden == False:
                    self.hideTitleBar()
                    self.makeClickThrough()
            return 0
        elif msg == WM_APP + 1:
            user32.InvalidateRect(hwnd, None, False)
            return 0
        elif msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)  # triggers WM_DESTROY
            return 0
        elif msg == WM_ERASEBKGND:
            return 1  # tell Windows "I handled it"
        elif msg == 0x0111:  # WM_COMMAND
            control_id = wparam & 0xFFFF

            if control_id == 1001:
                path = self.openFileDialog()
                if path:
                    self.loadBitmap(path)
            elif control_id == 1003:
                self.toggleClickThrough()
            return 0
            
        # self.printError()

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def openFileDialog(self):
        buffer = ctypes.create_unicode_buffer(260)

        ofn = OPENFILENAME()
        ofn.lStructSize = ctypes.sizeof(ofn)
        ofn.hwndOwner = self.hwnd
        ofn.lpstrFilter = "Images\0*.bmp;*.png\0All Files\0*.*\0"
        ofn.lpstrFile = ctypes.cast(buffer, wintypes.LPWSTR)
        ofn.nMaxFile = 260
        ofn.Flags = 0x00000008 | 0x00001000  # OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST
        ofn.lpstrTitle = "Select an image"

        if comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
            return buffer.value
        return None

    def stop(self):
        user32.PostQuitMessage(0)

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
        
        X: Final[int] = 100
        Y: Final[int] = 100
        
        hwnd = user32.CreateWindowExW(
            WS_EX_TOPMOST, 
            self.class_name,
            self.windowName,
            WS_OVERLAPPEDWINDOW,
            X, Y, width, height,
            None,
            None,
            self.hInstance,
            None
        )
        if not hwnd:
            raise RuntimeError("CreateWindowEx failed: " + ctypes.FormatError(kernel32.GetLastError()))
        self.hwnd = hwnd
        self.button = user32.CreateWindowExW(
            0,
            "BUTTON",
            "Open Image",
            0x50010000,  # WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON
            0, 0, 100, 30,
            self.hwnd,
            1001,  # ID
            self.hInstance,
            None
        )
        user32.ShowWindow(self.button, 0)
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

    def showTitleBar(self):
        style = user32.GetWindowLongW(self.hwnd, GWL_STYLE)

        new_style = style | (WS_CAPTION | WS_SYSMENU | WS_THICKFRAME)

        user32.SetWindowLongW(self.hwnd, GWL_STYLE, new_style)
        self.isTitleBarHidden = False
        user32.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            0x0027 # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )

    def hideTitleBar(self):
        style = user32.GetWindowLongW(self.hwnd, GWL_STYLE)

        new_style = style & ~(WS_CAPTION | WS_SYSMENU | WS_THICKFRAME)

        user32.SetWindowLongW(self.hwnd, GWL_STYLE, new_style)
        self.isTitleBarHidden = True
        user32.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            0x0027  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )

    def setTransparency(self, alpha:ctypes.c_byte):
        user32.SetLayeredWindowAttributes(self.hwnd, 0, alpha, LWA_ALPHA)
        
    def setTopmost(self):
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
    
        ex_style |= WS_EX_TOPMOST
        
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style)
        
        user32.SetWindowPos(
            self.hwnd, -1, 0, 0, 0, 0,
            0x0027  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )

    def makeClickThrough(self):
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)

        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style | 0x20 | 0x80000) # WS_EX_LAYERED and WS_EX_TRANSPARENT
        user32.SetWindowPos(self.hwnd, -1, 0, 0, 0, 0, 0x0027)  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
    
    def unmakeClickThrough(self):
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style & ~(0x20 | 0x80000))  # WS_EX_LAYERED and WS_EX_TRANSPARENT
        user32.SetWindowPos(self.hwnd, -1, 0, 0, 0, 0, 0x0027)  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED

    def unsetTopmost(self):
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        
        ex_style &= ~WS_EX_TOPMOST
        
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style)
        
        user32.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            0x0027  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )

    def setHotkey(self):
        user32.RegisterHotKey(self.hwnd, 1, 0x0002 | 0x0001 | 0x4000, 0x53) # MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, S key

    def unsetHotKey(self):
        user32.UnregisterHotKey(self.hwnd, 1)

    def printError(self):
        error_code = kernel32.GetLastError()
        message = ctypes.FormatError(error_code)

        print(f"Error {error_code}: {message}")

    def createWindowClassCleanup(self): # rewrite when multiple windows needed
        user32.UnregisterClassW(self.class_name ,self.hInstance)
    
    def bitmapCleanup(self):
        if self.bitmap:
            gdi32.DeleteObject(self.bitmap)
            self.bitmap = None

    def windowCleanup(self):
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
    
    def cleanup(self):
        self.bitmapCleanup()
        self.windowCleanup()
        self.createWindowClassCleanup()

    def refreshWindow(self):
        user32.InvalidateRect(self.hwnd, None, True)
        user32.UpdateWindow(self.hwnd)

    def __init__(self, image: str, windowname:str, width: int = 800, height: int = 600): # make later image size scaled to monitor size 
        self.setTypes()
        user32.DefWindowProcW.restype = LRESULT
        self.class_name = uuid.uuid4().hex
        wndclass = self.createWindowClass()
       
        # self.printError()

        try:
             hwnd = self.createWindow(width, height)
        except:
            self.cleanup()
            raise RuntimeError("Window creation failed")
        self.setHotkey()
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED)
        self.bitmap = self.loadBitmap(image)

        user32.ShowWindow(hwnd, SW_SHOWNORMAL)
        user32.UpdateWindow(hwnd)
    

if __name__ == "__main__":
    
    ac = AppController()
    ac.start("1.bmp")
    ac.setTransparencyPercent(90)
    ac.hideTitleBar()
    # ac.showTitleBar()
    ac.setTopmost()
    # ac.makeClickThrough()

    # i = 15
    # while(True):
    #     time.sleep(1)
    #     if not ac.isAlive():
    #         break
    #     ac.loadBitmap("2.bmp")

    #     time.sleep(1)
    #     if not ac.isAlive():
    #         break
    #     ac.loadBitmap("1.bmp")


    ac.join()   
