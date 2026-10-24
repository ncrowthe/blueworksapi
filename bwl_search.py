# -*- coding: utf-8 -*-
"""
Blueworks Live Search Tool
Authenticates via OAuth client_credentials and searches processes/artifacts.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import requests
import json
import configparser
import os
import pymupdf as fitz

# -- Config --------------------------------------------------------------------
_cfg = configparser.ConfigParser()
_cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
if not _cfg.read(_cfg_path):
    raise FileNotFoundError("config.ini not found at: " + _cfg_path)
CLIENT_ID     = _cfg.get("blueworks", "client_id")
CLIENT_SECRET = _cfg.get("blueworks", "client_secret")

_raw_mandatory = _cfg.get("blueworks", "mandatory_metadata")
try:
    MANDATORY_METADATA = json.loads(_raw_mandatory)
    if not isinstance(MANDATORY_METADATA, list):
        MANDATORY_METADATA = [MANDATORY_METADATA]
except Exception:
    MANDATORY_METADATA = [
        item.strip().strip('"\'')
        for item in _raw_mandatory.strip("[]").split(",")
        if item.strip()
    ]

# -- OAuth / API constants -----------------------------------------------------
TOKEN_URL        = "https://ibm.blueworkslive.com/oauth/token"
SEARCH_URL       = "https://ibm.blueworkslive.com/scr/api/Search?version=20191214"
DIAGRAM_URL      = "https://ibm.blueworkslive.com/scr/api/PrintDiagram"
GLOSSARY_URL     = "https://ibm.blueworkslive.com/bwl/glossary-values"
PROCESS_DATA_URL = "https://ibm.blueworkslive.com/scr/api/ProcessData?version=20191214"

# -- HTTP helpers --------------------------------------------------------------
def get_token() -> str:
    """Request an OAuth bearer token using client_credentials grant."""
    resp = requests.post(
        TOKEN_URL,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=(
            "grant_type=client_credentials"
            "&client_id=" + CLIENT_ID +
            "&client_secret=" + CLIENT_SECRET
        ),
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        raise ValueError("No access_token in response: " + str(data))
    return token


def check_node_compliance(node: dict, required_fields: list) -> bool:
    """Check that all required metadata fields exist and are non-empty on the node."""
    if not isinstance(node, dict):
        return False
    for field in required_fields:
        # Check exact field name, lowercase-first camelCase, and all lowercase
        val = (
            node.get(field)
            if node.get(field) is not None
            else (
                node.get(field[:1].lower() + field[1:])
                if node.get(field[:1].lower() + field[1:]) is not None
                else node.get(field.lower())
            )
        )
        if not val:
            return False
    return True


def has_mandatory_metadata(process: dict) -> bool:
    """
    Return True if the process carries all mandatory metadata fields configured in config.ini.

    Traverses the process hierarchy to find the root activity node:
    1. Via items mapping: items[processId]["rootActivityID"] -> items[rootId]
    2. Direct nesting: process[processId]["rootActivityID"]
    3. Direct process dictionary
    """
    if not isinstance(process, dict):
        return False

    required_fields = MANDATORY_METADATA
    if not required_fields:
        return True

    process_id = process.get("processId") or process.get("id")
    items = process.get("items")
    target_node = None

    # 1. Look up via items dictionary (standard BWL process JSON)
    if isinstance(items, dict):
        proc_node = items.get(process_id, {}) if process_id else {}
        root_id = proc_node.get("rootActivityID")

        # Fallback: find rootActivityID across items if processId didn't match directly
        if not root_id:
            for item in items.values():
                if isinstance(item, dict) and "rootActivityID" in item:
                    root_id = item.get("rootActivityID")
                    break

        if root_id and isinstance(items.get(root_id), dict):
            target_node = items[root_id]

    # 2. Look up via nested processId -> rootActivityID dict
    if target_node is None and process_id and isinstance(process.get(process_id), dict):
        proc_node = process[process_id]
        root_node = proc_node.get("rootActivityID")
        if isinstance(root_node, dict):
            target_node = root_node
        else:
            target_node = proc_node

    # 3. Look up rootActivityID directly on the process dict
    if target_node is None and isinstance(process.get("rootActivityID"), dict):
        target_node = process["rootActivityID"]

    # 4. Fallback to process dictionary itself
    if target_node is None:
        target_node = process

    return check_node_compliance(target_node, required_fields)


def fetch_process_data(token: str, process_id: str) -> dict:
    """Fetch process JSON details for the given process ID from PROCESS_DATA_URL."""
    resp = requests.get(
        PROCESS_DATA_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept":        "application/json",
        },
        params={"processId": process_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def search_bwl(token: str, search_value: str) -> list:
    """Call the Blueworks Live search endpoint and return a list of process name dicts."""
    resp = requests.post(
        SEARCH_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept":        "application/json",
        },
        params={
            "searchValue":     search_value,
            "searchFieldName": "space_name",
            "returnFields":    "output",
        },
        timeout=30,
    )
    print("DEBUG request URL:", resp.request.url)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for space in data.get("spaces", []):
        space_name = space.get("name", "-")
        print("space_name: " + space_name)
        for process in space.get("processes", []):
            process_id = process.get("id") or process.get("processId")
            activity_count = 0
            for milestone in process.get("milestones", []):
                for activity in milestone.get("activities", []):
                    #print("activity: " + activity.get("name", "-"))
                    activity_count += 1

            # Look up process details using PROCESS_DATA_URL to check for mandatory metadata
            compliant = False
            if process_id:
                try:
                    process_data = fetch_process_data(token, process_id)
                    compliant = has_mandatory_metadata(process_data)
                except Exception as ex:
                    print(f"Error fetching process data for {process_id}: {ex}")
                    compliant = has_mandatory_metadata(process)
            else:
                compliant = has_mandatory_metadata(process)

            results.append({
                "name":       process.get("name", "-"),
                "id":         process.get("id", "-"),
                "type":       "Process",
                "space":      space_name,
                "activities": activity_count,
                "compliance": "Compliant" if compliant else "Non-compliant",
            })
    return results


def fetch_diagram(token: str, process_id: str) -> bytes:
    """Fetch the PrintDiagram PDF for the given process ID and return raw bytes."""
    resp = requests.get(
        DIAGRAM_URL,
        headers={"Authorization": "Bearer " + token},
        params={"processId": process_id},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def fetch_glossary(token: str):
    """Call the Glossary API and return the parsed JSON."""
    resp = requests.get(
        GLOSSARY_URL,
        headers={
            "Authorization": "Bearer " + token,
            "Accept":        "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except ValueError:
        raise ValueError("Glossary response was not JSON (Content-Type: "
                         + resp.headers.get("Content-Type", "unknown") + ")")


def json_to_table(data):
    """Convert parsed JSON into (columns, rows) for display in a table."""
    # Only these columns are displayed; any other key is ignored
    display_columns = ["name", "category", "added-by-user"]

    # Locate a list of records: the data itself, or the first list value in a dict
    records = None
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                records = value
                break
        if records is None:
            return ["key", "value"], [[k, _cell(v)] for k, v in data.items()]
    else:
        return ["value"], [[_cell(data)]]

    columns = []
    for rec in records:
        if isinstance(rec, dict):
            for k in rec:
                if k in display_columns and k not in columns:
                    columns.append(k)
    if not columns:
        return ["value"], [[_cell(rec)] for rec in records]
    rows = [[_cell(rec.get(c, "")) if isinstance(rec, dict) else "" for c in columns]
            for rec in records]
    return columns, rows


def _cell(value) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return "" if value is None else str(value)


# -- Result formatting ---------------------------------------------------------

def format_results(data: dict) -> list:
    """
    Normalise the API response into a flat list of dicts with keys:
    name, type, space.
    """
    items = []
    raw = data.get("items") or data.get("results") or []
    if isinstance(raw, list):
        for entry in raw:
            items.append({
                "name":     entry.get("name", entry.get("title", "-")),
                "id":       entry.get("id", entry.get("id", "-")),                
                "type":     entry.get("type", entry.get("artifactType", "-")),
                "space":    entry.get("spaceName", entry.get("space", "-")),
            })
    # Fall back: show raw JSON when the structure is unexpected
    if not items and data:
        items.append({
            "name":     json.dumps(data, indent=2),
            "type":     "raw response",
            "space":    "",
        })
    return items


# -- Main application window ---------------------------------------------------

class BWLSearchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blueworks Live Custom UI")
        self.resizable(True, True)
        self.minsize(760, 480)
        self._token = None
        self._build_menu()
        self._build_ui()
        self._apply_style()

    # -- UI construction -------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self)
        menubar.add_command(label="Glossary", command=self._on_glossary)
        self.config(menu=menubar)

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self, padx=12, pady=10)
        top.pack(fill=tk.X)

        tk.Label(
            top, text="Blueworks Live Custom UI",
            font=("Segoe UI", 14, "bold")
        ).pack(side=tk.LEFT)

        self._auth_indicator = tk.Label(
            top, text="  Not authenticated",
            fg="#888", font=("Segoe UI", 9)
        )
        self._auth_indicator.pack(side=tk.RIGHT, padx=4)

        # Search bar
        bar = tk.Frame(self, padx=12, pady=4)
        bar.pack(fill=tk.X)

        tk.Label(bar, text="Space Name:", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self._search_var = tk.StringVar(value="000 Test Space")
        self._search_entry = ttk.Entry(
            bar, textvariable=self._search_var,
            font=("Segoe UI", 10), width=55
        )
        self._search_entry.pack(side=tk.LEFT, padx=(6, 8), ipady=4)
        self._search_entry.bind("<Return>", lambda _e: self._on_search())

        self._search_btn = ttk.Button(bar, text="Search", command=self._on_search)
        self._search_btn.pack(side=tk.LEFT)

        self._clear_btn = ttk.Button(bar, text="Clear", command=self._on_clear)
        self._clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        # Status / progress
        status_bar = tk.Frame(self, padx=12)
        status_bar.pack(fill=tk.X)

        self._status_var = tk.StringVar(value="Enter a search term and press Search.")
        tk.Label(
            status_bar, textvariable=self._status_var,
            font=("Segoe UI", 9), anchor="w"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._progress = ttk.Progressbar(status_bar, mode="indeterminate", length=120)
        self._progress.pack(side=tk.RIGHT, pady=2)

        # Results table
        table_frame = tk.Frame(self, padx=12, pady=8)
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("name", "id", "type", "space", "activities", "compliance")
        self._tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", selectmode="browse",
            displaycolumns=("name", "type", "space", "activities", "compliance")  # "id" kept but hidden
        )

        col_cfg = {
            "name":     ("Name",          360, tk.W),
            "id":       ("Id",            360, tk.W),            
            "type":     ("Type",          110, tk.CENTER),
            "space":    ("Space",         160, tk.W),
            "activities": ("Activities",  90, tk.CENTER),
            "compliance": ("Compliance",  110, tk.CENTER),
        }
        for col, (heading, width, anchor) in col_cfg.items():
            self._tree.heading(col, text=heading)
            self._tree.column(col, width=width, anchor=anchor, stretch=(col == "name"))

        vsb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,   command=self._tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)
        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Result count footer
        self._count_var = tk.StringVar(value="")
        tk.Label(
            self, textvariable=self._count_var,
            font=("Segoe UI", 9), fg="#555",
            anchor="e", padx=12, pady=4
        ).pack(fill=tk.X)

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview",         font=("Segoe UI", 9), rowheight=24)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TButton",          font=("Segoe UI", 9))
        style.configure("TEntry",           font=("Segoe UI", 10))
        self._tree.tag_configure("odd",  background="#f7f8fa")
        self._tree.tag_configure("even", background="#ffffff")
        self._tree.tag_configure("non_compliant", background="#ffebee", foreground="#c62828")
        self._tree.tag_configure("compliant",     background="#e8f5e9", foreground="#2e7d32")

    # -- Event handlers --------------------------------------------------------

    def _on_clear(self):
        self._search_var.set("")
        self._tree.delete(*self._tree.get_children())
        self._count_var.set("")
        self._status_var.set("Enter a search term and press Search.")
        self._search_entry.focus()

    def _on_search(self):
        query = self._search_var.get().strip()
        if not query:
            messagebox.showwarning("Input required", "Please enter a search term.")
            return
        self._set_busy(True)
        self._tree.delete(*self._tree.get_children())
        self._count_var.set("")
        threading.Thread(target=self._do_search, args=(query,), daemon=True).start()

    def _do_search(self, query):
        """Runs on a background thread - does not touch widgets directly."""
        try:
            if not self._token:
                self._set_status("Authenticating...")
                self._token = get_token()
                self.after(0, lambda: self._auth_indicator.config(
                    text="  Authenticated", fg="#2d8a4e"
                ))

            self._set_status('Searching for "' + query + '"...')
            results = search_bwl(self._token, query)
            self.after(0, lambda r=results, q=query: self._populate_results(r, q))

        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (401, 403):
                self._token = None
                self.after(0, lambda: self._auth_indicator.config(
                    text="  Not authenticated", fg="#888"
                ))
            msg = str(exc)
            self.after(0, lambda m=msg: self._show_error(m))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self._show_error(m))
        finally:
            self.after(0, lambda: self._set_busy(False))

    # -- UI update helpers (must run on main thread) ---------------------------

    def _populate_results(self, results, query):
        for i, item in enumerate(results):
            if item.get("compliance") == "Non-compliant":
                tag = "non_compliant"
            else:
                tag = "compliant"
            self._tree.insert("", tk.END, values=(
                item["name"], item["id"], item["type"], item["space"],
                item.get("activities", ""),
                item.get("compliance", "")
            ), tags=(tag,))
        count = len(results)
        suffix = "s" if count != 1 else ""
        self._count_var.set(str(count) + " result" + suffix + " found.")
        self._set_status(
            "Done - " + str(count) + " result" + suffix +
            ' for "' + query + '".'
        )

    def _set_busy(self, busy):
        state = tk.DISABLED if busy else tk.NORMAL
        self._search_btn.config(state=state)
        self._clear_btn.config(state=state)
        self._search_entry.config(state=state)
        if busy:
            self._progress.start(12)
        else:
            self._progress.stop()

    def _set_status(self, msg):
        self.after(0, lambda m=msg: self._status_var.set(m))

    def _on_row_select(self, _event):
        selected = self._tree.selection()
        if not selected:
            return
        values = self._tree.item(selected[0], "values")
        # values order: name, id, type, space, activities, compliance
        process_id = values[1]
        if not process_id or process_id == "-":
            return
        self._set_busy(True)
        self._set_status("Fetching diagram for process " + process_id + "...")
        threading.Thread(
            target=self._do_fetch_diagram, args=(process_id,), daemon=True
        ).start()

    def _do_fetch_diagram(self, process_id):
        """Background thread: fetch PDF bytes then hand off to viewer."""
        try:
            if not self._token:
                self._token = get_token()
            pdf_bytes = fetch_diagram(self._token, process_id)
            self.after(0, lambda b=pdf_bytes, pid=process_id: self._show_diagram(b, pid))
        except requests.HTTPError as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self._show_error(m))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self._show_error(m))
        finally:
            self.after(0, lambda: self._set_busy(False))

    def _show_diagram(self, pdf_bytes, process_id):
        """Render every page of the PDF and show them in a scrollable Toplevel window."""


        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        win = tk.Toplevel(self)
        win.title("Diagram - " + process_id)
        win.minsize(800, 600)

        # Toolbar
        toolbar = ttk.Frame(win, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        def _save_pdf():
            filename = filedialog.asksaveasfilename(
                parent=win,
                title="Save PDF Diagram",
                defaultextension=".pdf",
                initialfile=f"{process_id}.pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
            )
            if filename:
                try:
                    with open(filename, "wb") as f:
                        f.write(pdf_bytes)
                    messagebox.showinfo("Saved", f"PDF saved successfully to:\n{filename}", parent=win)
                except Exception as ex:
                    messagebox.showerror("Save Error", f"Failed to save file:\n{ex}", parent=win)

        download_btn = ttk.Button(toolbar, text="Download PDF", command=_save_pdf)
        download_btn.pack(side=tk.LEFT)

        # Scrollable canvas
        canvas = tk.Canvas(win, bg="#ffffff")
        vsb = ttk.Scrollbar(win, orient=tk.VERTICAL, command=canvas.yview)
        hsb = ttk.Scrollbar(win, orient=tk.HORIZONTAL, command=canvas.xview)
        canvas.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        vsb.pack(side=tk.RIGHT,  fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(fill=tk.BOTH, expand=True)

        # Render each page as a PNG image and stack vertically
        images = []   # keep references alive
        y_offset = 10
        for page in doc:
            pix = page.get_pixmap(dpi=120)
            img_data = pix.tobytes("png")
            from tkinter import PhotoImage
            import base64
            tk_img = PhotoImage(data=base64.b64encode(img_data))
            images.append(tk_img)
            canvas.create_image(10, y_offset, anchor="nw", image=tk_img)
            y_offset += pix.height + 10

        canvas.configure(scrollregion=canvas.bbox("all"))
        # Store image refs on the window so they aren't garbage collected
        setattr(win, "_diagram_images", images)
        doc.close()
        self._set_status("Diagram loaded for process " + process_id + ".")

    # -- Glossary --------------------------------------------------------------

    def _on_glossary(self):
        self._set_busy(True)
        self._set_status("Fetching glossary...")
        threading.Thread(target=self._do_glossary, daemon=True).start()

    def _do_glossary(self):
        """Background thread: call the Glossary API then hand off to the table window."""
        try:
            if not self._token:
                self._set_status("Authenticating...")
                self._token = get_token()
                self.after(0, lambda: self._auth_indicator.config(
                    text="  Authenticated", fg="#2d8a4e"
                ))
            data = fetch_glossary(self._token)
            columns, rows = json_to_table(data)
            self.after(0, lambda c=columns, r=rows: self._show_glossary(c, r))
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (401, 403):
                self._token = None
                self.after(0, lambda: self._auth_indicator.config(
                    text="  Not authenticated", fg="#888"
                ))
            msg = str(exc)
            self.after(0, lambda m=msg: self._show_error(m))
        except Exception as exc:
            msg = str(exc)
            self.after(0, lambda m=msg: self._show_error(m))
        finally:
            self.after(0, lambda: self._set_busy(False))

    def _show_glossary(self, columns, rows):
        win = tk.Toplevel(self)
        win.title("Glossary")
        win.minsize(600, 400)

        frame = tk.Frame(win, padx=12, pady=8)
        frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=180, anchor=tk.W)
        tree.tag_configure("odd",  background="#f7f8fa")
        tree.tag_configure("even", background="#ffffff")
        for i, row in enumerate(rows):
            tree.insert("", tk.END, values=row, tags=("odd" if i % 2 else "even",))

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL,   command=tree.yview)
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        suffix = "" if len(rows) == 1 else "s"
        self._set_status("Glossary loaded - " + str(len(rows)) + " row" + suffix + ".")

    def _show_error(self, msg):
        self._set_status("Error: " + msg)
        messagebox.showerror("Request failed", msg)


# -- Entry point ---------------------------------------------------------------

if __name__ == "__main__":
    app = BWLSearchApp()
    app.mainloop()
