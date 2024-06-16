from typing import Any, Callable

import tkinter as tk
from tkinter import ttk, messagebox as msg, filedialog as fd

from cli import Command
import gui.style as style
from logger import LogFunction, Logger, info, set_global_logger
import subcommand.common as common

# yoinked from another of my projects
def limit_textvar_numeric_length(var: tk.StringVar, count: int) -> None:
    """Limit value for text variable to a number of specified length"""
    def limit_tracer(*_): # since we don't need the tk args
        filtered = filter(lambda c: c.isnumeric(), var.get()[:count])
        var.set(''.join(filtered))

    var.trace_add("write", limit_tracer)

MAX_DISPLAY_WIDTH: int = 80

Job = Callable[[], None]

class InteractiveMode:
    '''Implements features for a GUI interactive mode

    Basic functionality is to determine what subcommand the uesr wants to
    select and then fill in the blanks in the command line parser objects for
    the specified subcommand, then pass control to subcommand function and
    quit.

    This class wraps GUI objects from tkinter

    Constructor Parameters:
        prog_args: parsed dictionary of command-line arguments passed to the
            program by the user
    '''

    def __init__(self,
                 commands: list[Command],
                 prog_args: dict[str, Any] | None = None) -> None:

        self.commands: dict[str, Command] = {
                command.name: command
                for command in commands
                }

        self.prog_args: dict[str, Any] = prog_args \
                if prog_args is not None \
                else {}

        self.vars: dict[str, tk.StringVar] = {}

        self.init_main_window()
        style.init_styles()
        self.override_global_logger()

        self.filetypes_dict: dict[str, tuple[str, ...]] = {
                "Srt Subtitle File": ("*.srt",),
                "All files": ("*",)
                }

    def init_main_window(self) -> None:
        '''Initialise GUI components'''
        self.root: tk.Tk = tk.Tk()
        self.root.title("{} {}".format(
            self.get_program_name(),
            self.get_program_version()))
        self.root.minsize(450, 300)

        frame = ttk.Frame(self.root, style = "Page.Sub.TFrame", padding = 5)
        frame.pack(expand = True, fill = "both")

        frm_input = ttk.Frame(frame, style = "Page.Sub.TFrame")
        frm_input.pack(fill = "x", padx = 2.5, pady = 2.5)

        lbl_file = ttk.Label(frm_input, style = "Page.TLabel")
        lbl_file["text"] = "File:"
        lbl_file.pack(side = "left", anchor = "w")

        self.vars["input"] = tk.StringVar(frm_input)

        txt_input = ttk.Entry(frm_input)
        txt_input["textvariable"] = self.vars["input"]
        txt_input["state"] = "readonly"
        txt_input.pack(side = "left", expand = True, fill = "x", padx = 2.5)

        btn_load_file = ttk.Button(frm_input)
        btn_load_file["text"] = "Browse..."
        btn_load_file["command"] = self.on_open_file
        btn_load_file.pack(side = "right")

        frm_edit = ttk.Frame(frame, style = "Page.Sub.TFrame")
        frm_edit.pack(expand = True, fill = "both", padx = 2.5, pady = 2.5)
        frm_edit.columnconfigure((0, 1), weight = 1, pad = 2.5)
        frm_edit.rowconfigure((0, 1), pad = 2.5)
        self.frm_edit = frm_edit

        self.init_delay_frame(0, 0, "nw")
        self.init_info_frame(0, 1, "ne")
        self.init_trim_frame(1, 0, "nw")
        self.init_output_frame(frame)

    def init_delay_frame(self, row: int, column: int, sticky: str) -> None:
        '''Initialise frame for editing delay at specified position'''
        frm_delay = ttk.Frame(self.frm_edit, style = "Page.Sub.TFrame")
        frm_delay.grid(row = row, column = column, sticky = sticky)
        frm_delay.columnconfigure(tuple(range(5)), pad = 2.5)
        frm_delay.columnconfigure(tuple(range(1, 5)), weight = 1)
        frm_delay.rowconfigure(tuple(range(4)), pad = 2.5)

        lbl_delay = ttk.Label(frm_delay, style = "Page.TLabel")
        lbl_delay["text"] = "Delay:"
        lbl_delay["state"] = "disabled"
        lbl_delay.grid(row = 0, column = 0)

        frm_delay_input = ttk.Frame(frm_delay, style = "Page.Sub.TFrame")
        frm_delay_input.grid(
                row = 0, column  = 1, columnspan = 4, sticky = "w")

        var_delay = tk.StringVar(frm_delay_input)
        def limit_delay_tracer(*_):
            value: str = var_delay.get()
            if value == '':
                return

            var_delay.set("{}{}".format(
                '-' if value[0] == '-' else '',
                ''.join(filter(lambda c: c.isnumeric(), value))))

        var_delay.trace_add("write", limit_delay_tracer)
        self.vars["delay"] = var_delay

        txt_delay = ttk.Entry(frm_delay_input)
        txt_delay["width"] = 6
        txt_delay["textvariable"] = self.vars["delay"]
        txt_delay["state"]  = "disabled"
        txt_delay.pack(side = "left")

        # TODO implement unit switching
        #self.vars["unit"] = tk.StringVar(frm_delay_input, "ms")

        lbl_delay_unit = ttk.Label(frm_delay_input, style = "Page.TLabel")
        lbl_delay_unit["text"] = "ms"
        #lbl_delay_unit["textvariable"] = self.vars["unit"]
        lbl_delay_unit["state"] = "disabled"
        lbl_delay_unit.pack(side = "left")

        btn_pablo_100_less = ttk.Button(frm_delay)
        btn_pablo_100_less["text"] = "-100ms"
        btn_pablo_100_less["width"] = -1
        btn_pablo_100_less["state"] = "disabled"
        btn_pablo_100_less["command"] = lambda: self.increment_delay(-100)
        btn_pablo_100_less.grid(row = 1, column = 1, sticky = "ew")
        btn_pablo_1000_less = ttk.Button(frm_delay)
        btn_pablo_1000_less["text"] = "-1s"
        btn_pablo_1000_less["width"] = -1
        btn_pablo_1000_less["state"] = "disabled"
        btn_pablo_1000_less["command"] = lambda: self.increment_delay(-1000)
        btn_pablo_1000_less.grid(row = 1, column = 2, sticky = "ew")
        btn_pablo_5000_less = ttk.Button(frm_delay)
        btn_pablo_5000_less["text"] = "-5s"
        btn_pablo_5000_less["width"] = -1
        btn_pablo_5000_less["state"] = "disabled"
        btn_pablo_5000_less["command"] = lambda: self.increment_delay(-5000)
        btn_pablo_5000_less.grid(row = 1, column = 3, sticky = "ew")
        btn_pablo_10000_less = ttk.Button(frm_delay)
        btn_pablo_10000_less["text"] = "-10s"
        btn_pablo_10000_less["width"] = -1
        btn_pablo_10000_less["state"] = "disabled"
        btn_pablo_10000_less["command"] = lambda: self.increment_delay(-10000)
        btn_pablo_10000_less.grid(row = 1, column = 4, sticky = "ew")
        btn_pablo_60000_less = ttk.Button(frm_delay)
        btn_pablo_60000_less["text"] = "-1m"
        btn_pablo_60000_less["width"] = -1
        btn_pablo_60000_less["state"] = "disabled"
        btn_pablo_60000_less["command"] = lambda: self.increment_delay(-60000)
        btn_pablo_60000_less.grid(row = 1, column = 5, sticky = "ew")
        btn_pablo_100_more = ttk.Button(frm_delay)
        btn_pablo_100_more["text"] = "+100ms"
        btn_pablo_100_more["width"] = -1
        btn_pablo_100_more["state"] = "disabled"
        btn_pablo_100_more["command"] = lambda: self.increment_delay(100)
        btn_pablo_100_more.grid(row = 2, column = 1, sticky = "ew")
        btn_pablo_1000_more = ttk.Button(frm_delay)
        btn_pablo_1000_more["text"] = "+1s"
        btn_pablo_1000_more["width"] = -1
        btn_pablo_1000_more["state"] = "disabled"
        btn_pablo_1000_more["command"] = lambda: self.increment_delay(1000)
        btn_pablo_1000_more.grid(row = 2, column = 2, sticky = "ew")
        btn_pablo_5000_more = ttk.Button(frm_delay)
        btn_pablo_5000_more["text"] = "+5s"
        btn_pablo_5000_more["width"] = -1
        btn_pablo_5000_more["state"] = "disabled"
        btn_pablo_5000_more["command"] = lambda: self.increment_delay(5000)
        btn_pablo_5000_more.grid(row = 2, column = 3, sticky = "ew")
        btn_pablo_10000_more = ttk.Button(frm_delay)
        btn_pablo_10000_more["text"] = "+10s"
        btn_pablo_10000_more["width"] = -1
        btn_pablo_10000_more["state"] = "disabled"
        btn_pablo_10000_more["command"] = lambda: self.increment_delay(10000)
        btn_pablo_10000_more.grid(row = 2, column = 4, sticky = "ew")
        btn_pablo_60000_more = ttk.Button(frm_delay)
        btn_pablo_60000_more["text"] = "+1m"
        btn_pablo_60000_more["width"] = -1
        btn_pablo_60000_more["state"] = "disabled"
        btn_pablo_60000_more["command"] = lambda: self.increment_delay(60000)
        btn_pablo_60000_more.grid(row = 2, column = 5, sticky = "ew")

        #rb_unit_ms = ttk.Radiobutton(frm_delay, style = "Page.TRadiobutton")
        #rb_unit_ms["text"] = "ms"
        #rb_unit_ms["value"] = "ms"
        #rb_unit_ms["variable"] = self.vars["unit"]
        #rb_unit_ms["state"] = "disabled"
        #rb_unit_ms.grid(row = 3, column = 1)

        #rb_unit_s = ttk.Radiobutton(frm_delay, style = "Page.TRadiobutton")
        #rb_unit_s["text"] = "s"
        #rb_unit_s["value"] = "s"
        #rb_unit_s["variable"] = self.vars["unit"]
        #rb_unit_s["state"] = "disabled"
        #rb_unit_s.grid(row = 3, column = 2)

        def reset_delay_frame_fn() -> None:
            lbl_delay["state"] = "normal"
            self.vars["delay"].set(str(0))
            txt_delay["state"]  = "normal"
            lbl_delay_unit["state"] = "normal"
            btn_pablo_100_less["state"] = "normal"
            btn_pablo_1000_less["state"] = "normal"
            btn_pablo_5000_less["state"] = "normal"
            btn_pablo_10000_less["state"] = "normal"
            btn_pablo_60000_less["state"] = "normal"
            btn_pablo_100_more["state"] = "normal"
            btn_pablo_1000_more["state"] = "normal"
            btn_pablo_5000_more["state"] = "normal"
            btn_pablo_10000_more["state"] = "normal"
            btn_pablo_60000_more["state"] = "normal"
            #self.vars["unit"].set("ms")
            #rb_unit_ms["state"] = "normal"
            #rb_unit_s["state"] = "normal"

        self.reset_delay_frame_fn = reset_delay_frame_fn

    def init_info_frame(self, row: int, column: int, sticky: str) -> None:
        '''Initialise information frame at specified postion'''
        frm_info = ttk.Frame(self.frm_edit, padding = 5)
        frm_info["style"] = "Page.Sub.TFrame" #hidden
        frm_info.grid(row = row, rowspan = 2, column = column, sticky = sticky)
        frm_info.columnconfigure(0, pad = 2.5)

        self.vars["info"] = tk.StringVar(frm_info)

        lbl_info_value = ttk.Label(frm_info, style = "Page.TLabel")
        lbl_info_value["textvariable"] = self.vars["info"]
        lbl_info_value["state"] = "disabled"
        lbl_info_value.grid(row = 0, column = 1)

        def reset_info_frame_fn() -> None:
            frm_info["style"] = "Page.TFrame" #bordered
            lbl_info_value["state"] = "normal"

        self.reset_info_frame_fn = reset_info_frame_fn

    def init_trim_frame(self, row: int, column: int, sticky: str) -> None:
        '''Initialise frame for trimming at specified position'''
        frm_trim = ttk.Frame(self.frm_edit, style = "Page.Sub.TFrame")
        frm_trim.grid(row = row, column = column, sticky = sticky)
        frm_trim.columnconfigure(0, pad = 2.5)
        frm_trim.rowconfigure(tuple(range(5)), pad = 2.5)

        lbl_trim = ttk.Label(frm_trim, style = "Page.TLabel")
        lbl_trim["text"] = "Trim:"
        lbl_trim["state"] = "disabled"
        lbl_trim.grid(row = 0, column = 0)

        self.vars["trim_option"] = tk.StringVar(frm_trim, "none")

        rb_trim_option_none = ttk.Radiobutton(
                frm_trim, style = "Page.TRadiobutton")
        rb_trim_option_none["text"] = "Don't trim"
        rb_trim_option_none["value"] = "none"
        rb_trim_option_none["variable"] = self.vars["trim_option"]
        rb_trim_option_none["state"] = "disabled"
        rb_trim_option_none.grid(row = 0, column = 1, sticky = "w")

        rb_trim_option_line = ttk.Radiobutton(
                frm_trim, style = "Page.TRadiobutton")
        rb_trim_option_line["text"] = "Trim by line number"
        rb_trim_option_line["value"] = "line"
        rb_trim_option_line["variable"] = self.vars["trim_option"]
        rb_trim_option_line["state"] = "disabled"
        rb_trim_option_line.grid(row = 1, column = 1, sticky = "w")

        frm_trim_line = ttk.Frame(frm_trim, style = "Page.Sub.TFrame")
        frm_trim_line.grid(row = 2, column = 1, sticky = "w")
        frm_trim_line.columnconfigure(0, pad = 2.5)
        frm_trim_line.rowconfigure((0, 1), pad = 2.5)

        lbl_from_line = ttk.Label(frm_trim_line, style = "Page.TLabel")
        lbl_from_line["text"] = "From:"
        lbl_from_line["state"] = "disabled"
        lbl_from_line.grid(row = 0, column = 0, sticky = "e")

        self.vars["trim_from_line"] = tk.StringVar(frm_trim_line)

        txt_from_line = ttk.Entry(frm_trim_line)
        txt_from_line["width"] = 6
        txt_from_line["textvariable"] = self.vars["trim_from_line"]
        txt_from_line["state"] = "disabled"
        txt_from_line.grid(row = 0, column = 1)

        lbl_to_line = ttk.Label(frm_trim_line, style = "Page.TLabel")
        lbl_to_line["text"] = "To:"
        lbl_to_line["state"] = "disabled"
        lbl_to_line.grid(row = 1, column = 0, sticky = "e")

        self.vars["trim_to_line"] = tk.StringVar(frm_trim_line)

        txt_to_line = ttk.Entry(frm_trim_line)
        txt_to_line["width"] = 6
        txt_to_line["textvariable"] = self.vars["trim_to_line"]
        txt_to_line["state"] = "disabled"
        txt_to_line.grid(row = 1, column = 1)

        rb_trim_option_time = ttk.Radiobutton(
                frm_trim, style = "Page.TRadiobutton")
        rb_trim_option_time["text"] = "Trim by timestamp"
        rb_trim_option_time["value"] = "time"
        rb_trim_option_time["variable"] = self.vars["trim_option"]
        rb_trim_option_time["state"] = "disabled"
        rb_trim_option_time.grid(row = 3, column = 1, sticky = "w")

        frm_trim_time = ttk.Frame(frm_trim, style = "Page.Sub.TFrame")
        frm_trim_time.grid(row = 4, column = 1, sticky = "w")
        frm_trim_time.columnconfigure(0, pad = 2.5)
        frm_trim_time.rowconfigure((0, 1), pad = 2.5)

        lbl_from_time = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_from_time["text"] = "From:"
        lbl_from_time["state"] = "disabled"
        lbl_from_time.grid(row = 0, column = 0, sticky = "e")

        self.vars["trim_from_time_h"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_from_time_h"], 3)

        txt_from_time_h = ttk.Entry(frm_trim_time)
        txt_from_time_h["width"] = 3
        txt_from_time_h["textvariable"] = self.vars["trim_from_time_h"]
        txt_from_time_h["state"] = "disabled"
        txt_from_time_h.grid(row = 0, column = 1)

        lbl_sep_from_h_m = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_sep_from_h_m["text"] = ":"
        lbl_sep_from_h_m["state"] = "disabled"
        lbl_sep_from_h_m.grid(row = 0, column = 2)

        self.vars["trim_from_time_m"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_from_time_m"], 2)

        txt_from_time_m = ttk.Entry(frm_trim_time)
        txt_from_time_m["width"] = 2
        txt_from_time_m["textvariable"] = self.vars["trim_from_time_m"]
        txt_from_time_m["state"] = "disabled"
        txt_from_time_m.grid(row = 0, column = 3)

        lbl_sep_from_m_s = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_sep_from_m_s["text"] = ":"
        lbl_sep_from_m_s["state"] = "disabled"
        lbl_sep_from_m_s.grid(row = 0, column = 4)

        self.vars["trim_from_time_s"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_from_time_s"], 2)

        txt_from_time_s = ttk.Entry(frm_trim_time)
        txt_from_time_s["width"] = 2
        txt_from_time_s["textvariable"] = self.vars["trim_from_time_s"]
        txt_from_time_s["state"] = "disabled"
        txt_from_time_s.grid(row = 0, column = 5)

        lbl_sep_from_s_ms = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_sep_from_s_ms["text"] = "."
        lbl_sep_from_s_ms["state"] = "disabled"
        lbl_sep_from_s_ms.grid(row = 0, column = 6)

        self.vars["trim_from_time_ms"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_from_time_ms"], 3)

        txt_from_time_ms = ttk.Entry(frm_trim_time)
        txt_from_time_ms["width"] = 3
        txt_from_time_ms["textvariable"] = self.vars["trim_from_time_ms"]
        txt_from_time_ms["state"] = "disabled"
        txt_from_time_ms.grid(row = 0, column = 7)

        lbl_to_time = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_to_time["text"] = "To:"
        lbl_to_time["state"] = "disabled"
        lbl_to_time.grid(row = 1, column = 0, sticky = "e")

        self.vars["trim_to_time_h"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_to_time_h"], 3)

        txt_to_time_h = ttk.Entry(frm_trim_time)
        txt_to_time_h["width"] = 3
        txt_to_time_h["textvariable"] = self.vars["trim_to_time_h"]
        txt_to_time_h["state"] = "disabled"
        txt_to_time_h.grid(row = 1, column = 1)

        lbl_sep_to_h_m = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_sep_to_h_m["text"] = ":"
        lbl_sep_to_h_m["state"] = "disabled"
        lbl_sep_to_h_m.grid(row = 1, column = 2)

        self.vars["trim_to_time_m"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_to_time_m"], 2)

        txt_to_time_m = ttk.Entry(frm_trim_time)
        txt_to_time_m["width"] = 2
        txt_to_time_m["textvariable"] = self.vars["trim_to_time_m"]
        txt_to_time_m["state"] = "disabled"
        txt_to_time_m.grid(row = 1, column = 3)

        lbl_sep_to_m_s = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_sep_to_m_s["text"] = ":"
        lbl_sep_to_m_s["state"] = "disabled"
        lbl_sep_to_m_s.grid(row = 1, column = 4)

        self.vars["trim_to_time_s"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_to_time_s"], 2)

        txt_to_time_s = ttk.Entry(frm_trim_time)
        txt_to_time_s["width"] = 2
        txt_to_time_s["textvariable"] = self.vars["trim_to_time_s"]
        txt_to_time_s["state"] = "disabled"
        txt_to_time_s.grid(row = 1, column = 5)

        lbl_sep_to_s_ms = ttk.Label(frm_trim_time, style = "Page.TLabel")
        lbl_sep_to_s_ms["text"] = "."
        lbl_sep_to_s_ms["state"] = "disabled"
        lbl_sep_to_s_ms.grid(row = 1, column = 6)

        self.vars["trim_to_time_ms"] = tk.StringVar(frm_trim_time)
        limit_textvar_numeric_length(self.vars["trim_to_time_ms"], 3)

        txt_to_time_ms = ttk.Entry(frm_trim_time)
        txt_to_time_ms["width"] = 3
        txt_to_time_ms["textvariable"] = self.vars["trim_to_time_ms"]
        txt_to_time_ms["state"] = "disabled"
        txt_to_time_ms.grid(row = 1, column = 7)

        def trim_option_line_enable_fn(enable: bool = True) -> None:
            state: str = "normal" if enable else "disabled"
            lbl_from_line["state"] = state
            txt_from_line["state"] = state
            lbl_to_line["state"] = state
            txt_to_line["state"] = state

        def trim_option_time_enable_fn(enable: bool = True) -> None:
            state: str = "normal" if enable else "disabled"
            lbl_from_time["state"] = state
            txt_from_time_h["state"] = state
            lbl_sep_from_h_m["state"] = state
            txt_from_time_m["state"] = state
            lbl_sep_from_m_s["state"] = state
            txt_from_time_s["state"] = state
            lbl_sep_from_s_ms["state"] = state
            txt_from_time_ms["state"] = state
            lbl_to_time["state"] = state
            txt_to_time_h["state"] = state
            lbl_sep_to_h_m["state"] = state
            txt_to_time_m["state"] = state
            lbl_sep_to_m_s["state"] = state
            txt_to_time_s["state"] = state
            lbl_sep_to_s_ms["state"] = state
            txt_to_time_ms["state"] = state

        def on_trim_option_none() -> None:
            trim_option_line_enable_fn(False)
            trim_option_time_enable_fn(False)

        def on_trim_option_line() -> None:
            trim_option_line_enable_fn(True)
            trim_option_time_enable_fn(False)

        def on_trim_option_time() -> None:
            trim_option_line_enable_fn(False)
            trim_option_time_enable_fn(True)

        rb_trim_option_none["command"] = on_trim_option_none
        rb_trim_option_line["command"] = on_trim_option_line
        rb_trim_option_time["command"] = on_trim_option_time

        def reset_trim_frame_fn() -> None:
            lbl_trim["state"] = "normal"
            self.vars["trim_option"].set("none")
            rb_trim_option_none["state"] = "normal"
            rb_trim_option_line["state"] = "normal"
            rb_trim_option_time["state"] = "normal"

            trim_option_line_enable_fn(False)
            trim_option_time_enable_fn(False)

        self.trim_option_line_enable_fn = trim_option_line_enable_fn
        self.trim_option_time_enable_fn = trim_option_time_enable_fn
        self.reset_trim_frame_fn = reset_trim_frame_fn

    def init_output_frame(self, parent: ttk.Frame) -> None:
        '''Initialise frame for exporting'''
        frm_output = ttk.Frame(parent, style = "Page.Sub.TFrame")
        frm_output.pack(fill = "x", padx = 2.5, pady = 2.5)

        frm_output_inner = ttk.Frame(frm_output, style = "Page.Sub.TFrame")
        frm_output_inner.pack(side = "right")

        btn_save_to_file = ttk.Button(frm_output_inner)
        btn_save_to_file["text"] = "Save To..."
        btn_save_to_file["state"] = "disabled"
        btn_save_to_file["command"] = self.on_save_to
        btn_save_to_file.pack(side = "left", anchor = "w")

        btn_overwrite = ttk.Button(frm_output_inner)
        btn_overwrite["text"] = "Overwrite"
        btn_overwrite["state"] = "disabled"
        btn_overwrite["command"] = self.on_overwrite
        btn_overwrite.pack(side = "left", anchor = "w")

        def reset_output_frame_fn() -> None:
            btn_save_to_file["state"] = "normal"
            btn_overwrite["state"] = "normal"

        self.reset_output_frame_fn = reset_output_frame_fn

    def override_global_logger(self) -> None:
        '''Override global logger to redirect notifications to GUI'''
        # very crude hack into the logger system
        self.info_buffer: list[str] = []
        self.warn_buffer: list[str] = []
        self.error_buffer: list[str] = []

        def info_fn(output: str) -> None:
            output = output.strip("\t\n")
            if output != "":
                self.info_buffer.append(output)

        def warn_fn(output: str) -> None:
            output = output.strip("\t\n")
            if output != "":
                self.warn_buffer.append(output)

        def error_fn(output: str) -> None:
            output = output.strip("\t\n")
            if output != "":
                self.error_buffer.append(output)

        log = Logger(
                LogFunction(lambda _: None),
                LogFunction(lambda _: None),
                LogFunction(info_fn),
                LogFunction(warn_fn),
                LogFunction(error_fn))

        set_global_logger(log)

    def post_command_buffers(self,
                             defer_msg: bool = False
                             ) -> tuple[list[str], list[str], list[str]]:
        '''Yield copies of command buffers and reset internal buffers

        If defer_msg is specified then warnings and errors are not reported'''
        info_buffer = self.info_buffer.copy()
        warn_buffer = self.warn_buffer.copy()
        error_buffer = self.error_buffer.copy()

        self.info_buffer.clear()
        self.warn_buffer.clear()
        self.error_buffer.clear()

        if not defer_msg and len(warn_buffer) != 0:
            msg.showwarning("Warning", "\n".join(warn_buffer))

        if not defer_msg and len(error_buffer) != 0:
            msg.showerror("Error", "\n".join(error_buffer))

        return info_buffer, warn_buffer, error_buffer

    def reset_delay_frame(self) -> None:
        '''Enable the widgets in the delay frame for editing'''
        self.reset_delay_frame_fn()

    def reset_info_frame(self) -> None:
        '''Enable the widgets in the info frame for viewing'''
        self.reset_info_frame_fn()

    def reset_trim_frame(self) -> None:
        '''Enable the widgets in the trim frame for editing'''
        self.reset_trim_frame_fn()

    def reset_frames(self) -> None:
        '''Enable widget groups'''
        self.reset_delay_frame()
        self.reset_info_frame()
        self.reset_trim_frame()
        self.reset_output_frame()

    def get_filetypes(self) -> list[tuple[str, tuple[str, ...]]]:
        '''Return filetypes for filedialogs'''
        return [(key, value)
                for key, value in self.filetypes_dict.items() ]

    def on_open_file(self) -> None:
        '''Event handler for opening a file'''
        filename = fd.askopenfilename(
                title = "Open a subtitle file",
                filetypes = self.get_filetypes())

        if filename == "":
            return

        display_command = self.commands["display"].function
        command_args = {
                "dbg1": False,
                "input": (filename,),
                "use_ranges": False,
                "encoding": "utf-8"
                }
        common.parse_many_promised_fileranges(command_args)
        display_command(command_args)
        info_buf, _, _ = self.post_command_buffers()
        self.set_display_output(info_buf)
        self.reset_frames()
        self.vars["input"].set(filename)

        self.root.title(f"subby - {filename}")

        # TODO add linklabel to fix issues with file

        line_count: int = -1
        for line in info_buf:
            info_split = line.split(" ")
            if info_split[2] == "lines":
                line_count = int(info_split[1])
                break

        self.set_trim_line_bounds(line_count)
        self.vars["trim_from_line"].set(str(0))
        self.vars["trim_to_line"].set(str(line_count))

    def on_overwrite(self) -> None:
        '''Event handler for overwriting to the current file'''
        output: str = self.vars["input"].get()
        if output == "":
            return

        do_continue = msg.askyesno(
                "subby",
                f"This action will overwrite {output}. Are you sure"\
                        " you want to continue?")

        if not do_continue:
            return

        self.export(output)

    def on_save_to(self) -> None:
        '''Event handler for saving to a subtitle file'''
        type_var = tk.StringVar()
        output: str = fd.asksaveasfilename(
                title = "Save As",
                confirmoverwrite = True,
                filetypes = self.get_filetypes(),
                typevariable = type_var)
        if output == "":
            return

        extension: str = self.filetypes_dict[type_var.get()][0].strip("*")
        output = output + extension
        self.export(output)

    def export(self, output_filename: str) -> None:
        '''Export subtitles to the output filename'''
        jobs: list[Job] = []
        jobs.append(lambda: self.delay_current_file(output_filename))

        if self.vars["trim_option"].get() == "none":
            self.append_display_output([f"Exporting whole file"])
        else:
            jobs.append(lambda: info("Trim not implemented"))

        for job in jobs:
            job()

        information, _, errors = self.post_command_buffers()
        self.append_display_output(information)
        if len(errors) != 0:
            self.append_display_output(["File could not be saved"])
        else:
            self.append_display_output(["Finished!"])

    def delay_current_file(self, output_filename: str) -> None:
        '''Delay the current file, saving result to output'''
        delay_str: str = self.vars["delay"].get()
        delay: int
        if delay_str == "":
            delay = 0
        else:
            delay = int(delay_str)

        filename: str = self.vars["input"].get()

        # there is technically a bug in delay.py: the unit parameter should be
        # set to "ms" by default, but erroneously is set to None. If the
        # program explicitly checked if this parameter was milliseconds, then
        # this would have been caught, but the program only checks if the unit
        # has been set to something other than milliseconds

        delay_command = self.commands["delay"].function
        command_args = {
                "output": output_filename,
                "overwrite": False,
                "confirm": True,
                "unit": None, # TODO see above
                "exclusive": False,
                "input": filename,
                "use_ranges": False,
                "encoding": "utf-8",
                "delay": delay
                }
        common.parse_promised_filerange(command_args)
        delay_command(command_args)

    def on_gui_prompt(self, title: str, msg_: str) -> bool:
        return msg.askyesno(title, msg_)

    def set_display_output(self, output: list[str]) -> None:
        '''Clear and set the info display'''
        text: str = "\n".join((
            line
            if len(line) <= MAX_DISPLAY_WIDTH
            else line[:MAX_DISPLAY_WIDTH - 2] + "..."
            for line in output
            ))
        self.vars["info"].set(text)

    def append_display_output(self, output: list[str]) -> None:
        '''Append to the end of the info display'''
        new_text: str = "\n".join((
            line
            if len(line) <= MAX_DISPLAY_WIDTH
            else line[:MAX_DISPLAY_WIDTH - 2] + "..."
            for line in output
            ))
        old_text: str = self.vars["info"].get()
        self.vars["info"].set(old_text + "\n" + new_text)

    def set_trim_line_bounds(self, line_count: int) -> None:
        '''Set the limits for the trim lines entries'''
        def numeric_value(var: tk.StringVar) -> int:
            value: str = ''.join(filter(lambda c: c.isnumeric(), var.get()))
            if value == '':
                return 0
            else:
                return int(value)

        def from_line_limit_tracer(*_):
            from_value = numeric_value(self.vars["trim_from_line"])
            if from_value > line_count:
                from_value = line_count
            self.vars["trim_from_line"].set(str(from_value))

        def to_line_limit_tracer(*_):
            to_value = numeric_value(self.vars["trim_to_line"])
            if to_value > line_count:
                to_value = line_count
            self.vars["trim_to_line"].set(str(to_value))

        self.vars["trim_from_line"].trace_add("write", from_line_limit_tracer)
        self.vars["trim_to_line"].trace_add("write", to_line_limit_tracer)

    def increment_delay(self, amount: int) -> None:
        '''Increment delay by an amount of milliseconds'''
        delay_str: str = self.vars["delay"].get()
        delay: int = int(delay_str) if delay_str != "" else 0
        delay = delay + amount
        self.vars["delay"].set(str(delay))

    def reset_output_frame(self) -> None:
        '''Enable the widgets in the output frame'''
        self.reset_output_frame_fn()

    def get_program_name(self) -> str:
        '''Return program name from program arguments'''
        return self.prog_args.get("prog", "")

    def get_program_version(self) -> str:
        '''Return program version from program arguments'''
        return self.prog_args.get("version", "")

    def start(self) -> None:
        '''Begin interactive mode'''
        self.root.mainloop()

