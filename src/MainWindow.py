#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import subprocess
import locale
from locale import gettext as _

import re
import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import GLib, Gtk, Gdk

# from domain_joiner_ldap import LDAP

# Translation Constants:
APPNAME = "pardus-domain-joiner"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)


class Model:
    def __init__(self):
        self.domain = ""
        self.computer_name = ""
        self.username = ""
        self.password = ""
        self.organizational_unit = ""
        self.connection_type = "sssd"


class MainWindow:
    def __init__(self, application):
        self.application = application

        self.setup_ui_builder()

        self.setup_window()

        self.setup_css()

        self.setup_widgets()

        self.setup_variables()

        self.setup_about_dialog()

        # self.check_realm_list()

    # == SETUPS ==
    def setup_ui_builder(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APPNAME)
        self.builder.add_from_file(
            os.path.dirname(os.path.abspath(__file__)) + "/../ui/MainWindow.glade"
        )
        self.builder.connect_signals(self)

    def setup_window(self):
        self.window = self.builder.get_object("main_window")
        self.window.set_application(self.application)
        self.window.connect("destroy", self.on_destroy)

    def setup_css(self):
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(
            os.path.dirname(os.path.abspath(__file__)) + "/../data/style.css"
        )
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(
            screen, cssProvider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def setup_widgets(self):
        def UI(a):
            return self.builder.get_object(a)

        self.main_stack = UI("main_stack")

        # Main Page
        self.domain_entry = UI("domain_entry")
        self.username_entry = UI("username_entry")
        self.password_entry = UI("password_entry")
        self.prejoin_btn = UI("prejoin_btn")

        # Advanced Settings Page
        self.hostname_entry = UI("hostname_entry")
        self.change_hostname_btn = UI("change_hostname_btn")

        self.sssd_radio = UI("sssd_radio")

        self.ou_path_radio = UI("ou_path_radio")
        self.ou_path_entry = UI("ou_path_entry")

        # Prejoin Page
        self.domain_prejoin_label = UI("domain_prejoin_label")
        self.username_prejoin_label = UI("username_prejoin_label")
        self.hostname_prejoin_label = UI("hostname_prejoin_label")
        self.service_prejoin_label = UI("service_prejoin_label")
        self.ou_prejoin_label = UI("ou_prejoin_label")

    def setup_variables(self):
        self.model = Model()

        self.model.hostname = os.uname()[1]
        self.hostname_entry.set_text(self.model.hostname)

        # checking for errors when joining the domain
        # self.user_password_check = False
        # self.domain_check = False
        # self.domain_name_check = False
        # self.ou_address_check = False
        # self.join_check = False

    def setup_about_dialog(self):
        self.about_dialog = self.builder.get_object("about_dialog")

        if self.about_dialog.get_titlebar is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("Pardus Domain Joiner"))
            about_headerbar.show_all()
            self.about_dialog.set_titlebar(about_headerbar)

            try:
                version = open(
                    os.path.dirname(os.path.abspath(__file__)) + "/__version__"
                ).readline()
                self.about_dialog.set_version(version)
            except Exception:
                pass

    # == FUNCTIONS ==
    """
    def sanitize_input(self, input_text):
        sanitized_input = re.sub(r"[^a-zA-Z0-9,=]", "", input_text)
        return sanitized_input

    def generate_ouaddress(self, domain):
        ouaddress = ""
        fulldn = ", dc=" + domain.replace(".", ", dc=")
        if self.ou_default_rb.get_active():
            ouaddress = "cn=Computers" + fulldn
        else:
            input_text = self.ou_specific_entry.get_text()
            sanitized_ou = self.sanitize_input(input_text)
            ouaddress = sanitized_ou
            if "dc=" not in ouaddress:
                ouaddress += fulldn

        return ouaddress
    """

    def check_credentials(self):
        is_valid = (
            len(self.username_entry.get_text()) != 0
            and len(self.password_entry.get_text()) != 0
            and len(self.domain_entry.get_text()) != 0
        )

        self.prejoin_btn.set_sensitive(is_valid)

    # === CALLBACKS ===
    def on_destroy(self, win):
        win.get_application().quit()

    def on_about_btn_clicked(self, btn):
        self.about_dialog.run()
        self.about_dialog.hide()

    # Main Page
    def on_prejoin_btn_clicked(self, btn):
        self.model.domain = self.domain_entry.get_text()
        self.model.username = self.username_entry.get_text()
        self.model.password = self.password_entry.get_text()

        self.domain_prejoin_label.set_text(self.model.domain)
        self.username_prejoin_label.set_text(self.model.username)
        self.hostname_prejoin_label.set_text(self.model.hostname)
        self.service_prejoin_label.set_text(self.model.connection_type)
        self.ou_prejoin_label.set_text(self.model.organizational_unit)

        self.main_stack.set_visible_child_name("prejoin")

        print(vars(self.model))

    def on_advanced_settings_btn_clicked(self, btn):
        self.main_stack.set_visible_child_name("advanced_settings")

    def on_back_to_main_btn_clicked(self, btn):
        self.main_stack.set_visible_child_name("main")

    def on_save_btn_clicked(self, btn):
        self.model.organizational_unit = (
            self.ou_path_entry.get_text() if self.ou_path_radio.get_active() else ""
        )

        self.model.connection_type = (
            "sssd" if self.sssd_radio.get_active() else "winbind"
        )

        self.main_stack.set_visible_child_name("main")

        print(vars(self.model))

    def on_password_entry_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(1, "view-reveal-symbolic")

    def on_password_entry_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(1, "view-conceal-symbolic")

    def on_domain_entry_changed(self, entry):
        self.check_credentials()

    def on_username_entry_changed(self, entry):
        self.check_credentials()

    def on_password_entry_changed(self, entry):
        self.check_credentials()

    # Advanced settings
    def on_hostname_entry_changed(self, entry):
        self.change_hostname_btn.set_sensitive(len(entry.get_text()) != 0)

    def on_change_hostname_btn_clicked(self, btn):
        current_hostname = self.model.hostname
        new_hostname = self.hostname_entry.get_text()

        if current_hostname == new_hostname:
            return

        dialog = Gtk.MessageDialog(
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=_("Are you sure?"),
            secondary_text=_("Hostname will be changed.\n\nOld: {}\nNew: {}").format(
                current_hostname, new_hostname
            ),
        )

        response = dialog.run()
        dialog.hide()
        print(response)

    def on_ou_path_radio_toggled(self, btn):
        self.ou_path_entry.set_sensitive(btn.get_active())

    # Pre Join
    def on_join_btn_clicked(self, btn):
        self.main_stack.set_visible_child_name("joining")

    # Joining Page
    def on_cancel_joining_btn_clicked(self, btn):
        print("cancel joining")
