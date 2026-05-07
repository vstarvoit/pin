import ctypes
from ctypes import wintypes
from typing import Final
import winStructures
from winStructures import *
import uuid
import threading
from PIL import Image
import numpy as np

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32
comdlg32 = ctypes.windll.comdlg32
msimg32 = ctypes.windll.msimg32
comctl32 = ctypes.windll.comctl32

WM_EXITSIZEMOVE: Final[int] = 0x0232
WM_DESTROY: Final[int] = 0x0002
WM_PAINT: Final[int] = 0x000F
WM_SIZE: Final[int] = 0x0005
SRCCOPY: Final[int] = 0x00CC0020
IMAGE_BITMAP: Final[int] = 0
LR_LOADFROMFILE: Final[int] = 0x00000010
WS_OVERLAPPEDWINDOW: Final[int] = 0x10CF0000
WS_POPUP: Final[int] =0x80000000  
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
GWL_EXSTYLE: Final[int] = -20
WS_EX_TOPMOST: Final[int] = 0x00000008
WM_HSCROLL: Final[int] = 0x0114
WM_COMMAND: Final[int] = 0x0111
WS_CHILD: Final[ctypes.c_long] = 0x40000000
WS_VISIBLE: Final[ctypes.c_long] = 0x10000000
TBS_AUTOTICKS: Final[int] = 0x0001
TBM_SETRANGE: Final[int] = 0x0401
TBM_SETPOS: Final[int] = 0x0405
TBM_GETPOS: Final[int] = 0x0400

