# -*- coding: utf-8 -*-

import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, scrolledtext

class UARTCommunication:
    def __init__(self):
        self.ser = None
        self.baud_rate = 9600
        self.access_denied_shown = False
        self.stop_auto_receive = False

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port):
        if self.ser and self.ser.is_open:
            self.ser.close()

        try:
            self.ser = serial.Serial(port, self.baud_rate, timeout=1)
            self.access_denied_shown = False
            self.stop_auto_receive = False
            return f"Connected to {port} at {self.baud_rate} baud"
        except serial.SerialException as e:
            self.ser = None
            if not self.access_denied_shown:
                self.access_denied_shown = True
                return f"Error: Could not open port {port} - {e}"
            return ""
        except PermissionError as e:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = None
            if not self.access_denied_shown:
                self.access_denied_shown = True
                self.stop_auto_receive = True
                return f"Error: Access denied to port {port} - {e}"
            return ""

    def set_baud_rate(self, baud_rate):
        self.baud_rate = baud_rate
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.ser.baudrate = baud_rate
            self.ser.open()

    def send_message(self, message):
        if self.ser and self.ser.is_open:
            self.ser.write((message + "\n").encode())
            return f"Sent: {message}"
        return "Port not opened"

    def receive_message(self):
        if self.ser and self.ser.is_open:
            try:
                response = self.ser.readline().decode("utf-8", errors="replace").strip()
                if response:
                    return response
            except Exception as e:
                self.stop_auto_receive = True
                return f"Error: {e}"
        return "Port not opened"

def auto_receive(uart, output_text, status_label, root):
    if uart.stop_auto_receive:
        return

    response = uart.receive_message()
    if response and response != "Port not opened":
        output_text.insert(tk.END, f"{response}\n")
        output_text.see(tk.END)
    root.after(100, lambda: auto_receive(uart, output_text, status_label, root))

import tkinter as tk
from tkinter import ttk, scrolledtext


def start_gui():
    uart = UARTCommunication()
    root = tk.Tk()
    root.title("UART Communication Interface")
    root.geometry("800x600")
    root.configure(bg="#d3d3d3")  # Grayish background

    # Frame for Configuration
    config_frame = tk.Frame(root, bg="#d3d3d3", pady=20)
    config_frame.pack(fill="x", padx=20)

    # Select Port
    port_label = tk.Label(config_frame, text="Serial Port:", font=("Helvetica", 12), bg="#d3d3d3", fg="#000000")
    port_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(
        config_frame, textvariable=port_var, values=uart.list_ports(), state="readonly", width=30
    )
    port_combobox.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    # Select Baud Rate
    baud_label = tk.Label(config_frame, text="Transmission Speed:", font=("Helvetica", 12), bg="#d3d3d3", fg="#000000")
    baud_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    baud_var = tk.StringVar(value="9600")
    baud_combobox = ttk.Combobox(
        config_frame,
        textvariable=baud_var,
        values=["4800", "9600", "19200", "57600", "115200"],
        state="readonly",
        width=30
    )
    baud_combobox.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    def update_baud_rate():
        try:
            baud_rate = int(baud_var.get())
            uart.set_baud_rate(baud_rate)
            status_label.config(text=f"Baud rate set to {baud_rate}", fg="#006400")
        except ValueError:
            status_label.config(text="Invalid baud rate selected", fg="#8b0000")

    baud_combobox.bind("<<ComboboxSelected>>", lambda _: update_baud_rate())

    # Button to open port
    open_button = tk.Button(
        config_frame,
        text="Activate Port",
        command=lambda: open_port_callback(),
        font=("Helvetica", 12),
        bg="#000000",
        fg="#ffffff",
        width=15
    )
    open_button.grid(row=0, column=2, padx=20, pady=10)

    # Frame for Message
    message_frame = tk.Frame(root, bg="#d3d3d3", pady=20)
    message_frame.pack(fill="x", padx=20)

    message_label = tk.Label(message_frame, text="Input Text:", font=("Helvetica", 12), bg="#d3d3d3", fg="#000000")
    message_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

    message_entry = tk.Entry(message_frame, font=("Helvetica", 12), width=30)
    message_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    send_button = tk.Button(
        message_frame,
        text="Send Message",
        command=lambda: send_message_callback(),
        font=("Helvetica", 12),
        bg="#000000",
        fg="#ffffff",
        width=15
    )
    send_button.grid(row=0, column=2, padx=20, pady=10)

    # Frame for Output
    output_frame = tk.Frame(root, bg="#d3d3d3", pady=10)
    output_frame.pack(fill="both", expand=True, padx=20, pady=10)

    output_label = tk.Label(output_frame, text="Received Messages:", font=("Helvetica", 14), bg="#d3d3d3", fg="#000000")
    output_label.pack(anchor="w", padx=10)

    output_text = scrolledtext.ScrolledText(
        output_frame, width=90, height=15, wrap=tk.WORD, font=("Helvetica", 11), bg="#ffffff", fg="#000000", insertbackground="#000000"
    )
    output_text.pack(padx=10, pady=10, fill="both", expand=True)

    # Status Label
    status_label = tk.Label(
        root, text="Status: Not connected", fg="#006400", font=("Helvetica", 12), bg="#d3d3d3"
    )
    status_label.pack(fill="x", pady=10)

    def send_message_callback():
        status = uart.send_message(message_entry.get())
        status_label.config(text=status, fg="#006400" if "Sent" in status else "#8b0000")

    def open_port_callback():
        status = uart.open_port(port_var.get())
        if status:
            status_label.config(text=status, fg="#006400" if "Connected" in status else "#8b0000")
        if "Connected" in status:
            auto_receive(uart, output_text, status_label, root)

    root.mainloop()


if __name__ == "__main__":
    start_gui()
