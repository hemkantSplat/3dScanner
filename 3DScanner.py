from threading import Thread
import customtkinter
import os
from PIL import Image, ImageTk
import tkinter
import tkinter.messagebox
import cv2
from tkinter_webcam import webcam
import threading
import warnings
import multiprocessing
import serial
import serial.tools.list_ports

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("dark-blue")
import time
import sys


warnings.filterwarnings("ignore")


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.webcam_thread = None
        self.scanstarted = False
        self.scanPaused = False
        self.scan_paused = threading.Event()
        self.scan_stopped = threading.Event()
        self.lock = threading.Lock()
        self.scan_thread = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        warnings.filterwarnings("ignore")
        self.webcam_feed_active = False
        self.selected_webcam = 0
        self.rotating_speed = "1"
        self.ports = serial.tools.list_ports.comports()
        self.com_ports = []
        self.rotating = False
        # check if no ports found and set self.ports to "No Device Connected"
        for port in self.ports:
            port_info = f"{port.device} ({port.description})"
            self.com_ports.append(port_info)
        print(self.com_ports)
        if not self.ports:
            self.com_ports = ["No Device Connected"]
        else:
            self.com_ports = [port.device for port in self.ports]
        print(self.com_ports)
        # if(self.com_ports[0] != "No Device Connected"):
        try:
            self.serial_port = serial.Serial(
                self.com_ports[0],
                115200,
                timeout=0,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,
                dsrdtr=True,
                rtscts=True,
            )
        except:
            print("No Device Connected")
        self.delay_var = customtkinter.IntVar(value=1)
        # set grid layout 1x2
        self.title("ZenScan v0.2155")
        self.geometry(f"{1024}x{600}")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.stop_event = threading.Event()  # Event to signal the webcam thread to stop
        # load images with light and dark mode image
        image_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "test_images"
        )
        self.logo_image = customtkinter.CTkImage(
            Image.open(os.path.join(image_path, "zenscan.png")), size=(150, 75)
        )
        # self.large_test_image = customtkinter.CTkImage(Image.open(os.path.join(image_path, "large_test_image.png")), size=(500, 150))
        self.image_icon_image = customtkinter.CTkImage(
            Image.open(os.path.join(image_path, "image_icon_light.png")), size=(20, 20)
        )
        self.home_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join(image_path, "home_dark.png")),
            dark_image=Image.open(os.path.join(image_path, "home_light.png")),
            size=(20, 20),
        )
        self.chat_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join(image_path, "chat_dark.png")),
            dark_image=Image.open(os.path.join(image_path, "chat_light.png")),
            size=(20, 20),
        )
        self.add_user_image = customtkinter.CTkImage(
            light_image=Image.open(os.path.join(image_path, "add_user_dark.png")),
            dark_image=Image.open(os.path.join(image_path, "add_user_light.png")),
            size=(20, 20),
        )
        self.splash_image = customtkinter.CTkImage(
            Image.open(os.path.join(image_path, "SplashScreen.png")), size=(845, 538)
        )

        # create navigation frame
        self.navigation_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(4, weight=1)

        self.navigation_frame_label = customtkinter.CTkLabel(
            self.navigation_frame,
            text="",
            image=self.logo_image,
            compound="left",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        )
        self.navigation_frame_label.grid(row=0, column=0, padx=20, pady=20)

        self.home_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Home",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.home_image,
            anchor="w",
            command=self.home_button_event,
        )
        self.home_button.grid(row=1, column=0, sticky="ew")

        self.scan_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Scan",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.chat_image,
            anchor="w",
            command=self.frame_2_button_event,
        )
        self.scan_button.grid(row=2, column=0, sticky="ew")

        self.frame_3_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Preview",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.add_user_image,
            anchor="w",
            command=self.frame_3_button_event,
        )
        self.frame_3_button.grid(row=3, column=0, sticky="ew")
        self.settings_button = customtkinter.CTkButton(
            self.navigation_frame,
            corner_radius=0,
            height=40,
            border_spacing=10,
            text="Settings",
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            image=self.add_user_image,
            anchor="w",
            command=self.settings_button_event,
        )
        self.settings_button.grid(row=4, column=0, sticky="ewn")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(
            self.navigation_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode_event,
        )
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=20, sticky="s")

        # create home frame
        self.home_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.home_frame.grid_columnconfigure(0, weight=1)
        self.splash_frame = customtkinter.CTkLabel(
            self.home_frame,
            fg_color="transparent",
            text="",
            image=self.splash_image,
            compound="left",
        )
        self.splash_frame.grid(
            row=0, column=0, rowspan=4, sticky="nsew", padx=(0, 0), pady=(0, 0)
        )
        # self.cam1_frame.grid_rowconfigure(4, weight=1)
        # self.home_frame_button_4 = customtkinter.CTkButton(self.home_frame, text="CTkButton", image=self.image_icon_image, compound="bottom", anchor="w")
        # self.home_frame_button_4.grid(row=4, column=0, padx=20, pady=10)

        # create second frame

        self.settings_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.settings_frame.grid_columnconfigure(1, weight=1)
        self.settings_frame.grid_columnconfigure((2, 4), weight=0)
        self.settings_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)

        ## Camera Preview

        self.cam_frame = customtkinter.CTkFrame(
            self.settings_frame, fg_color="transparent"
        )
        self.cam_frame.grid(
            row=0,
            column=1,
            rowspan=4,
            sticky="nsew",
            padx=(10, 10),
            pady=(10, 10),
        )
        self.cam_frame.grid_rowconfigure(4, weight=1)

        self.cam1_frame = customtkinter.CTkLabel(
            self.cam_frame, fg_color="transparent", text=""
        )
        self.cam1_frame.grid(
            row=0, column=1, rowspan=4, sticky="nsew", padx=(10, 10), pady=(10, 10)
        )
        self.cam1_frame.grid_rowconfigure(4, weight=1)

        self.radiobutton_frame = customtkinter.CTkFrame(self.settings_frame)
        self.radiobutton_frame.grid(
            row=0, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        self.images_var = tkinter.IntVar(value=64)
        self.direction_var = tkinter.IntVar(value=0)
        self.label_radio_group = customtkinter.CTkLabel(
            master=self.radiobutton_frame, text="Number of Images"
        )
        self.label_radio_group.grid(
            row=0, column=0, columnspan=1, padx=10, pady=10, sticky=""
        )
        self.radio_button_1 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.images_var,
            value=64,
            text="64",
            command=self.set_images_event,
        )
        self.radio_button_1.grid(row=1, column=0, pady=10, padx=10, sticky="ne")
        self.radio_button_2 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.images_var,
            value=48,
            text="48",
            command=self.set_images_event,
        )
        self.radio_button_2.grid(row=2, column=0, pady=10, padx=10, sticky="ne")
        self.radio_button_3 = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.images_var,
            value=32,
            text="32",
            command=self.set_images_event,
        )
        self.radio_button_3.grid(row=3, column=0, pady=10, padx=10, sticky="ne")
        self.delay_var = tkinter.IntVar(value=1)
        self.label_radio_group = customtkinter.CTkLabel(
            master=self.radiobutton_frame, text="Direction"
        )
        self.label_radio_group.grid(
            row=0, column=1, columnspan=1, padx=10, pady=10, sticky="w"
        )
        self.cw_button = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.direction_var,
            value=0,
            text="CW",
            command=self.dir_button_event,
        )
        self.cw_button.grid(row=1, column=1, pady=10, padx=10, sticky="w")
        self.ccw_button = customtkinter.CTkRadioButton(
            master=self.radiobutton_frame,
            variable=self.direction_var,
            value=1,
            text="CCW",
            command=self.dir_button_event,
        )
        self.ccw_button.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        self.capture_label = customtkinter.CTkLabel(
            master=self.radiobutton_frame, text="Delay"
        )
        self.capture_label.grid(
            row=4, column=0, columnspan=1, padx=10, pady=10, sticky="w"
        )
        self.delay_input = customtkinter.CTkEntry(
            self.radiobutton_frame, width=100, textvariable=self.delay_var
        )
        self.delay_input.grid(row=4, column=1, padx=5, pady=5, sticky="ne")

        # Rotation

        # create checkbox and switch frame
        self.rotation_frame = customtkinter.CTkFrame(self.settings_frame)
        self.rotation_frame.grid(
            row=1, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        self.cameras = self.get_cameras()
        self.com_label = customtkinter.CTkLabel(
            master=self.rotation_frame, text="Device Port"
        )
        self.com_label.grid(row=1, column=0, columnspan=1, padx=10, pady=10, sticky="w")
        self.com_input = customtkinter.CTkComboBox(
            self.rotation_frame,
            width=100,
            values=self.com_ports,
            command=self.com_port_event,
        )
        self.com_input.grid(row=1, column=1, padx=10, pady=10, sticky="ne")

        self.cameras_label = customtkinter.CTkLabel(
            master=self.rotation_frame, text="Camera"
        )
        self.cameras_label.grid(
            row=2, column=0, columnspan=1, padx=10, pady=10, sticky="w"
        )
        self.cameras_input = customtkinter.CTkComboBox(
            self.rotation_frame, width=100, values=self.cameras
        )
        self.cameras_input.grid(row=2, column=1, padx=10, pady=10, sticky="ne")

        # self.freerotate_button = customtkinter.CTkButton(
        #     self.rotation_frame, command=self.generic_button_event, text="Free Rotate")
        # self.freerotate_button.grid(row=4, column=0, padx=10, pady=10, sticky="ne")

        # histograms

        # create slider and progressbar frame
        self.buttons_frame = customtkinter.CTkFrame(
            self.settings_frame, fg_color="transparent", height=10
        )
        self.buttons_frame.grid(
            row=4, column=1, padx=(20, 0), pady=(20, 0), sticky="sew"
        )
        self.buttons_frame.grid_columnconfigure(5, weight=1)
        self.buttons_frame.grid_rowconfigure(4, weight=1)
        self.setzero_button = customtkinter.CTkButton(
            self.buttons_frame,
            command=self.setZero_event,
            text="Set Zero",
            height=50,
            width=100,
        )
        self.setzero_button.grid(row=1, column=1, padx=10, pady=10)
        self.zero_button = customtkinter.CTkButton(
            self.buttons_frame,
            command=self.gotoZero_event,
            text="Zero",
            height=50,
            width=100,
        )
        self.zero_button.grid(row=1, column=2, padx=10, pady=10)
        self.freerotate_button = customtkinter.CTkButton(
            self.buttons_frame,
            command=self.free_rotation_event,
            text="Free Rotate",
            height=50,
            width=100,
        )
        self.freerotate_button.grid(row=1, column=3, padx=10, pady=10)
        # self.sidebar_button_4 = customtkinter.CTkButton(
        #     self.buttons_frame, command=self.generic_button_event)
        # self.sidebar_button_4.grid(row=1, column=4, padx=10, pady=10)

        # create third frame
        self.scan_frame = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.scan_frame.grid_columnconfigure(1, weight=1)
        self.scan_frame.grid_columnconfigure((2, 4), weight=0)
        self.scan_frame.grid_rowconfigure((0, 1, 2, 3), weight=1)

        # Camera Preview

        self.scan_cam_frame = customtkinter.CTkFrame(
            self.scan_frame, fg_color="transparent"
        )
        self.scan_cam_frame.grid(
            row=0,
            column=1,
            rowspan=4,
            sticky="nsew",
            padx=(10, 10),
            pady=(10, 10),
        )
        self.scan_cam_frame.grid_rowconfigure(4, weight=1)

        self.scan_cam1_frame = customtkinter.CTkLabel(
            self.scan_cam_frame, fg_color="transparent", text=""
        )
        self.scan_cam1_frame.grid(
            row=0, column=1, rowspan=4, sticky="nsew", padx=(10, 10), pady=(10, 10)
        )
        self.scan_cam1_frame.grid_rowconfigure(4, weight=1)

        self.scan_radiobutton_frame = customtkinter.CTkFrame(self.scan_frame)
        self.scan_radiobutton_frame.grid(
            row=0, column=3, padx=(20, 20), pady=(20, 0), sticky="nsew"
        )
        # self.scan_images_var = tkinter.IntVar(value=0)
        self.scan_direction_var = tkinter.IntVar(value=0)
        self.scan_label_radio_group = customtkinter.CTkLabel(
            master=self.scan_radiobutton_frame, text="Number of Images"
        )
        self.scan_label_radio_group.grid(
            row=0, column=0, columnspan=1, padx=10, pady=10, sticky=""
        )
        self.scan_radio_button_1 = customtkinter.CTkRadioButton(
            master=self.scan_radiobutton_frame,
            variable=self.images_var,
            value=64,
            text="64",
            command=self.set_images_event,
        )
        self.scan_radio_button_1.grid(row=1, column=0, pady=10, padx=10, sticky="ne")
        self.scan_radio_button_2 = customtkinter.CTkRadioButton(
            master=self.scan_radiobutton_frame,
            variable=self.images_var,
            value=48,
            text="48",
            command=self.set_images_event,
        )
        self.scan_radio_button_2.grid(row=2, column=0, pady=10, padx=10, sticky="ne")
        self.scan_radio_button_3 = customtkinter.CTkRadioButton(
            master=self.scan_radiobutton_frame,
            variable=self.images_var,
            value=32,
            text="32",
            command=self.set_images_event,
        )
        self.scan_radio_button_3.grid(row=3, column=0, pady=10, padx=10, sticky="ne")
        self.delay_var = tkinter.IntVar(value=1)
        self.scan_label_radio_group = customtkinter.CTkLabel(
            master=self.scan_radiobutton_frame, text="Direction"
        )
        self.scan_label_radio_group.grid(
            row=0, column=1, columnspan=1, padx=10, pady=10, sticky="w"
        )
        self.scan_cw_button = customtkinter.CTkRadioButton(
            master=self.scan_radiobutton_frame,
            variable=self.direction_var,
            value=0,
            text="CW",
            command=self.dir_button_event,
        )
        self.scan_cw_button.grid(row=1, column=1, pady=10, padx=10, sticky="w")
        self.scan_ccw_button = customtkinter.CTkRadioButton(
            master=self.scan_radiobutton_frame,
            variable=self.direction_var,
            value=1,
            text="CCW",
            command=self.dir_button_event,
        )
        self.scan_ccw_button.grid(row=2, column=1, pady=10, padx=10, sticky="w")
        self.scan_capture_label = customtkinter.CTkLabel(
            master=self.scan_radiobutton_frame, text="Delay"
        )
        self.scan_capture_label.grid(
            row=4, column=0, columnspan=1, padx=10, pady=10, sticky="w"
        )
        self.scan_scan_delay_input = customtkinter.CTkEntry(
            self.scan_radiobutton_frame, width=100, textvariable=self.delay_var
        )
        self.scan_scan_delay_input.grid(row=4, column=1, padx=5, pady=5, sticky="ne")

        # Rotation

        # create checkbox and switch frame
        self.scan_buttons_frame = customtkinter.CTkFrame(
            self.scan_frame, fg_color="transparent", height=10
        )
        self.scan_buttons_frame.grid(
            row=4, column=1, padx=(20, 0), pady=(20, 0), sticky="nsew"
        )
        self.scan_buttons_frame.grid_columnconfigure(5, weight=1)
        self.scan_buttons_frame.grid_rowconfigure(4, weight=1)
        self.scan_buttons_frame2 = customtkinter.CTkFrame(
            self.scan_buttons_frame, fg_color="transparent", height=10
        )
        self.scan_buttons_frame2.grid(
            row=1, column=0, padx=(20, 0), pady=(20, 0), sticky="nsew"
        )
        self.progressbar_1 = customtkinter.CTkProgressBar(
            self.scan_buttons_frame, width=500, progress_color="#098e16"
        )
        self.progressbar_1.grid(
            row=0, column=0, padx=(20, 10), pady=(10, 10), sticky="ew"
        )
        self.progressbar_1.set(0)
        self.scan_start_btn = customtkinter.CTkButton(
            self.scan_buttons_frame2,
            command=self.start_scan_thread,
            text="Start Scan",
            height=50,
            width=100,
            font=("Helvetica", 24, "bold"),
            fg_color="#2d5a31",
            hover_color="#00c412",
        )
        self.scan_start_btn.grid(row=2, column=2, padx=10, pady=10, sticky="nsew")
        self.scan_stop_btn = customtkinter.CTkButton(
            self.scan_buttons_frame2,
            command=self.stop_scan_event,
            text="Stop Scan",
            height=50,
            width=100,
            font=("Helvetica", 24, "bold"),
            fg_color="#824042",
            hover_color="red",
        )
        self.scan_stop_btn.grid(row=2, column=3, padx=10, pady=10, sticky="nsew")
        self.scan_pause_btn = customtkinter.CTkButton(
            self.scan_buttons_frame2,
            command=self.pause_scan_event,
            text="Pause Scan",
            height=50,
            width=100,
            font=("Helvetica", 24, "bold"),
            fg_color="#7a7249",
            hover_color="#e5ce37",
        )
        self.scan_pause_btn.grid(row=2, column=4, padx=10, pady=10, sticky="nsew")
        self.label_progress = customtkinter.CTkLabel(
            master=self.scan_buttons_frame2,
            text="Progress",
            font=("Helvetica", 16, "bold"),
        )
        self.label_progress.grid(
            row=0, column=3, columnspan=1, padx=10, pady=10, sticky="nesw"
        )

        # create fourth frame
        self.fourthframe = customtkinter.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )

        # select default frame
        self.select_frame_by_name("home")

    @staticmethod
    def get_cameras(max_cameras=10):
        cameras = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i)
            if cap is None or not cap.isOpened():
                print("Camera not found:", i)
            else:
                print("Camera found:", i)
                cameras.append(str(i))
            cap.release()
        print(cameras)
        return cameras

    def start_webcam_feed(self):
        self.stop_thread = False
        print(self.webcam_feed_active)
        # if self.webcam_feed_active:
        #     return
        print(self.selected_webcam)
        cap = cv2.VideoCapture(0)

        def webcam_thread():
            print(self.stop_event.is_set())
            try:
                while True:
                    if self.stop_thread:
                        break
                    # Read a frame from the webcam
                    ret, frame = cap.read()
                    if ret:
                        # Get the width of the self.cam_frame widget
                        frame_width = self.cam_frame.winfo_width()
                        # print(frame_width)
                        frame_height = int(frame_width / 1.777777777777778)
                        # print(frame_height, frame_width)
                        # Get height of frames based on input aspect ratio
                        # print(frame_height)
                        # Get height of frames based on input aspect ratio
                        #
                        # Resize the frame to the calculated dimensions
                        frame_resized = cv2.resize(frame, (frame_width, frame_height))
                        # Convert the frame to RGB
                        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

                        # Create an ImageTk object
                        img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))

                        # Update the cam_frame image

                        self.cam1_frame.configure(image=img)
                        self.cam1_frame.image = (
                            img  # Keep a reference to prevent garbage collection
                        )
                        self.cam1_frame.place(x=0, y=0, relwidth=1, relheight=1)
            except:
                print("Error displaying video")

        # Start the webcam thread
        Thread(target=webcam_thread).start()
        # self.stop_event.clear()  # Reset the stop event
        # self.webcam_thread = threading.Thread(target=webcam_thread, daemon=True)
        # self.webcam_thread.start()
        self.webcam_feed_active = True

    def stop_webcam_feed(self):
        self.stop_event.set()  # Signal the webcam thread to stop
        # self.webcam_thread.join()  # Wait for the webcam thread to finish
        self.webcam_feed_active = False

    def start_scan_webcam_feed(self):
        self.stop_thread = False
        print(self.webcam_feed_active)
        # if self.webcam_feed_active:
        #     return
        print(self.selected_webcam)
        cap = cv2.VideoCapture(0)

        def webcam_scan_thread():
            print(self.stop_event.is_set())
            try:
                while True:
                    if self.stop_thread:
                        break
                    # Read a frame from the webcam
                    ret, frame = cap.read()
                    if ret:
                        # Get the width of the self.cam_frame widget
                        frame_width = self.scan_cam_frame.winfo_width()
                        # print(frame_width)
                        frame_height = int(frame_width / 1.777777777777778)
                        frame_resized = cv2.resize(frame, (frame_width, frame_height))
                        # Convert the frame to RGB
                        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

                        # Create an ImageTk object
                        img = ImageTk.PhotoImage(Image.fromarray(frame_rgb))

                        # Update the cam_frame image

                        self.scan_cam1_frame.configure(image=img)
                        self.scan_cam1_frame.image = (
                            img  # Keep a reference to prevent garbage collection
                        )
                        self.scan_cam1_frame.place(x=0, y=0, relwidth=1, relheight=1)
            except:
                print("Error displaying video")

        # Start the webcam thread
        Thread(target=webcam_scan_thread).start()
        # self.stop_event.clear()  # Reset the stop event
        # self.webcam_thread = threading.Thread(target=webcam_thread, daemon=True)
        # self.webcam_thread.start()
        self.webcam_feed_active = True

    def stop_scan_webcam_feed(self):
        self.stop_event.set()  # Signal the webcam thread to stop
        # self.webcam_thread.join()  # Wait for the webcam thread to finish
        self.webcam_feed_active = False

    def select_frame_by_name(self, name):
        # set button color for selected button
        self.home_button.configure(
            fg_color=("gray75", "gray25") if name == "home" else "transparent"
        )
        self.settings_button.configure(
            fg_color=("gray75", "gray25") if name == "settings" else "transparent"
        )
        self.scan_button.configure(
            fg_color=("gray75", "gray25") if name == "scan" else "transparent"
        )
        self.frame_3_button.configure(
            fg_color=("gray75", "gray25") if name == "frame_4" else "transparent"
        )

        # show selected frame
        if name == "home":
            self.home_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.home_frame.grid_forget()
        if name == "settings":
            self.settings_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.settings_frame.grid_forget()
        if name == "scan":
            self.scan_frame.grid(row=0, column=1, sticky="nsew")
        else:
            self.scan_frame.grid_forget()

    def select_cam_by_tab(self, name):
        # show selected frame
        print(name)

    def home_button_event(self):
        self.select_frame_by_name("home")
        self.stop_scan_webcam_feed()
        self.stop_webcam_feed()

    def frame_2_button_event(self):
        self.select_frame_by_name("scan")
        self.stop_webcam_feed()
        self.after(1, self.start_scan_webcam_feed)

    def frame_3_button_event(self):
        self.select_frame_by_name("frame_3")
        self.stop_webcam_feed()
        self.stop_scan_webcam_feed()

    def settings_button_event(self):
        self.select_frame_by_name("settings")
        self.stop_scan_webcam_feed()
        self.after(1, self.start_webcam_feed)

    def generic_button_event(self):
        print("generic button event")

    def start_button_event(self):
        print("generic button event")

    def pause_button_event(self):
        print("generic button event")

    def stop_button_event(self):
        print("generic button event")

    def send_imagesnum_event(self, num):
        if num == 64:
            self.rotating_speed = "1"
        elif num == 48:
            self.rotating_speed = "2"
        elif num == 32:
            self.rotating_speed = "3"
        # self.serial_port.write(bytearray('s', 'ascii'))

    def set_images_event(self):
        im = self.images_var.get()
        self.send_imagesnum_event(im)
        print(im)

    def on_closing(self):
        # This method will be called when the GUI window is closed
        # sys.exit()
        os._exit(0)

    def free_rotation_event(self):
        if self.rotating == True:
            print("stop rotating")
            self.freerotate_button.configure(text="Free Rotation")
            self.serial_port.write(bytearray("s", "ascii"))
            self.rotating = False

        else:
            print("start rotating")
            self.freerotate_button.configure(text="Stop Free Rotation")
            self.serial_port.write(bytearray("6", "ascii"))
            self.rotating = True

    def dir_button_event(self):
        dir = self.direction_var.get()
        if dir == 0:
            print("clockwise")
            if self.serial_port:
                self.serial_port.write(bytearray("7", "ascii"))
        elif dir == 1:
            print("Counter-clockwise")
            if self.serial_port:
                self.serial_port.write(bytearray("8", "ascii"))
        print("dir button event")

    def camswitch_event(self):
        self.stop_webcam_feed()  # Stop the current webcam feed

        selected_tab = self.camTabview.get()  # Get the selected tab
        if selected_tab == "Cam 1":
            self.selected_webcam = 0
        elif selected_tab == "Cam 2":
            self.selected_webcam = 1
        elif selected_tab == "Cam 3":
            self.selected_webcam = 2
        else:
            self.selected_webcam = 0  # Default to 0 if an invalid tab is selected

        if self.selected_webcam >= 0:
            self.start_webcam_feed()  # Start the webcam feed for the newly selected webcam

    def setZero_event(self):
        self.serial_port.write(bytearray("4", "ascii"))
        print("Zero Set")

    def gotoZero_event(self):
        self.serial_port.write(bytearray("5", "ascii"))
        print("Rotating to zero")

    def start_scan_event(self):
        global scan_thread
        delay = self.delay_var.get()
        speed = self.images_var.get()
        print(speed)
        for i in range(1, speed + 2):
            delay = self.delay_var.get()
            # self.serial_port.write(bytearray('1', 'ascii'))
            if self.scan_stopped.is_set():
                break
            if self.scan_paused.is_set():
                self.lock.acquire()
            if self.scan_stopped.is_set():
                break
            print(i)
            print("Rotating")
            percent = i / speed
            print(percent * 100, "%")
            self.progressbar_1.set(percent)
            self.label_progress.configure(
                text=str(int(percent * 100))
                + "%"
                + "      "
                + str(i)
                + "/"
                + str(speed)
            )
            self.serial_port.write(bytearray(self.rotating_speed, "ascii"))
            if speed == 64:
                time.sleep(1)
            elif speed == 48:
                time.sleep(1.4)
            elif speed == 32:
                time.sleep(2)
            self.photo_event()
            time.sleep(delay)
        self.progressbar_1.set(0)
        # self.lock.release()

    def start_scan_thread(self):
        self.scan_stopped.clear()
        self.scan_paused.clear()
        self.scan_thread = threading.Thread(target=self.start_scan_event, daemon=True)
        self.scan_thread.start()

    def stop_scan_event(self):
        # global self.scan_thread
        if self.scan_paused.is_set():
            self.resume_scan_event()
        self.progressbar_1.set(0)
        self.label_progress.configure(text="Progress")
        if self.scan_thread:
            self.scan_stopped.set()
            self.resume_scan_event()
            self.scan_pause_btn.configure(text="Pause Scan")

        print("Scan Stopped")

    def pause_scan_event(self):
        if self.scanPaused == False:
            if self.scan_thread:
                print("Pausing Scan")
                self.scan_paused.set()
                if not self.lock.locked():  # Check if the lock is already acquired
                    self.lock.acquire()
                self.scanPaused = True
                self.scan_pause_btn.configure(text="Resume Scan")
                print("Scan Paused")
        else:
            self.resume_scan_event()

    def resume_scan_event(self):
        if self.scan_thread:
            self.scan_paused.clear()
            self.lock.release()
            self.scanPaused = False
            self.scan_pause_btn.configure(text="Pause Scan")
            print("Scan Resumed")

    def photo_event(self):
        self.serial_port.write(bytearray("0", "ascii"))
        print("Photo taken")

    def com_port_event(self):
        self.connect_port = self.com_input.get()
        self.serial_port = serial.Serial(
            self.com_ports[0],
            115200,
            timeout=0,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            dsrdtr=True,
            rtscts=True,
        )
        print("COM Port event")

    def change_appearance_mode_event(self, new_appearance_mode):
        customtkinter.set_appearance_mode(new_appearance_mode)


if __name__ == "__main__":
    app = App()
    app.mainloop()
