import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import threading
import winsound
import os
import sys

TARGET_CONFIDENCE = 0.75

# PyInstaller resource path
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ImageSearchBot:
    def __init__(self, root):
        self.root = root
        self.root.title("Lastwar task detector v1.1 #1667 불타는아나고")
        self.root.geometry("400x250")
        
        try:
            self.root.iconbitmap(resource_path("custom_icon.ico")) 
        except Exception as e:
            print("Cannot load the icon file.", e)

        self.is_running = False
        self.target_window_title = None
        self.template_image_path = resource_path("target_icon.png") 

        self.create_widgets()
        
    def create_widgets(self):
        # windows area
        lbl_select = tk.Label(self.root, text="Choose the 'Last War-Survival Game'!")
        lbl_select.pack(pady=5)
        
        self.combo_windows = ttk.Combobox(self.root, width=40)
        self.combo_windows.pack(pady=5)
        self.refresh_windows()
        
        btn_refresh = tk.Button(self.root, text="Refesh window list", command=self.refresh_windows)
        btn_refresh.pack(pady=2)

        # button
        frame_controls = tk.Frame(self.root)
        frame_controls.pack(pady=20)
        
        self.btn_start = tk.Button(frame_controls, text="START", bg="green", fg="white", width=15, command=self.start_monitoring)
        self.btn_start.pack(side=tk.LEFT, padx=10)
        
        self.btn_stop = tk.Button(frame_controls, text="END", bg="red", fg="white", width=15, command=self.stop_monitoring, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=10)
        
        # status
        self.lbl_status = tk.Label(self.root, text="Idle...", fg="gray")
        self.lbl_status.pack(pady=10)

    def refresh_windows(self):
        windows = gw.getAllTitles()
        clean_windows = sorted([w for w in windows if w.strip()])
        self.combo_windows['values'] = clean_windows
        if clean_windows:
            self.combo_windows.current(0)

    # START
    def start_monitoring(self):
        target = self.combo_windows.get()
        if not target:
            messagebox.showwarning("Warning", "Select the window!")
            return
        if not os.path.exists(self.template_image_path):
            messagebox.showerror("ERROR", f"File not found at:\n{self.template_image_path}")
            return

        self.target_window_title = target
        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text=f"Searching: {target}", fg="blue")
        
        self.monitor_thread = threading.Thread(target=self.run_loop, daemon=True)
        self.monitor_thread.start()

    # STOP
    def stop_monitoring(self):
        self.is_running = False
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="STOPPED", fg="red")

    def run_loop(self):
        try:
            img_array = np.fromfile(self.template_image_path, np.uint8)
            template = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
             print(f"Image load error: {e}")
             template = None

        if template is None:
            print("Failed to loading image")
            self.stop_monitoring()
            return
            
        h, w = template.shape[:2]

        while self.is_running:
            try:
                self.lbl_status.config(text="🔎 Searching..", fg="black")
                
                # find window
                windows = gw.getWindowsWithTitle(self.target_window_title)
                if not windows:
                    print("Cannot find the window.")
                    self.lbl_status.config(text="⛔ Cannot find the window!", fg="red")
                    time.sleep(1)
                    continue
                
                win = windows[0]
                if win.isMinimized:
                    self.lbl_status.config(text="⛔ Window is minimized!", fg="red")
                    time.sleep(1)
                    continue
                
                # take screenshot
                screenshot = pyautogui.screenshot(region=(win.left, win.top, win.width, win.height))
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) 

                result = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
                
                # THRESHOLD
                loc = np.where(result >= TARGET_CONFIDENCE)
                
                if len(loc[0]) > 0:
                    y_idx = loc[0][0]
                    x_idx = loc[1][0]
                    pt = (x_idx, y_idx) 
                    
                    match_confidence = result[y_idx][x_idx]
                    
                    center_x = win.left + pt[0] + w // 2
                    center_y = win.top + pt[1] + h // 2

                    self.lbl_status.config(text=f"Found! Loc:{pt}, Conf: {match_confidence:.2f}", fg="green")
                    
                    # Beep
                    winsound.Beep(1000, 200)

                    # Mouse move
                    pyautogui.moveTo(center_x, center_y, duration=0.5)
                    time.sleep(2) 
                else:
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    self.lbl_status.config(text=f"🔎 Searching.. (Max Conf: {max_val:.2f})", fg="blue")

            except Exception as e:
                print(f"ERROR: {e}")

            # CPU 사용량을 줄이고 GUI 멈춤을 방지하기 위해 약간의 대기
            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageSearchBot(root)
    root.mainloop()