class UIThread:
    window = None
    
    def run(self, ready:threading.Event, imagePath:str = None, windowName:str = "Window", width:int = 800, height:int = 600):
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

    def start(self, imagePath:str = None, windowName:str = "Window", width:int = 800, height:int = 600):
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
    alpha:int = 255
    slider = None
    original_bitmap = None
    scaled_bitmap = None

    def loadImage(self, path: str):
        img = Image.open(path).convert("RGBA")
        width, height = img.size

        arr = np.array(img, dtype=np.uint8)

        # premultiply alpha
        alpha = arr[:, :, 3:4] / 255.0
        arr[:, :, :3] = (arr[:, :, :3] * alpha).astype(np.uint8)

        # RGBA → BGRA 
        arr = arr[:, :, [2, 1, 0, 3]]

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB

        bits = ctypes.c_void_p()

        hdc = user32.GetDC(None)

        hbitmap = gdi32.CreateDIBSection(
            hdc,
            ctypes.byref(bmi),
            0,
            ctypes.byref(bits),
            None,
            0
        )

        user32.ReleaseDC(None, hdc)

        if not hbitmap:
            raise RuntimeError("CreateDIBSection failed")

        # copy pixel data
        ctypes.memmove(bits, arr.tobytes(), arr.nbytes)

        return hbitmap, width, height

    def loadBitmap(self, filename: str):
        hbitmap, w, h = self.loadImage(filename)

        if self.original_bitmap:
            gdi32.DeleteObject(self.original_bitmap)

        self.original_bitmap = hbitmap

        self.image_width = w
        self.image_height = h

        self.resizeBitmapToWindow()
        self.renderLayered()
        user32.UpdateWindow(self.hwnd)
    
    def resizeBitmapToWindow(self):
        if not self.original_bitmap:
            return

        rect = RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))   

        width = rect.right - rect.left
        height = rect.bottom - rect.top 

        if width <= 0 or height <= 0:
            return

        screen_dc = user32.GetDC(None)

        src_dc = gdi32.CreateCompatibleDC(screen_dc)
        dst_dc = gdi32.CreateCompatibleDC(screen_dc)

        old_src = gdi32.SelectObject(src_dc, self.original_bitmap)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0

        bits = ctypes.c_void_p()

        new_bitmap = gdi32.CreateDIBSection(
            screen_dc,
            ctypes.byref(bmi),
            0,
            ctypes.byref(bits),
            None,
            0
        )

        old_dst = gdi32.SelectObject(dst_dc, new_bitmap)

        blend_fn = BLENDFUNCTION()
        blend_fn.BlendOp = 0          # AC_SRC_OVER
        blend_fn.BlendFlags = 0
        blend_fn.SourceConstantAlpha = 255
        blend_fn.AlphaFormat = 1      # AC_SRC_ALPHA

        msimg32.AlphaBlend(
            dst_dc,
            0, 0, width, height,
            src_dc,
            0, 0,
            self.image_width, self.image_height,
            blend_fn  
        )

        gdi32.SelectObject(src_dc, old_src)
        gdi32.SelectObject(dst_dc, old_dst)

        gdi32.DeleteDC(src_dc)
        gdi32.DeleteDC(dst_dc)

        user32.ReleaseDC(None, screen_dc)

        if self.scaled_bitmap:
            gdi32.DeleteObject(self.scaled_bitmap)

        self.scaled_bitmap = new_bitmap

        self.bmp_width = width
        self.bmp_height = height

    def renderLayered(self):
        bitmap = self.scaled_bitmap
        if not bitmap:
            return

        screen_dc = user32.GetDC(None)
        mem_dc = gdi32.CreateCompatibleDC(screen_dc)

        old_obj = gdi32.SelectObject(mem_dc, bitmap)

        rect = RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))

        win_width = rect.right - rect.left
        win_height = rect.bottom - rect.top

        size = SIZE(win_width, win_height)   # use full window size, not client size
        pt_src = POINT(0, 0)
        pt_dst = POINT(rect.left, rect.top)

        blend = BLENDFUNCTION()
        blend.BlendOp = 0
        blend.BlendFlags = 0
        blend.SourceConstantAlpha = self.alpha
        blend.AlphaFormat = 1

        user32.UpdateLayeredWindow(
            self.hwnd, screen_dc,
            ctypes.byref(pt_dst),
            ctypes.byref(size),
            mem_dc,
            ctypes.byref(pt_src),
            0,
            ctypes.byref(blend),
            0x00000002
        )

        gdi32.SelectObject(mem_dc, old_obj)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(None, screen_dc)

    def windowProcedure(self, hwnd, msg, wparam, lparam):
        if msg == WM_DESTROY:
            self.cleanup()
            user32.PostQuitMessage(0)     
            return 0
        elif msg == WM_PAINT:
            ps = PAINTSTRUCT()
            hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))

            rect = RECT()
            user32.GetClientRect(hwnd, ctypes.byref(rect))

            if not self.original_bitmap:
                hbr = gdi32.GetStockObject(0)  # WHITE_BRUSH
                user32.FillRect(hdc, ctypes.byref(rect), hbr)

                user32.DrawTextW(
                    hdc,
                    "No image loaded",
                    -1,
                    ctypes.byref(rect),
                    0x00000001 | 0x00000004  # DT_CENTER | DT_VCENTER
                )
            else:
                mem_dc = gdi32.CreateCompatibleDC(hdc)

                old_obj = gdi32.SelectObject(mem_dc, self.original_bitmap)
                if not old_obj:
                    gdi32.DeleteDC(mem_dc)
                    user32.EndPaint(hwnd, ctypes.byref(ps))
                    return 0

                bmp = BITMAP()
                gdi32.GetObjectW(self.original_bitmap, ctypes.sizeof(bmp), ctypes.byref(bmp))

                gdi32.SetStretchBltMode(hdc, 0x0003)  # HALFTONE

                width = rect.right - rect.left
                height = rect.bottom - rect.top

                gdi32.StretchBlt(
                    hdc,
                    0, 0,
                    width, height,
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
            slider_width = width // 2
            slider_height = 30
            x = (width - slider_width) // 2
            y = height - slider_height - 70  # 20px above button

            user32.MoveWindow(
                self.slider,
                x, y,
                slider_width, slider_height,
                True
            )
            return 0
        elif msg == WM_HOTKEY:
            if wparam == 1:
                if self.isTitleBarHidden == True:
                    self.showEditorUI()
                elif self.isTitleBarHidden == False:
                    self.hideEditorUI()
            return 0
        elif msg == WM_CLOSE:
            user32.DestroyWindow(hwnd)  # triggers WM_DESTROY
            return 0
        elif msg == WM_EXITSIZEMOVE:
            self.resizeBitmapToWindow()
            self.renderLayered()
            user32.UpdateWindow(self.hwnd)
            user32.InvalidateRect(self.hwnd, None, True)
        
            return 0
        elif msg == WM_ERASEBKGND:
            ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            if ex & WS_EX_LAYERED:
                return 1
            return 0

        elif msg == WM_COMMAND:
            control_id = wparam & 0xFFFF

            if control_id == 1001:
                path = self.openFileDialog()
                if path:
                    self.loadBitmap(path)
                    self.hideEditorUI()
                    self.showEditorUI()
            return 0
        elif msg == WM_HSCROLL:
            if lparam == self.slider:
                pos = user32.SendMessageW(self.slider, TBM_GETPOS, 0, 0)
                self.alpha = int(pos * 2.55)
                if self.original_bitmap:
                    self.resizeBitmapToWindow()
                    self.renderLayered()

            
        # self.printError()

        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def showEditorUI(self):
        self.disableLayered()
        self.showTitleBar()
        self.showSubWindow(self.button)
        user32.SendMessageW(self.slider, TBM_SETPOS, 1, self.alpha)
        self.showSubWindow(self.slider)
        user32.InvalidateRect(self.hwnd, None, True)
        user32.UpdateWindow(self.hwnd)
        user32.RedrawWindow(self.hwnd, None, None, 0x0085)  # RDW_ERASE | RDW_INVALIDATE | RDW_UPDATENOW | RDW_ALLCHILDREN


    def hideEditorUI(self):
        self.hideSubWindow(self.button)
        self.hideSubWindow(self.slider)
        self.hideTitleBar()
 
        if self.original_bitmap:
            self.enableLayered()   
            self.renderLayered()   
        else:
            self.disableLayered()
            user32.RedrawWindow(self.hwnd, None, None, 0x0085)

    def disableLayered(self):
        style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        style &= ~WS_EX_LAYERED
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, style)
        user32.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            0x0027  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )
 
    def enableLayered(self):
        style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, style)
        user32.SetWindowPos(
            self.hwnd, 0, 0, 0, 0, 0,
            0x0027  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
        )

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

    def showSubWindow(self, wnd):
        user32.ShowWindow(wnd, 1)
    
    def hideSubWindow(self, wnd):
        user32.ShowWindow(wnd, 0)

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
        self.slider = user32.CreateWindowExW(
            0,
            "msctls_trackbar32",  
            None,
            WS_CHILD | WS_VISIBLE | TBS_AUTOTICKS,
            50, 50, 200, 30,     # X, Y, width, height
            self.hwnd,
            2001,                # Slider ID
            self.hInstance,
            None
        )
        user32.SendMessageW(self.slider, TBM_SETPOS, 1, self.alpha)
        user32.ShowWindow(self.button, 0)
        user32.ShowWindow(self.slider, 0)
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
        user32.UpdateLayeredWindow.argtypes = [
            wintypes.HWND,
            wintypes.HDC,
            ctypes.POINTER(POINT),
            ctypes.POINTER(SIZE),
            wintypes.HDC,
            ctypes.POINTER(POINT),
            wintypes.COLORREF,
            ctypes.POINTER(BLENDFUNCTION),
            wintypes.DWORD,
        ]

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

    def setTransparency(self, alpha:int):
        self.alpha = alpha
        if self.slider:
            user32.SendMessageW(self.slider, TBM_SETPOS, 1, alpha)
        self.renderLayered()

        
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

        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style | 0x20 ) # WS_EX_TRANSPARENT
        user32.SetWindowPos(self.hwnd, -1, 0, 0, 0, 0, 0x0027)  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
    
    def unmakeClickThrough(self):
        ex_style = user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style & ~(0x20 ))  # WS_EX_TRANSPARENT
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
        if self.original_bitmap:
            gdi32.DeleteObject(self.original_bitmap)
            self.original_bitmap = None

        if self.scaled_bitmap:
            gdi32.DeleteObject(self.scaled_bitmap)
            self.scaled_bitmap = None

    def windowCleanup(self):
        if self.hwnd:
            user32.DestroyWindow(self.hwnd)
            self.hwnd = None
    
    def cleanup(self):
        self.bitmapCleanup()
        self.windowCleanup()
        self.createWindowClassCleanup()

    def refreshWindow(self):
        user32.UpdateWindow(self.hwnd)

    def __init__(self, image:str = None, windowname:str = "Pin", width: int = 800, height: int = 600): # make later image size scaled to monitor size 
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
        user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, ex_style)
        
        self.bmp_width = width
        self.bmp_height = height
        user32.ShowWindow(hwnd, SW_SHOWNORMAL)

        if image:
            self.loadBitmap(image)

        user32.UpdateWindow(hwnd)
    

if __name__ == "__main__":
    
    ac = AppController()
    ac.start()

    ac.hideTitleBar()
    ac.setTopmost()

    


    ac.join()   
