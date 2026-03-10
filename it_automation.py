import asyncio
import flet as ft
import os
import psutil
import subprocess
import platform
from datetime import datetime
from zipfile import ZipFile
from fpdf import FPDF

class ITLogic:
    def onboard_user(self, name, dept):
        if not name: return "Error: Name is required."
        try:
            base_dir = f"./IT_Deployment/{dept}/{name.replace(' ', '_')}"
            os.makedirs(base_dir, exist_ok=True)
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "IT Onboarding Document", ln=True, align='C')
            pdf.ln(10)
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, f"Employee Name: {name}", ln=True)
            pdf.cell(200, 10, f"Department: {dept}", ln=True)
            pdf.cell(200, 10, f"Temporary Password: Welcome@{datetime.now().year}", ln=True)
            pdf.output(f"{base_dir}/Welcome_Kit.pdf")
            return f"Success: Created {base_dir}"
        except Exception as e:
            return f"Error: {str(e)}"

    def archive_logs(self):
        log_dir = "./logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            return "Created ./logs directory."
        files = [os.path.join(log_dir, f) for f in os.listdir(log_dir)]
        if not files: return "Log directory is empty."
        archive_name = f"Archive_{datetime.now().strftime('%H%M%S')}.zip"
        with ZipFile(archive_name, 'w') as zipf:
            for f in files:
                zipf.write(f, os.path.basename(f))
                os.remove(f) 
        return f"Archived {len(files)} files into {archive_name}"

    def ping_host(self, host):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', host]
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) == 0

    def get_system_inventory(self):
        try:
            info = {
                "OS": f"{platform.system()} {platform.release()}",
                "Processor": platform.processor(),
                "RAM Total": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
                "Python Version": platform.python_version(),
                "Machine": platform.machine()
            }
            return [f"{key}: {val}" for key, val in info.items()]
        except Exception as e:
            return [f"Error fetching inventory: {str(e)}"]

async def main(page: ft.Page):
    page.title = "IT_Automator"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 1000
    page.window.height = 850
    page.bgcolor = "#0F1115"
    logic = ITLogic()

    # --- UI Controls ---
    name_in = ft.TextField(label="Full Name", height=45, border_color="#3d414d")
    dept_in = ft.Dropdown(label="Dept", options=[ft.dropdown.Option("IT"), ft.dropdown.Option("HR"), ft.dropdown.Option("Dev")], height=55)
    host_input = ft.TextField(label="IP or URL (e.g. google.com)", border_color="#3d414d", expand=True)
    log_display = ft.ListView(expand=1, spacing=10)

    # --- Meter-Style UI Controls ---
    cpu_meter = ft.ProgressRing(value=0, stroke_width=8, color="cyan", bgcolor="#2A2D37")
    mem_meter = ft.ProgressRing(value=0, stroke_width=8, color="purple", bgcolor="#2A2D37")
    cpu_label = ft.Text("0%", size=20, weight="bold")
    mem_label = ft.Text("0%", size=20, weight="bold")

    def write_log(message, is_error=False):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_display.controls.append(ft.Text(f"[{timestamp}] {message}", color="red" if is_error else "white70", size=12))
        page.update()

    async def handle_ping(e):
        target = host_input.value if host_input.value else "8.8.8.8"
        write_log(f"Pinging {target}...")
        success = await asyncio.to_thread(logic.ping_host, target)
        write_log(f"Result: {'ONLINE' if success else 'OFFLINE'}", is_error=not success)

    async def handle_inventory(e):
        write_log("--- SYSTEM AUDIT START ---")
        for line in logic.get_system_inventory(): write_log(line)
        write_log("--- AUDIT COMPLETE ---")

    async def monitor_loop():
        while True:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            cpu_meter.value, mem_meter.value = cpu / 100, mem / 100
            cpu_label.value, mem_label.value = f"{cpu}%", f"{mem}%"
            cpu_meter.color = "red" if cpu > 80 else "cyan"
            mem_meter.color = "red" if mem > 85 else "purple"
            page.update()
            await asyncio.sleep(1.5)

    page.run_task(monitor_loop)

    # --- UI Layout ---
    page.add(
        ft.Row([ft.Text("🛡️", size=30), ft.Text(" IT OPERATIONS", size=22, weight="bold")]),
        ft.Divider(color="white10"),
        
        # Row 1: The Meters
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("💻 CPU LOAD", weight="bold"),
                    ft.Stack([
                        cpu_meter, 
                        # FIX: Using top-level Alignment coordinates to prevent the AttributeError
                        ft.Container(content=cpu_label, alignment=ft.Alignment(0, 0), width=80, height=80)
                    ]),
                    ft.Text("Processor Tasking", size=10, color="white38")
                ], horizontal_alignment="center"),
                padding=20, bgcolor="#1A1C23", border_radius=15, expand=1, border=ft.Border.all(1, "white10")
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("🧠 RAM USAGE", weight="bold"),
                    ft.Stack([
                        mem_meter, 
                        # FIX: Using top-level Alignment coordinates to prevent the AttributeError
                        ft.Container(content=mem_label, alignment=ft.Alignment(0, 0), width=80, height=80)
                    ]),
                    ft.Text("Memory Allocation", size=10, color="white38")
                ], horizontal_alignment="center"),
                padding=20, bgcolor="#1A1C23", border_radius=15, expand=1, border=ft.Border.all(1, "white10")
            ),
        ], spacing=20),

        # Row 2: Networking
        ft.Container(
            content=ft.Column([
                ft.Text("🌐 NETWORK DIAGNOSTICS"),
                ft.Row([host_input, ft.Button("Ping", on_click=handle_ping)])
            ]),
            padding=20, bgcolor="#1A1C23", border_radius=10
        ),

        # Row 3: Onboarding & Maintenance
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("👤 USER PROVISIONING", weight="bold"),
                    name_in, dept_in,
                    ft.Button("Create User", on_click=lambda _: write_log(logic.onboard_user(name_in.value, dept_in.value)))
                ]),
                padding=20, bgcolor="#1A1C23", border_radius=10, expand=1
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("🧹 MAINTENANCE", weight="bold"),
                    ft.Text("Cleanup and System Inventory", color="white38"),
                    ft.Row([
                        ft.Button("Archive Logs", on_click=lambda _: write_log(logic.archive_logs()), bgcolor="orange", color="black"),
                        ft.Button("System Audit", on_click=handle_inventory, bgcolor="blue", color="white")
                    ])
                ]),
                padding=20, bgcolor="#1A1C23", border_radius=10, expand=1
            ),
        ], spacing=20),

        ft.Text("CONSOLE OUTPUT", size=12, color="white24"),
        ft.Container(content=log_display, bgcolor="#050505", padding=15, border_radius=10, expand=True)
    )

if __name__ == "__main__":
    ft.run(main)