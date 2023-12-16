import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from threading import Thread

class App:
    def __init__(self):
        # Main window
        self.window = tk.Tk()
        self.window.title('Webcam app')

        # Combobox
        self.cameras = self.get_cameras()
        self.combo = ttk.Combobox(self.window, values=self.cameras)
        self.combo.pack()

        # Buttons
        self.button_open = tk.Button(
            self.window, text='Open camera', command=self.open_camera)
        self.button_open.pack()
        self.button_stop = tk.Button(
            self.window, text='Stop camera', command=self.stop_camera)
        self.button_stop.pack()

        # Label for video feed
        self.label = tk.Label(self.window)
        self.label.pack()

        self.stop_thread = False
        self.cap = None

        self.window.mainloop()

    # Get list of camera indexes
    @staticmethod
    def get_cameras(max_cameras=10):
        cameras = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap is None or not cap.isOpened():
                print('Camera not found:', i)
            else:
                print('Camera found:', i)
                cameras.append(str(i))  # convert integer to string
            cap.release()
        return cameras

    # Open selected camera
    def open_camera(self):
        self.stop_thread = False
        self.cap = cv2.VideoCapture(int(self.combo.get()))  # convert string to integer

        def video_loop():
            try:
                while True:
                    if self.stop_thread:
                        break
                    success, frame = self.cap.read()
                    if success:
                        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                        img = Image.fromarray(cv2image)
                        imgtk = ImageTk.PhotoImage(image=img)
                        self.label.imgtk = imgtk
                        self.label.configure(image=imgtk)
            except:
                print("Error displaying video")

        Thread(target=video_loop).start()

    # Stop camera
    def stop_camera(self):
        if self.cap is not None:
            self.stop_thread = True
            self.cap.release()
            self.cap = None

# Create an App instance
App()
