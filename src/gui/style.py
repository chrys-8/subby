from tkinter import ttk

# this file was grabbed from another UI project I worked on while training

var = {
        "background": "white",
        "foreground": "#c21b1b",
        "text_normal": 9,
        "text_bigger": 20,
        "text_big": 16
        }

style = {
        "Page.TFrame": {
            "relief": "solid",
            "background": var["background"]
            },
        "Page.TLabel": {
            "background": var["background"]
            },
        "Page.TRadiobutton": {
            "background": var["background"]
            },
        "Page.Link.TLabel": {
            "background": var["background"],
            "font": "-size {} -underline 1".format(var["text_normal"])
            },
        "Page.Link.Active.TLabel": {
            "background": var["background"],
            "font": "-size {} -underline 1".format(var["text_normal"]),
            "foreground": "blue"
            },
        "Page.DeleteLink.TLabel": {
            "background": var["background"],
            "font": "-size {} -underline 1".format(var["text_normal"]),
            "foreground": "red"
            },
        "Page.DeleteLink.Active.TLabel": {
            "background": var["background"],
            "font": "-size {} -underline 1".format(var["text_normal"]),
            "foreground": "black"
            },
        "Page.Heading.TLabel": {
            "font": "Segeo-UI, {}".format(var["text_big"]),
            "background": var["background"]
            },
        "Heading.TLabel": {
            "font": "Segeo-UI, {}".format(var["text_bigger"])
            },
        "Navbar.TFrame": {
            "background": var["background"]
            },
        "Navbar.TLabel": {
            "background": var["background"]
            },
        "Page.Sub.TFrame": {
            "background": var["background"]
            },
        "Page.Sub.TLabel": {
            "background": var["background"]
            },
        "Page.Sub.Link.TLabel": {
            "background": var["background"],
            "font": "-size {} -underline 1".format(var["text_normal"])
            },
        "Page.Sub.Link.Active.TLabel": {
            "background": var["background"],
            "font": "-size {} -underline 1".format(var["text_normal"]),
            "foreground": "blue"
            },
        "Page.Sub.Selected.Link.TLabel" : {
            "background": var["background"],
            "font": "-size {} -weight bold".format(var["text_normal"])
            },
        "Page.Sub.Selected.Link.Active.TLabel" : {
            "background": var["background"],
            "font": "-size {} -weight bold".format(var["text_normal"]),
            "foreground": "blue"
            },
        "Page.Heading.Accent.TLabel": {
            "font": "Segeo-UI, {}".format(var["text_big"]),
            "background": var["background"],
            "foreground": var["foreground"]
            }
        }

def init_styles() -> None:
    """Initialise Ttk style database"""
    style_db = ttk.Style()
    for style_name in style.keys():
        style_db.configure(style_name, **style[style_name])
