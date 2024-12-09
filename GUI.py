import threading
import serial
import serial.tools.list_ports
import json
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinter import messagebox


class UARTCommunication:
    def __init__(self):
        self.ser = None

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def open_port(self, port, baud_rate=9600):
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            return f"Connected to {port}"
        except Exception as e:
            self.ser = None
            return f"Error: {e}"

    def send_message(self, message):
        if self.ser and self.ser.is_open:
            try:
                json_message = json.dumps(message)
                self.ser.write((json_message + "\n").encode())
                return f"Sent: {json_message}"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"

    def receive_message(self):
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode().strip()
                    if response:
                        json_response = json.loads(response)
                        return json_response
            except json.JSONDecodeError:
                return "Error: Invalid JSON received"
            except Exception as e:
                return f"Error: {e}"
        return "Port not opened"


def update_game_board(board, buttons):
    for i in range(3):
        for j in range(3):
            buttons[i][j].config(text=board[i][j])


def send_move(uart, row, col):
    message = {"command": "MOVE", "row": row, "col": col}
    uart.send_message(message)


def set_mode(uart, mode):
    message = {"command": "MODE", "mode": mode}
    uart.send_message(message)


def reset_game(uart):
    message = {"command": "RESET"}
    uart.send_message(message)


def auto_receive(uart, buttons, output_text, root):
    try:
        if uart.ser and uart.ser.is_open:
            response = uart.receive_message()
            if response and response != "Port not opened":
                if isinstance(response, dict):
                    if "board" in response:
                        update_game_board(response["board"], buttons)
                    else:
                        output_text.insert(tk.END, f"Game status: {response['message']}\n")

                    if response.get("type") == "win_status":
                        thread = threading.Thread(target=messagebox.showinfo, args=("Win Status",
                                                                                    response.get("message")))
                        thread.start()

                else:
                    output_text.insert(tk.END, f"Received: {response}\n")
                output_text.see(tk.END)
    except Exception as e:
        output_text.insert(tk.END, f"Error: {str(e)}\n")
    root.after(100, lambda: auto_receive(uart, buttons, output_text, root))

def start_gui():
    uart = UARTCommunication()

    root = tk.Tk()
    root.title("TicTacToe Game Interface")
    root.config(bg="#2e3b4e")

    font_style = ("Arial", 10, "bold")
    font_large = ("Arial", 14, "bold")

    port_frame = tk.Frame(root, bg="#1b263b", relief="raised", bd=2)
    port_frame.pack(pady=10, padx=10, fill="x")

    port_label = tk.Label(port_frame, text="Port:", font=font_style, fg="#ffffff", bg="#1b263b")
    port_label.pack(side="left", padx=5)
    port_var = tk.StringVar()
    port_combobox = ttk.Combobox(port_frame, textvariable=port_var, values=uart.list_ports(), state="readonly")
    port_combobox.pack(side="left", padx=5, pady=5)

    open_button = tk.Button(port_frame, text="Open Port", command=lambda: open_port_callback(), font=font_style, bg="#3b5998", fg="#ffffff")
    open_button.pack(side="left", padx=5)

    buttons_frame = tk.Frame(root, bg="#2e3b4e")
    buttons_frame.pack(pady=10)

    buttons = [[None for _ in range(3)] for _ in range(3)]
    for i in range(3):
        for j in range(3):
            button = tk.Button(buttons_frame, text=" ", width=10, height=3, font=font_large, bg="#6c757d", fg="#ffffff",
                               command=lambda row=i, col=j: send_move(uart, row, col))
            button.grid(row=i, column=j, padx=5, pady=5)
            buttons[i][j] = button

    mode_frame = tk.Frame(root, bg="#1b263b", relief="raised", bd=2)
    mode_frame.pack(pady=10, padx=10, fill="x")

    mode_label = tk.Label(mode_frame, text="Mode:", font=font_style, fg="#ffffff", bg="#1b263b")
    mode_label.pack(side="left", padx=5)
    mode_var = tk.StringVar(value="User vs User")
    mode_combobox = ttk.Combobox(mode_frame, textvariable=mode_var, values=["User vs User", "User vs AI", "AI vs AI"], state="readonly")
    mode_combobox.pack(side="left", padx=5, pady=5)

    mode_button = tk.Button(mode_frame, text="Set Mode", command=lambda: set_mode(uart, mode_combobox.current()), font=font_style, bg="#3b5998", fg="#ffffff")
    mode_button.pack(side="left", padx=5)

    reset_button = tk.Button(mode_frame, text="Reset", command=lambda: reset_game(uart), font=font_style, bg="#dc3545", fg="#ffffff")
    reset_button.pack(side="left", padx=5)

    output_frame = tk.Frame(root, bg="#2e3b4e")
    output_frame.pack(pady=10)

    output_text = scrolledtext.ScrolledText(output_frame, width=50, height=10, wrap=tk.WORD, font=("Courier New", 10), bg="#1b263b", fg="#ffffff")
    output_text.pack(padx=5, pady=5)

    status_label = tk.Label(root, text="Status: Not connected", font=font_style, fg="#ffffff", bg="#2e3b4e")
    status_label.pack(pady=10)

    def open_port_callback():
        status = uart.open_port(port_var.get())
        status_label.config(text=status)
        if "Connected" in status:
            auto_receive(uart, buttons, output_text, root)
        else:
            output_text.insert(tk.END, f"Failed to connect: {status}\n")

    root.mainloop()

if __name__ == "__main__":
    start_gui()
