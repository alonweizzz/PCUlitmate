import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import threading
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
import psutil
from PIL import Image

VERSION = "0.1.0"
BG, PANEL, MUTED, ACCENT = "#0B1020", "#151D31", "#A0AFCB", "#5A8BFF"
ctk.set_appearance_mode("dark")


def gb(n):
    return f"{n / 1024**3:.1f} GB"


def powershell(command):
    try:
        return subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", command],
            text=True, timeout=8,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).strip()
    except (OSError, subprocess.SubprocessError):
        return "Unavailable"


class Metric(ctk.CTkFrame):
    def __init__(self, parent, title, column):
        super().__init__(parent, fg_color=PANEL, corner_radius=15)
        self.grid(row=0, column=column, sticky="nsew", padx=7)
        ctk.CTkLabel(self, text=title, text_color=MUTED).pack(anchor="w", padx=20, pady=(18, 6))
        self.number = ctk.CTkLabel(self, text="—", font=ctk.CTkFont(size=32, weight="bold"))
        self.number.pack(anchor="w", padx=20)
        self.bar = ctk.CTkProgressBar(self, progress_color=ACCENT)
        self.bar.pack(fill="x", padx=20, pady=(12, 8))
        self.bar.set(0)
        self.details = ctk.CTkLabel(self, text="Loading...", text_color=MUTED)
        self.details.pack(anchor="w", padx=20, pady=(0, 18))

    def set_value(self, percentage, description):
        p = max(0, min(100, float(percentage)))
        self.number.configure(text=f"{p:.0f}%")
        self.bar.set(p / 100)
        self.details.configure(text=description)


class PCUltimate(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PCULTIMATE v" + VERSION)
        self.geometry("1080x730")
        self.minsize(860, 640)
        self.configure(fg_color=BG)
        self.set_brand_icon()
        self.running = True
        self.build_ui()
        psutil.cpu_percent(interval=None)
        self.after(300, self.refresh)
        threading.Thread(target=self.load_hardware, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def set_brand_icon(self):
        try:
            icon_path = self.asset_path("pcultimate-icon.png")
            from PIL import ImageTk
            self._window_icon = ImageTk.PhotoImage(Image.open(icon_path))
            self.iconphoto(True, self._window_icon)
        except (OSError, RuntimeError):
            pass

    @staticmethod
    def asset_path(name):
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        return base / "assets" / name

    def build_ui(self):
        root = ctk.CTkScrollableFrame(self, fg_color=BG)
        root.pack(fill="both", expand=True, padx=22, pady=18)
        top = ctk.CTkFrame(root, fg_color="transparent")
        top.pack(fill="x", pady=(0, 23))
        self.brand_image = ctk.CTkImage(light_image=Image.open(self.asset_path("pcultimate-logo.png")), dark_image=Image.open(self.asset_path("pcultimate-logo.png")), size=(280, 73))
        ctk.CTkLabel(top, text="", image=self.brand_image).pack(side="left")
        ctk.CTkLabel(top, text="SYSTEM DASHBOARD  •  v" + VERSION, text_color=MUTED).pack(side="right")
        ctk.CTkLabel(root, text="Your PC at a glance", font=ctk.CTkFont(size=23, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(root, text="Live performance and hardware information", text_color=MUTED).pack(anchor="w", pady=(3, 20))

        cards = ctk.CTkFrame(root, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 18))
        for i in range(3):
            cards.grid_columnconfigure(i, weight=1, uniform="cards")
        self.cpu = Metric(cards, "CPU USAGE", 0)
        self.ram = Metric(cards, "MEMORY USAGE", 1)
        self.disk = Metric(cards, "SYSTEM DISK", 2)

        base = ctk.CTkFrame(root, fg_color="transparent")
        base.pack(fill="x")
        base.grid_columnconfigure(0, weight=2)
        base.grid_columnconfigure(1, weight=1)
        details = ctk.CTkFrame(base, fg_color=PANEL, corner_radius=15)
        details.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        ctk.CTkLabel(details, text="Hardware & operating system",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 15))
        self.labels = {}
        for name in ("Computer", "Operating system", "Processor", "Graphics", "Total RAM",
                     "CPU cores", "Architecture", "System drive", "Boot time"):
            line = ctk.CTkFrame(details, fg_color="transparent")
            line.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(line, text=name, text_color=MUTED, width=130, anchor="w").pack(side="left")
            label = ctk.CTkLabel(line, text="—", anchor="w", justify="left", wraplength=370)
            label.pack(side="left", fill="x", expand=True)
            self.labels[name] = label

        shortcuts = ctk.CTkFrame(base, fg_color=PANEL, corner_radius=15)
        shortcuts.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        ctk.CTkLabel(shortcuts, text="Quick controls",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20, pady=(20, 15))
        for title, target in [("Task Manager", "taskmgr.exe"),
                              ("Windows Settings", "ms-settings:about"),
                              ("Device Manager", "devmgmt.msc")]:
            ctk.CTkButton(shortcuts, text=title, height=40,
                          command=lambda target=target: self.launch(target)).pack(fill="x", padx=20, pady=7)
        self.status = ctk.CTkLabel(shortcuts, text="●  Live monitoring • 2s refresh",
                                    text_color="#48D9A0")
        self.status.pack(anchor="w", padx=20, pady=(26, 10))

    def load_hardware(self):
        cpu = powershell("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)")
        gpu = powershell("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")
        if self.running:
            self.after(0, lambda: self.set_hardware(cpu, gpu))

    def set_hardware(self, cpu, gpu):
        if self.running:
            self.labels["Processor"].configure(text=cpu)
            self.labels["Graphics"].configure(text=", ".join(gpu.splitlines()) or "Unavailable")

    def refresh(self):
        if not self.running:
            return
        try:
            memory = psutil.virtual_memory()
            self.cpu.set_value(psutil.cpu_percent(interval=None), "Live processor load")
            self.ram.set_value(memory.percent, f"{gb(memory.used)} / {gb(memory.total)}")
            drive = os.environ.get("SystemDrive", "C:") + "\\" if sys.platform == "win32" else "/"
            try:
                disk = psutil.disk_usage(drive)
                self.disk.set_value(disk.percent, f"{gb(disk.used)} / {gb(disk.total)}")
            except (OSError, PermissionError):
                self.disk.details.configure(text="Disk unavailable")
            values = {
                "Computer": socket.gethostname(),
                "Operating system": f"{platform.system()} {platform.release()}",
                "Total RAM": gb(memory.total),
                "CPU cores": f"{psutil.cpu_count(logical=False) or '?'} physical / {psutil.cpu_count(logical=True) or '?'} logical",
                "Architecture": platform.machine(),
                "System drive": drive,
                "Boot time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
            }
            for key, value in values.items():
                self.labels[key].configure(text=value)
        except Exception as exc:
            self.status.configure(text="Monitoring error: " + str(exc), text_color="#FF9A9A")
        finally:
            if self.running:
                self.after(2000, self.refresh)

    def launch(self, target):
        if sys.platform != "win32":
            messagebox.showinfo("PCULTIMATE", "Quick controls require Windows.")
            return
        try:
            if target.startswith("ms-settings:"):
                os.startfile(target)
            elif target.lower().endswith(".msc"):
                subprocess.Popen(["mmc.exe", target], shell=False)
            else:
                subprocess.Popen([target], shell=False)
        except OSError as exc:
            messagebox.showerror("PCULTIMATE", str(exc))

    def close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    PCUltimate().mainloop()
