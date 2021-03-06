import os
from gi.repository import Gtk, GLib, GdkPixbuf, Gio

from .helpers import (
    convert_theme_color_to_gdk,
    THEME_KEYS, script_dir
)


class ThemePreview(Gtk.Grid):

    BG = 'bg'
    FG = 'fg'

    def override_color(self, widget, value, color, state=Gtk.StateType.NORMAL):
        if value == self.BG:
            return widget.override_background_color(state, color)
        elif value == self.FG:
            return widget.override_color(state, color)

    def update_preview_colors(self, colorscheme):
        converted = {
            obj['key']: convert_theme_color_to_gdk(colorscheme[obj['key']])
            for obj in THEME_KEYS if obj['type'] == 'color'
        }
        self.override_color(self.bg, self.BG, converted["BG"])
        self.override_color(self.label, self.FG, converted["FG"])
        self.override_color(self.sel_label, self.FG, converted["SEL_FG"])
        self.override_color(self.sel_label, self.BG, converted["SEL_BG"])
        self.override_color(self.entry, self.FG, converted["TXT_FG"])
        self.override_color(self.entry, self.BG, converted["TXT_BG"])
        self.override_color(self.entry, self.FG, converted["SEL_FG"],
                            state=Gtk.StateFlags.SELECTED)
        self.override_color(self.entry, self.BG, converted["SEL_BG"],
                            state=Gtk.StateFlags.SELECTED)
        self.override_color(self.button, self.FG, converted["BTN_FG"])
        self.override_color(self.button, self.BG, converted["BTN_BG"])
        self.override_color(self.menuitem1, self.FG, converted["MENU_FG"])
        self.override_color(self.menuitem2, self.FG, converted["MENU_FG"])
        self.override_color(self.menubar, self.BG, converted["MENU_BG"])
        self.override_color(self.headerbar, self.BG, converted["MENU_BG"])
        self.override_color(self.headerbar, self.FG, converted["MENU_FG"])
        self.override_color(self.headerbar_button, self.FG,
                            converted["HDR_BTN_FG"])
        self.override_color(self.headerbar_button, self.BG,
                            converted["HDR_BTN_BG"])
        self.override_color(self.icon_preview_listbox, self.BG,
                            converted["TXT_BG"])

        gradient = colorscheme['GRADIENT']
        for widget, color in zip(
            [self.button, self.headerbar_button, self.entry],
            [
                colorscheme["BTN_BG"],
                colorscheme["HDR_BTN_BG"],
                colorscheme["TXT_BG"]
            ]
        ):
            css_provider_gradient = Gtk.CssProvider()
            css_provider_gradient.load_from_data((
                gradient > 0 and """
                * {{
                    background-image: linear-gradient(to bottom,
                        shade(#{color}, {amount1}),
                        shade(#{color}, {amount2})
                    );
                }}
                """.format(
                    color=color,
                    amount1=1 - gradient / 2,
                    amount2=1 + gradient * 2
                ) or """
                * {
                    background-image: none;
                }
                """
            ).encode('ascii'))
            Gtk.StyleContext.add_provider(
                widget.get_style_context(),
                css_provider_gradient,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        css_provider_roundness = Gtk.CssProvider()
        css_provider_roundness.load_from_data("""
            * {{
                border-radius: {roundness}px;
            }}
        """.format(roundness=colorscheme['ROUNDNESS']).encode('ascii'))
        for widget in [self.button, self.headerbar_button, self.entry]:
            Gtk.StyleContext.add_provider(
                widget.get_style_context(),
                css_provider_roundness,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

        for source_image, target_imagebox in (
            (self.icon_source_user_home, self.icon_user_home),
            (self.icon_source_user_desktop, self.icon_user_desktop),
            (self.icon_source_system_file_manager,
             self.icon_system_file_manager),
        ):
            new_svg_image = source_image.replace(
                "LightFolderBase", colorscheme["ICONS_LIGHT_FOLDER"]
            ).replace(
                "LightBase", colorscheme["ICONS_LIGHT"]
            ).replace(
                "MediumBase", colorscheme["ICONS_MEDIUM"]
            ).replace(
                "DarkStroke", colorscheme["ICONS_DARK"]
            ).encode('ascii')
            stream = Gio.MemoryInputStream.new_from_bytes(
                GLib.Bytes.new(new_svg_image)
            )

            # @TODO: is it possible to make it faster?
            pixbuf = GdkPixbuf.Pixbuf.new_from_stream(stream, None)

            target_imagebox.set_from_pixbuf(pixbuf)

    def __init__(self):
        super().__init__(row_spacing=6, column_spacing=6)

        self._init_icon_templates()
        self._init_widgets()
        self._override_css_style()

    def _init_icon_templates(self):
        for template_path, attr_name in (
            ("user-home.svg.template", "icon_source_user_home"),
            ("user-desktop.svg.template", "icon_source_user_desktop"),
            ("system-file-manager.svg.template",
             "icon_source_system_file_manager"),
        ):
            with open(
                os.path.join(script_dir, template_path), "rb"
            ) as f:
                setattr(self, attr_name, f.read().decode('utf-8'))

    def _init_widgets(self):
        preview_label = Gtk.Label("Preview:")
        self.bg = Gtk.Grid(row_spacing=6, column_spacing=6)
        self.attach(preview_label, 1, 1, 3, 1)
        self.attach_next_to(self.bg, preview_label,
                            Gtk.PositionType.BOTTOM, 1, 1)

        self.headerbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.headerbar = Gtk.HeaderBar()
        self.headerbar.set_show_close_button(True)
        self.headerbar.props.title = "Headerbar"
        self.headerbar_button = Gtk.Button(label="   Button   ")
        self.headerbar.pack_end(self.headerbar_button)

        self.menubar = Gtk.MenuBar()
        self.menuitem1 = Gtk.MenuItem(label='File')
        # menuitem.set_submenu(self.create_menu(3, True))
        self.menubar.append(self.menuitem1)
        self.menuitem2 = Gtk.MenuItem(label='Edit')
        # menuitem.set_submenu(self.create_menu(4, True))
        self.menubar.append(self.menuitem2)

        self.headerbox.pack_start(self.headerbar, True, True, 0)
        self.headerbox.pack_start(self.menubar, True, True, 0)

        self.label = Gtk.Label("This is a label.")
        self.sel_label = Gtk.Label("Selected item.")
        self.entry = Gtk.Entry(text="Text entry.")

        self.button = Gtk.Button(label="Click-click")

        self.icon_preview_listbox = Gtk.ListBox()
        self.icon_preview_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        row.add(hbox)
        for attr_name in (
            "icon_user_home",
            "icon_user_desktop",
            "icon_system_file_manager"
        ):
            setattr(self, attr_name, Gtk.Image())
            hbox.pack_start(getattr(self, attr_name), True, True, 0)
        self.icon_preview_listbox.add(row)
        self.icon_preview_listbox.show_all()

        self.bg.attach(self.headerbox, 1, 1, 5, 2)
        self.bg.attach(self.label, 3, 3, 1, 1)
        self.bg.attach_next_to(self.sel_label, self.label,
                               Gtk.PositionType.BOTTOM, 1, 1)
        self.bg.attach_next_to(self.entry, self.sel_label,
                               Gtk.PositionType.BOTTOM, 1, 1)
        self.bg.attach_next_to(self.button, self.entry,
                               Gtk.PositionType.BOTTOM, 1, 1)
        # hack to have margin inside children box instead of the parent one:
        self.bottom_margin = Gtk.Label()
        self.bg.attach_next_to(self.bottom_margin, self.button,
                               Gtk.PositionType.BOTTOM, 1, 1)
        self.bg.attach_next_to(self.icon_preview_listbox, self.bottom_margin,
                               Gtk.PositionType.BOTTOM, 1, 1)
        self.bottom_margin2 = Gtk.Label()
        self.bg.attach_next_to(self.bottom_margin2, self.icon_preview_listbox,
                               Gtk.PositionType.BOTTOM, 1, 1)

    def _override_css_style(self):
        css_provider = Gtk.CssProvider()
        try:
            if Gtk.get_minor_version() >= 20:
                css_provider.load_from_path(
                    os.path.join(script_dir, "theme20.css")
                )
            else:
                css_provider.load_from_path(
                    os.path.join(script_dir, "theme.css")
                )
        except GLib.Error as e:
            print(e)

        for widget in [
            self,
            self.label,
            self.sel_label,
            self.entry,
            self.button,
            self.menuitem1,
            self.menuitem2,
            self.menubar,
            self.headerbar,
            self.headerbar_button
        ]:
            Gtk.StyleContext.add_provider(
                widget.get_style_context(),
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
