import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from cvzone.HandTrackingModule import HandDetector
import pyfirmata2


class HandControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hand Control App")
        self.root.geometry("800x600")

        self.com_ports = self.get_com_ports()
        self.selected_com_port = tk.StringVar(value=self.com_ports[0] if self.com_ports else "")

        self.detector = HandDetector(detectionCon=0.8, maxHands=1)
        self.video = None

        self.board = None
        self.servos = {}
        self.servo_pins = ['d:10:s', 'd:9:s', 'd:6:s', 'd:5:s', 'd:3:s']

        self.is_running = False

        # GUI Elements
        self.com_label = ttk.Label(root, text="Select COM Port:")
        self.com_label.pack()

        self.combo = ttk.Combobox(root, textvariable=self.selected_com_port, values=self.com_ports)
        self.combo.pack()

        self.start_button = ttk.Button(root, text="Start", command=self.start)
        self.start_button.pack()

        self.stop_button = ttk.Button(root, text="Stop", command=self.stop, state=tk.DISABLED)
        self.stop_button.pack()

        # Create a frame for video feed
        self.video_frame = ttk.LabelFrame(root, text="Live Feed", width=640, height=480)
        self.video_frame.pack(pady=10)

        self.video_label = ttk.Label(self.video_frame)
        self.video_label.pack()

    def start(self):
        self.board = pyfirmata2.Arduino(self.selected_com_port.get())
        for idx, pin in enumerate(self.servo_pins):
            self.servos[idx] = self.board.get_pin(pin)

        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        self.video = cv2.VideoCapture(0)
        self.update()

    def stop(self):
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        if self.board is not None:
            self.board.exit()

        if self.video is not None:
            self.video.release()
            self.video = None

    def update(self):
        ret, frame = self.video.read()
        if ret:
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (640, 480))
            hands, img = self.detector.findHands(frame)

            if hands:
                lmList = hands[0]
                fingerUp = self.detector.fingersUp(lmList)
                finger_count = sum(fingerUp)
                print(fingerUp)

                servo_angles = {
                    (0, 0, 0, 0, 0): (0, 0, 0, 0, 0),
                    (0, 1, 0, 0, 0): (90, 0, 0, 0, 0),
                    (0, 0, 1, 0, 0): (0, 90, 0, 0, 0),
                    (0, 0, 0, 1, 0): (0, 0, 90, 0, 0),
                    (0, 0, 0, 0, 1): (0, 0, 0, 90, 0),
                    (1, 0, 0, 0, 0): (0, 0, 0, 0, 90),
                    (0, 1, 1, 0, 0): (90, 90, 0, 0, 0),
                    (0, 1, 0, 1, 0): (90, 0, 90, 0, 0),
                    (0, 1, 0, 0, 1): (90, 0, 0, 90, 0),
                    (1, 0, 0, 1, 0): (0, 0, 90, 0, 90),
                    (0, 0, 1, 1, 0): (0, 90, 90, 0, 90),
                    (0, 0, 1, 0, 1): (0, 90, 0, 90, 0),
                    (1, 0, 1, 0, 0): (0, 90, 0, 0, 90),
                    (0, 0, 0, 1, 1): (0, 0, 90, 90, 0),
                    (1, 0, 0, 1, 0): (0, 0, 90, 0, 90),
                    (1, 0, 0, 0, 1): (0, 0, 0, 90, 90),
                    (0, 1, 1, 1, 0): (90, 90, 90, 0, 0),
                    (0, 1, 1, 1, 1): (90, 90, 90, 90, 0),
                    (0, 0, 1, 1, 1): (0, 90, 90, 90, 0),
                    (1, 1, 1, 1, 1): (90, 90, 90, 90, 90),
                    (1, 1, 1, 1, 0): (90, 90, 90, 90, 0),
                    (1, 1, 1, 0, 1): (90, 90, 90, 0, 90),
                    (1, 1, 0, 1, 1): (90, 90, 0, 90, 90),
                    (1, 0, 1, 1, 1): (90, 0, 90, 90, 90),
                    (0, 1, 1, 0, 1): (90, 90, 90, 0, 90),
                    (1, 1, 0, 1, 0): (90, 90, 0, 90, 0),
                    (1, 0, 1, 0, 1): (90, 0, 90, 0, 90),
                    (0, 1, 0, 1, 1): (90, 90, 0, 90, 90),
                    (1, 1, 1, 0, 0): (90, 90, 90, 0, 0),
                    (1, 1, 0, 0, 0): (90, 0, 0, 0, 90),
                    (0, 1, 1, 0, 1): (90, 90, 0, 90, 0)
                }

                angle_servos = servo_angles.get(tuple(fingerUp), (0, 0, 0, 0, 0))

                for idx, angle in enumerate(angle_servos):
                    self.servos[idx].write(angle)

                # Display finger count on the image
            #cv2.putText(img, f"Fingers: {finger_count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(img)
            img = ImageTk.PhotoImage(image=img)

            self.video_label.config(image=img)
            self.video_label.image = img

        if self.is_running:
            self.root.after(10, self.update)

    def get_com_ports(self):
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]


if __name__ == "__main__":
    root = tk.Tk()
    app = HandControlApp(root)
    root.mainloop()
