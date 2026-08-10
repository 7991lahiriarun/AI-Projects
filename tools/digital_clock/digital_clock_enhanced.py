"""
Enhanced Digital Multi-Timezone Clock (Tkinter)

Features implemented:
- Multiple timezones (add/remove)
- Timezone autocomplete (common IANA zones)
- UTC offset and DST indicator per zone
- Analog + digital display per zone
- Alarms (one-time and recurring) per timezone with audible & visual alert
- Save/load layout and alarms to local JSON (clock_state.json)

Run:
  python digital_clock_enhanced.py

Requires: Python 3.9+ (zoneinfo). If your system lacks tzdata, install tzdata:
  pip install tzdata

This is an enhanced standalone desktop app intended for local use.
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import json
import os
import math
import platform
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

APP_STATE_FILE = "clock_state.json"

# A curated list of common IANA timezones for autocomplete
COMMON_ZONES = [
    "UTC",
    "Europe/London",
    "Europe/Berlin",
    "Europe/Paris",
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Sao_Paulo",
    "America/Argentina/Buenos_Aires",
    "Asia/Kolkata",
    "Asia/Shanghai",
    "Asia/Tokyo",
    "Asia/Hong_Kong",
    "Asia/Singapore",
    "Australia/Sydney",
    "Pacific/Auckland",
]

# Helper: format offset timedelta to +HH:MM
def format_utc_offset(td: timedelta):
    if td is None:
        return ""
    total = int(td.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    hrs = total // 3600
    mins = (total % 3600) // 60
    return f"UTC{sign}{int(hrs):02d}:{int(mins):02d}"

class Alarm:
    def __init__(self, tz, time_str, recurring=False, label=""):
        # time_str is HH:MM in the target timezone
        self.tz = tz
        self.time_str = time_str
        self.recurring = recurring
        self.label = label
        self.triggered_today = False

    def to_dict(self):
        return {"tz": self.tz, "time": self.time_str, "recurring": self.recurring, "label": self.label}

    @classmethod
    def from_dict(cls, d):
        return cls(d["tz"], d["time"], d.get("recurring", False), d.get("label", ""))

class MultiClockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital + Analog Multi-Timezone Clock")
        self.geometry("760x600")
        self.resizable(True, True)
        self.zone_frames = {}  # tz -> frame widgets
        self.alarms = []  # list of Alarm
        self._build_ui()
        self.load_state()
        if not self.zone_frames:
            for z in ["UTC", "America/New_York", "Asia/Kolkata"]:
                self.add_zone(z)
        self.update_times()

    def _build_ui(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        ctrl = ttk.Frame(main)
        ctrl.pack(fill="x")

        ttk.Label(ctrl, text="Add timezone:").pack(side="left")
        self.tz_var = tk.StringVar()
        self.tz_combo = ttk.Combobox(ctrl, textvariable=self.tz_var)
        self.tz_combo['values'] = COMMON_ZONES
        self.tz_combo['width'] = 30
        self.tz_combo.pack(side="left", padx=6)
        add_btn = ttk.Button(ctrl, text="Add", command=self._on_add)
        add_btn.pack(side="left")

        remove_btn = ttk.Button(ctrl, text="Remove selected", command=self._on_remove)
        remove_btn.pack(side="left", padx=6)

        save_btn = ttk.Button(ctrl, text="Save layout", command=self.save_state)
        save_btn.pack(side="right")

        load_btn = ttk.Button(ctrl, text="Load layout", command=self.load_state)
        load_btn.pack(side="right", padx=(0,6))

        alarm_btn = ttk.Button(ctrl, text="Manage Alarms", command=self._manage_alarms)
        alarm_btn.pack(side="right", padx=(0,12))

        # Canvas area for clocks
        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(fill="both", expand=True, pady=(10,0))

        self.canvas = tk.Canvas(canvas_frame)
        self.scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.inner, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

        # Selection tracking
        self.selected_zone = tk.StringVar(value="")

    def _on_add(self):
        tz = self.tz_var.get().strip()
        if not tz:
            return
        if tz in self.zone_frames:
            messagebox.showinfo("Exists", f"Timezone {tz} already added")
            return
        valid = self._validate_timezone(tz)
        if not valid:
            if not messagebox.askyesno("Unknown timezone", f"Timezone '{tz}' could not be validated. Add anyway?"):
                return
        self.add_zone(tz)
        self.tz_var.set("")

    def _validate_timezone(self, tz):
        if ZoneInfo is None:
            return True
        try:
            ZoneInfo(tz)
            return True
        except Exception:
            return False

    def _on_remove(self):
        tz = self.selected_zone.get()
        if not tz:
            messagebox.showinfo("Select", "No timezone selected to remove. Click a timezone's header to select it.")
            return
        if tz in self.zone_frames:
            frame, _ = self.zone_frames.pop(tz)
            frame.destroy()
            self.selected_zone.set("")

    def add_zone(self, tz_name):
        frame = ttk.Frame(self.inner, padding=8, relief='ridge')
        frame.pack(fill='x', pady=6, padx=6)

        header = ttk.Frame(frame)
        header.pack(fill='x')

        lbl = ttk.Label(header, text=tz_name, font=(None, 11, 'bold'))
        lbl.pack(side='left')

        info_lbl = ttk.Label(header, text='', foreground='#9ad')
        info_lbl.pack(side='left', padx=(8,0))

        sel_btn = ttk.Button(header, text='Select', command=lambda t=tz_name, f=frame: self._select_zone(t, f))
        sel_btn.pack(side='right')

        add_alarm_btn = ttk.Button(header, text='Add Alarm', command=lambda t=tz_name: self._add_alarm_for(t))
        add_alarm_btn.pack(side='right', padx=6)

        body = ttk.Frame(frame)
        body.pack(fill='x', pady=(6,0))

        # Digital label
        time_label = ttk.Label(body, text='--:--:--', font=(None, 16))
        time_label.pack(side='left', padx=(0,10))

        # Offset & DST
        offset_label = ttk.Label(body, text='', width=14)
        offset_label.pack(side='left')

        # Analog canvas
        analog = tk.Canvas(body, width=120, height=120)
        analog.pack(side='right')

        self.zone_frames[tz_name] = (frame, { 'time': time_label, 'offset': offset_label, 'analog': analog, 'info': info_lbl })

    def _select_zone(self, tz, frame):
        # visual highlight
        for t, (fr, _) in self.zone_frames.items():
            fr.config(style='')
        frame.config(style='Selected.TFrame')
        self.selected_zone.set(tz)

    def _add_alarm_for(self, tz):
        # ask HH:MM and recurring
        val = simpledialog.askstring("Alarm time", f"Enter alarm time in {tz} (24h HH:MM):")
        if not val:
            return
        try:
            hh, mm = val.split(':')
            hh = int(hh); mm = int(mm)
            assert 0<=hh<24 and 0<=mm<60
        except Exception:
            messagebox.showerror("Invalid", "Time must be HH:MM in 24-hour format")
            return
        rec = messagebox.askyesno("Recurring", "Make this alarm recurring daily?")
        label = simpledialog.askstring("Label (optional)", "Optional label for the alarm:") or ''
        a = Alarm(tz, f"{hh:02d}:{mm:02d}", recurring=rec, label=label)
        self.alarms.append(a)
        messagebox.showinfo("Alarm set", f"Alarm set for {tz} at {a.time_str} (recurring={a.recurring})")
        self.save_state()

    def _manage_alarms(self):
        # show a simple list and allow delete
        top = tk.Toplevel(self)
        top.title('Alarms')
        top.geometry('400x300')
        lf = ttk.Frame(top, padding=8)
        lf.pack(fill='both', expand=True)
        tree = ttk.Treeview(lf, columns=('tz','time','rec','label'), show='headings')
        tree.heading('tz', text='Timezone'); tree.heading('time', text='Time'); tree.heading('rec', text='Recurring'); tree.heading('label', text='Label')
        tree.pack(fill='both', expand=True)
        for i,a in enumerate(self.alarms):
            tree.insert('', 'end', iid=str(i), values=(a.tz, a.time_str, str(a.recurring), a.label))
        def delete_selected():
            sel = tree.selection()
            if not sel: return
            idx = int(sel[0])
            del self.alarms[idx]
            tree.delete(sel[0])
            # rebuild iids
            for i,item in enumerate(tree.get_children()):
                tree.item(item, iid=str(i))
            self.save_state()
        del_btn = ttk.Button(lf, text='Delete Selected', command=delete_selected)
        del_btn.pack(pady=6)

    def update_times(self):
        now_utc = datetime.utcnow()
        for tz, (frame, widgets) in list(self.zone_frames.items()):
            try:
                if ZoneInfo is None:
                    raise RuntimeError('zoneinfo not available')
                z = ZoneInfo(tz)
                now = datetime.now(z)
                timestr = now.strftime('%Y-%m-%d %H:%M:%S')
                widgets['time'].config(text=timestr)

                # offset
                off = now.utcoffset()
                widgets['offset'].config(text=format_utc_offset(off))

                # DST indicator
                dst = now.dst()
                widgets['info'].config(text=('DST' if dst and dst!=timedelta(0) else 'STD'))

                # analog draw
                self._draw_analog(widgets['analog'], now)

            except Exception:
                widgets['time'].config(text='Invalid timezone')
                widgets['offset'].config(text='')
                widgets['info'].config(text='')

        # check alarms
        self._check_alarms()
        self.after(1000, self.update_times)

    def _draw_analog(self, canvas, now):
        canvas.delete('all')
        w = int(canvas['width']); h = int(canvas['height'])
        cx = w//2; cy = h//2; r = min(cx,cy)-6
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, fill='#0f1720', outline='#2c3e50')
        # hour marks
        for i in range(12):
            angle = math.radians(i*30-90)
            x1 = cx + (r-6)*math.cos(angle); y1 = cy + (r-6)*math.sin(angle)
            x2 = cx + (r-2)*math.cos(angle); y2 = cy + (r-2)*math.sin(angle)
            canvas.create_line(x1,y1,x2,y2, fill='#9aa', width=2)
        hour = now.hour % 12 + now.minute/60.0
        minute = now.minute + now.second/60.0
        second = now.second
        # hour hand
        self._draw_hand(canvas, cx, cy, hour/12*360-90, r*0.5, '#f3f4f6', 4)
        # minute hand
        self._draw_hand(canvas, cx, cy, minute/60*360-90, r*0.75, '#cbd5e1', 3)
        # second hand
        self._draw_hand(canvas, cx, cy, second/60*360-90, r*0.85, '#fb7185', 1)

    def _draw_hand(self, canvas, cx, cy, angle_deg, length, color, width):
        angle = math.radians(angle_deg)
        x = cx + length*math.cos(angle); y = cy + length*math.sin(angle)
        canvas.create_line(cx, cy, x, y, fill=color, width=width, capstyle='round')

    def _check_alarms(self):
        for a in self.alarms:
            try:
                if ZoneInfo is None:
                    continue
                z = ZoneInfo(a.tz)
                now = datetime.now(z)
                hhmm = now.strftime('%H:%M')
                if hhmm == a.time_str:
                    if not a.triggered_today:
                        self._trigger_alarm(a)
                        a.triggered_today = True
                else:
                    a.triggered_today = False
            except Exception:
                continue

    def _trigger_alarm(self, alarm: Alarm):
        # visual highlight on the timezone frame if present
        t = alarm.tz
        msg = f"Alarm: {alarm.label or alarm.time_str} ({t})"
        try:
            frame, _ = self.zone_frames[t]
            frame.config(style='Alarm.TFrame')
        except Exception:
            pass
        # audible
        try:
            if platform.system() == 'Windows':
                import winsound
                winsound.Beep(1000, 700)
            else:
                # bell or simple beep via tkinter
                self.bell()
        except Exception:
            pass
        # popup
        messagebox.showinfo('Alarm', msg)
        # reset highlight after a short while
        self.after(1200, self._clear_alarm_highlights)
        # if not recurring, remove alarm
        if not alarm.recurring:
            try:
                self.alarms.remove(alarm)
                self.save_state()
            except Exception:
                pass

    def _clear_alarm_highlights(self):
        for t, (fr, _) in self.zone_frames.items():
            fr.config(style='')

    def save_state(self):
        state = {
            'zones': list(self.zone_frames.keys()),
            'alarms': [a.to_dict() for a in self.alarms]
        }
        try:
            with open(APP_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            messagebox.showinfo('Saved', f'Layout saved to {APP_STATE_FILE}')
        except Exception as e:
            messagebox.showerror('Error', f'Could not save layout: {e}')

    def load_state(self):
        if not os.path.exists(APP_STATE_FILE):
            return
        try:
            with open(APP_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
            # remove existing
            for tz in list(self.zone_frames.keys()):
                fr,_ = self.zone_frames.pop(tz)
                fr.destroy()
            for z in state.get('zones', []):
                self.add_zone(z)
            self.alarms = [Alarm.from_dict(d) for d in state.get('alarms', [])]
            messagebox.showinfo('Loaded', f'Layout loaded from {APP_STATE_FILE}')
        except Exception as e:
            messagebox.showerror('Error', f'Could not load layout: {e}')

if __name__ == '__main__':
    style = ttk.Style()
    style.configure('Selected.TFrame', background='#d0e7ff')
    style.configure('Alarm.TFrame', background='#ffdfdf')
    app = MultiClockApp()
    app.mainloop()
