"""PCULTIMATE 0.2 — local Windows monitoring and safe update checks."""
import json
import os
import platform
import socket
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
import customtkinter as ctk
import psutil
from PIL import Image, ImageTk

VERSION = "0.2.0"
RELEASES_API = "https://api.github.com/repos/alonweizzz/PCUlitmate/releases/latest"
CONFIG_DIR = Path(os.getenv("APPDATA") or Path.home()) / "PCULTIMATE"
CONFIG_FILE = CONFIG_DIR / "settings.json"
COLORS = {"dark": ("#0B1020", "#151D31", "#A0AFCB"),
          "light": ("#EDF3FC", "#FFFFFF", "#50627D")}


def version_tuple(v):
    try:
        parts = v.strip().lstrip("vV").split(".")
        return tuple(int(p) for p in parts[:3])
    except (ValueError, TypeError):
        return (0,)


def gb(n):
    return f"{n / 1024**3:.1f} GB"


def ps(command):
    try:
        return subprocess.check_output(["powershell", "-NoProfile", "-Command", command],
                                       text=True, timeout=8,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).strip()
    except (OSError, subprocess.SubprocessError):
        return "Unavailable"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = self.load_settings()
        self.theme = self.settings.get("theme", "dark")
        ctk.set_appearance_mode(self.theme)
        self.running = True
        self.title("PCULTIMATE " + VERSION)
        self.geometry("1100x750")
        self.minsize(870, 630)
        self.set_icon()
        self.build_ui()
        self.show_page("Dashboard")
        psutil.cpu_percent(interval=None)
        self.after(500, self.refresh)
        threading.Thread(target=self.load_hardware, daemon=True).start()
        self.after(3500, self.check_updates)
        self.protocol("WM_DELETE_WINDOW", self.close)

    @staticmethod
    def asset(name):
        return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets" / name

    @staticmethod
    def load_settings():
        try:
            value = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def save_settings(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_FILE.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")
        except OSError:
            pass

    def set_icon(self):
        try:
            self._icon = ImageTk.PhotoImage(Image.open(self.asset("pcultimate-icon.png")))
            self.iconphoto(True, self._icon)
        except (OSError, RuntimeError):
            pass

    def palette(self):
        return COLORS[self.theme]

    def build_ui(self):
        bg, panel, muted = self.palette()
        self.configure(fg_color=bg)
        self.shell = ctk.CTkFrame(self, fg_color="transparent")
        self.shell.pack(fill="both", expand=True)
        self.sidebar = ctk.CTkFrame(self.shell, width=235, fg_color=panel, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        try:
            image = Image.open(self.asset("pcultimate-logo.png"))
            self.brand = ctk.CTkImage(light_image=image, dark_image=image, size=(195, 52))
            ctk.CTkLabel(self.sidebar, text="", image=self.brand).pack(pady=(25, 32))
        except OSError:
            ctk.CTkLabel(self.sidebar, text="PCULTIMATE",
                         font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(25, 32))
        self.nav = {}
        for page, icon in (("Dashboard", "◈"), ("System Info", "▣"), ("Settings", "⚙"), ("Updates", "↻")):
            btn = ctk.CTkButton(self.sidebar, text=f"{icon}   {page}", anchor="w",
                                fg_color="transparent", hover_color=("#D9E7FA", "#273A5B"),
                                height=44, command=lambda p=page: self.show_page(p))
            btn.pack(fill="x", padx=15, pady=5)
            self.nav[page] = btn
        ctk.CTkLabel(self.sidebar, text="PCULTIMATE  •  v" + VERSION,
                     text_color=muted).pack(side="bottom", pady=24)
        self.content = ctk.CTkScrollableFrame(self.shell, fg_color=bg)
        self.content.pack(side="left", fill="both", expand=True, padx=20, pady=18)

    def clear_page(self):
        for child in self.content.winfo_children():
            child.destroy()

    def heading(self, title, subtitle):
        ctk.CTkLabel(self.content, text=title, font=ctk.CTkFont(size=27, weight="bold")).pack(anchor="w", pady=(10, 4))
        ctk.CTkLabel(self.content, text=subtitle, text_color=self.palette()[2]).pack(anchor="w", pady=(0, 24))

    def show_page(self, page):
        self.page = page
        for name, button in self.nav.items():
            button.configure(fg_color="#2563EB" if name == page else "transparent")
        self.clear_page()
        if page == "Dashboard":
            self.heading("System dashboard", "Live performance • refreshes every 2 seconds")
            cards = ctk.CTkFrame(self.content, fg_color="transparent")
            cards.pack(fill="x")
            for i in range(3):
                cards.grid_columnconfigure(i, weight=1, uniform="card")
            self.metrics = {}
            for i, title in enumerate(("CPU", "Memory", "System disk")):
                frame = ctk.CTkFrame(cards, corner_radius=16)
                frame.grid(row=0, column=i, padx=6, sticky="nsew")
                ctk.CTkLabel(frame, text=title, text_color=self.palette()[2]).pack(anchor="w", padx=17, pady=(18, 7))
                val = ctk.CTkLabel(frame, text="—", font=ctk.CTkFont(size=30, weight="bold"))
                val.pack(anchor="w", padx=17)
                bar = ctk.CTkProgressBar(frame)
                bar.pack(fill="x", padx=17, pady=(12, 7))
                bar.set(0)
                detail = ctk.CTkLabel(frame, text="Loading", text_color=self.palette()[2])
                detail.pack(anchor="w", padx=17, pady=(0, 16))
                self.metrics[title] = (val, bar, detail)
            ctk.CTkLabel(self.content, text="Quick actions",
                         font=ctk.CTkFont(size=19, weight="bold")).pack(anchor="w", pady=(30, 12))
            for title, target in (("Task Manager", "taskmgr.exe"),
                                  ("Device Manager", "devmgmt.msc"),
                                  ("Windows Settings", "ms-settings:about")):
                ctk.CTkButton(self.content, text=title, height=42,
                              command=lambda t=target: self.launch(t)).pack(anchor="w", pady=5)
        elif page == "System Info":
            self.heading("System information", "Hardware and operating system details")
            self.info_labels = {}
            for key in ("Computer", "Operating system", "Processor", "Graphics",
                        "RAM", "CPU cores", "Architecture", "System drive", "Boot time"):
                row = ctk.CTkFrame(self.content)
                row.pack(fill="x", pady=4)
                ctk.CTkLabel(row, text=key, width=155, anchor="w",
                             text_color=self.palette()[2]).pack(side="left", padx=16, pady=11)
                label = ctk.CTkLabel(row, text="Loading...", anchor="w", wraplength=450)
                label.pack(side="left", fill="x", expand=True)
                self.info_labels[key] = label
            self.populate_info()
        elif page == "Settings":
            self.heading("Appearance", "Customize your PCULTIMATE experience")
            ctk.CTkLabel(self.content, text="Theme").pack(anchor="w", pady=(0, 10))
            ctk.CTkSegmentedButton(self.content, values=["Dark", "Light"],
                                   command=self.change_theme).pack(anchor="w")
            ctk.CTkLabel(self.content, text="Current theme: " + self.theme.title(),
                         text_color=self.palette()[2]).pack(anchor="w", pady=18)
        else:
            self.heading("Updates", "Check official PCULTIMATE releases")
            ctk.CTkLabel(self.content, text="Installed version: " + VERSION).pack(anchor="w", pady=10)
            self.update_label = ctk.CTkLabel(self.content, text="Updates are checked at startup.",
                                               text_color=self.palette()[2], wraplength=540)
            self.update_label.pack(anchor="w", pady=10)
            ctk.CTkButton(self.content, text="Check for updates",
                          command=lambda: self.check_updates(manual=True)).pack(anchor="w", pady=12)

    def change_theme(self, value):
        self.theme = value.lower()
        self.settings["theme"] = self.theme
        self.save_settings()
        ctk.set_appearance_mode(self.theme)
        for child in self.shell.winfo_children():
            child.destroy()
        self.build_ui()
        self.show_page("Settings")

    def populate_info(self):
        if self.page != "System Info":
            return
        memory = psutil.virtual_memory()
        drive = (os.environ.get("SystemDrive", "C:") + "\\") if sys.platform == "win32" else "/"
        values = {
            "Computer": socket.gethostname(),
            "Operating system": platform.platform(),
            "Processor": getattr(self, "cpu_name", "Loading..."),
            "Graphics": getattr(self, "gpu_name", "Loading..."),
            "RAM": gb(memory.total),
            "CPU cores": f"{psutil.cpu_count(logical=False) or '?'} physical / {psutil.cpu_count() or '?'} logical",
            "Architecture": platform.machine(),
            "System drive": drive,
            "Boot time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M"),
        }
        for key, val in values.items():
            self.info_labels[key].configure(text=val)

    def load_hardware(self):
        cpu = ps("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)")
        gpu = ps("Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name")
        self.cpu_name, self.gpu_name = cpu, ", ".join(gpu.splitlines())
        if self.running:
            self.after(0, self.populate_info)

    def refresh(self):
        if not self.running:
            return
        try:
            if self.page == "Dashboard":
                memory = psutil.virtual_memory()
                drive = (os.environ.get("SystemDrive", "C:") + "\\") if sys.platform == "win32" else "/"
                items = [("CPU", psutil.cpu_percent(interval=None), "Processor load"),
                         ("Memory", memory.percent, f"{gb(memory.used)} / {gb(memory.total)}")]
                try:
                    disk = psutil.disk_usage(drive)
                    items.append(("System disk", disk.percent, f"{gb(disk.used)} / {gb(disk.total)}"))
                except OSError:
                    pass
                for key, percent, detail in items:
                    label, bar, sub = self.metrics[key]
                    label.configure(text=f"{percent:.0f}%")
                    bar.set(max(0, min(1, percent / 100)))
                    sub.configure(text=detail)
            elif self.page == "System Info":
                self.populate_info()
        finally:
            if self.running:
                self.after(2000, self.refresh)

    def check_updates(self, manual=False):
        if not self.running:
            return
        if manual and self.page == "Updates":
            self.update_label.configure(text="Checking GitHub releases...")
        threading.Thread(target=self.fetch_update, args=(manual,), daemon=True).start()

    def fetch_update(self, manual):
        try:
            req = urllib.request.Request(RELEASES_API, headers={"User-Agent": "PCULTIMATE/" + VERSION,
                                                                 "Accept": "application/vnd.github+json"})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.load(response)
            latest = data.get("tag_name", "")
            url = data.get("html_url", "")
            available = version_tuple(latest) > version_tuple(VERSION)
            result = f"New version {latest} available." if available else "You have the latest published version."
            if self.running:
                self.after(0, lambda: self.update_result(result, url if available else None, manual))
        except (OSError, ValueError, KeyError) as exc:
            if self.running and manual:
                self.after(0, lambda: self.update_result("Update check unavailable: " + str(exc), None, True))

    def update_result(self, result, url, manual):
        if not self.running:
            return
        if self.page == "Updates":
            self.update_label.configure(text=result)
        if url and (manual or not self.settings.get("dismissed_release") == url):
            if messagebox.askyesno("PCULTIMATE update", result + "\n\nOpen official GitHub release page?"):
                webbrowser.open(url)
            else:
                self.settings["dismissed_release"] = url
                self.save_settings()

    def launch(self, target):
        if sys.platform != "win32":
            messagebox.showinfo("PCULTIMATE", "This feature requires Windows.")
            return
        try:
            if target.startswith("ms-settings:"):
                os.startfile(target)
            elif target.endswith(".msc"):
                subprocess.Popen(["mmc.exe", target], shell=False)
            else:
                subprocess.Popen([target], shell=False)
        except OSError as exc:
            messagebox.showerror("PCULTIMATE", str(exc))

    def close(self):
        self.running = False
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
