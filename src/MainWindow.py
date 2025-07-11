#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import locale
from locale import gettext as _

from pardus_domain_core import domain_operations
import managers.ConfigManager as ConfigManager

import subprocess
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

CWD = os.path.dirname(os.path.abspath(__file__))


class Model:
    domain = ""
    computer_name = ""
    username = ""
    password = ""
    organizational_unit = ""
    connection_type = "sssd"
    hostname = ""


class MainWindow:
    def __init__(self, application):
        self.application = application

        self.setup_ui_builder()

        self.setup_window()

        self.setup_css()

        self.setup_widgets()

        self.setup_variables()

        self.setup_about_dialog()

        self.check_domain_already_joined()

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
        self.winbind_radio = UI("winbind_radio")

        self.ou_default_radio = UI("ou_default_radio")
        self.ou_path_radio = UI("ou_path_radio")
        self.ou_path_entry = UI("ou_path_entry")

        # Prejoin Page
        self.domain_prejoin_label = UI("domain_prejoin_label")
        self.username_prejoin_label = UI("username_prejoin_label")
        self.hostname_prejoin_label = UI("hostname_prejoin_label")
        self.service_prejoin_label = UI("service_prejoin_label")
        self.ou_prejoin_label = UI("ou_prejoin_label")

        # Joining Page
        self.joining_viewport = UI("joining_viewport")
        self.joining_log_label = UI("joining_log_label")
        self.joining_spinner = UI("joining_spinner")
        self.joining_title_label = UI("joining_title_label")
        self.cancel_btn_stack = UI("cancel_btn_stack")

        # Joined Page
        self.joined_domain_label = UI("joined_domain_label")

    def setup_variables(self):
        config = ConfigManager.read_config()

        self.model = Model()
        self.model.username = config["username"]
        self.model.domain = config["domain"]
        self.model.connection_type = config["connection_type"]
        self.model.organizational_unit = config["organizational_unit"]
        self.model.hostname = os.uname()[1]

        # Main Page
        self.domain_entry.set_text(self.model.domain)
        self.username_entry.set_text(self.model.username)

        # Advanced Settings Page
        self.hostname_entry.set_text(self.model.hostname)
        self.sssd_radio.set_active(self.model.connection_type == "sssd")
        self.winbind_radio.set_active(self.model.connection_type == "winbind")
        self.ou_default_radio.set_active(self.model.organizational_unit == "")
        self.ou_path_radio.set_active(self.model.organizational_unit != "")

        self.joining_process_pid = None

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
    def check_domain_already_joined(self):
        # Go to directly joined page if already joined
        self.stderr_text = ""
        self.stdout_text = ""

        def on_stdout(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            print("stdout", line)
            if line:
                self.stdout_text += line

            return True

        def on_stderr(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            print("stderr", line)
            if line:
                self.stderr_text += line + "\n"

            return True

        def on_exit(pid, status):
            if status == 0:
                domain = self.stdout_text.strip()
                print(f"joined domain name: '{domain}'")

                if domain:
                    self.joined_domain_label.set_text(domain)
                    self.main_stack.set_visible_child_name("in_domain")
                else:
                    self.main_stack.set_visible_child_name("main")

            else:
                print(self.stderr_text)

                self.application.quit()

        self.spawn_process(
            ["pkexec", f"{CWD}/Actions.py", "check_domain"],
            on_stdout,
            on_stderr,
            on_exit,
        )

    def check_credentials(self):
        is_valid = (
            len(self.username_entry.get_text()) != 0
            and len(self.password_entry.get_text()) != 0
            and len(self.domain_entry.get_text()) != 0
        )

        self.prejoin_btn.set_sensitive(is_valid)

    def save_config(self):
        config = vars(self.model).copy()

        config.pop("password", None)
        config.pop("hostname", None)
        config.pop("computer_name", None)

        ConfigManager.save_config(config)

    def spawn_process(self, params, on_stdout, on_stderr, on_exit):
        pid, _stdin, stdout, stderr = GLib.spawn_async(
            params,
            flags=GLib.SPAWN_SEARCH_PATH
            | GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN
            | GLib.SPAWN_DO_NOT_REAP_CHILD,
            standard_input=False,
            standard_output=True,
            standard_error=True,
        )

        if on_stdout:
            GLib.io_add_watch(
                GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, on_stdout
            )

        if on_stderr:
            GLib.io_add_watch(
                GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, on_stderr
            )

        GLib.child_watch_add(GLib.PRIORITY_DEFAULT, pid, on_exit)

        return pid

    # === CALLBACKS ===
    def on_destroy(self, win):
        win.get_application().quit()

    def on_about_btn_clicked(self, btn):
        self.about_dialog.run()
        self.about_dialog.hide()

    # Main Page
    def on_prejoin_btn_clicked(self, _):
        self.model.domain = self.domain_entry.get_text()
        self.model.username = self.username_entry.get_text()
        self.model.password = self.password_entry.get_text()

        self.domain_prejoin_label.set_text(self.model.domain)
        self.username_prejoin_label.set_text(self.model.username)
        self.hostname_prejoin_label.set_text(self.model.hostname)
        self.service_prejoin_label.set_text(self.model.connection_type)
        self.ou_prejoin_label.set_text(
            "-"
            if not self.model.organizational_unit
            else self.model.organizational_unit
        )

        self.main_stack.set_visible_child_name("prejoin")

    def on_advanced_settings_btn_clicked(self, btn):
        self.main_stack.set_visible_child_name("advanced_settings")

    def on_back_to_main_btn_clicked(self, btn):
        self.main_stack.set_visible_child_name("main")

    def on_save_btn_clicked(self, btn):
        # Update model
        self.model.organizational_unit = (
            self.ou_path_entry.get_text() if self.ou_path_radio.get_active() else ""
        )

        self.model.connection_type = (
            "sssd" if self.sssd_radio.get_active() else "winbind"
        )

        self.save_config()

        self.main_stack.set_visible_child_name("main")

    def on_password_entry_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(1, "view-reveal-symbolic")

    def on_password_entry_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(1, "view-conceal-symbolic")

    def on_password_entry_activate(self, entry):
        self.on_prejoin_btn_clicked(None)

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
        if response == Gtk.ResponseType.OK:
            self.stderr_text = ""

            def on_stderr(source, condition):
                if condition == GLib.IO_HUP:
                    return False

                line = source.readline().strip()
                if line:
                    self.stderr_text += line + "\n"

                return True

            def on_exit(pid, status):
                print(self.stderr_text)
                if status == 0:
                    self.model.hostname = new_hostname
                elif status == 126:
                    pass
                else:
                    dialog = Gtk.MessageDialog(
                        buttons=Gtk.ButtonsType.OK,
                        text=_("Couldn't change hostname"),
                        secondary_text=self.stderr_text,
                    )
                    dialog.run()
                    dialog.hide()

            self.spawn_process(
                ["pkexec", f"{CWD}/Actions.py", "hostname", new_hostname],
                None,
                on_stderr,
                on_exit,
            )

        dialog.hide()

    def on_ou_path_radio_toggled(self, btn):
        self.ou_path_entry.set_sensitive(btn.get_active())

    # Pre Join
    def on_join_btn_clicked(self, btn):
        # Clear UI
        self.joining_spinner.start()
        self.joining_title_label.set_text(_("Joining to the domain..."))
        self.joining_log_label.set_text("")
        self.cancel_btn_stack.set_visible_child_name("cancel")

        self.main_stack.set_visible_child_name("joining")

        def on_stdout(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            if line == "":
                return True

            lbl = self.joining_log_label
            lbl.set_markup(lbl.get_label() + line + "\n")

            adj = self.joining_viewport.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

            return True

        def on_stderr(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            if line == "":
                return True

            lbl = self.joining_log_label
            lbl.set_markup(lbl.get_label() + f'<span color="red">{line}</span>' + "\n")

            adj = self.joining_viewport.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

            return True

        def on_exit(pid, status):
            self.joining_process_pid = None

            if status != 0:
                lbl = self.joining_log_label
                lbl.set_markup(
                    lbl.get_label() + _("Process exit code:{}").format(status)
                )

            adj = self.joining_viewport.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

            if status == 0:
                self.main_stack.set_visible_child_name("in_domain")
                self.joined_domain_label.set_text(self.model.domain)

                self.save_config()
            elif status == 15 or status == 32256 or status == 32512 or status == 126:
                # Cancelled pkexec dialog
                self.main_stack.set_visible_child_name("prejoin")
            else:
                self.joining_title_label.set_text(_("An error occured while joining."))
                self.joining_spinner.stop()
                self.cancel_btn_stack.set_visible_child_name("back")

        self.joining_process_pid = self.spawn_process(
            [
                "pkexec",
                f"{CWD}/Actions.py",
                "join",
                self.model.hostname,
                self.model.domain,
                self.model.username,
                self.model.password,
                self.model.organizational_unit,
                self.model.connection_type,
            ],
            on_stdout,
            on_stderr,
            on_exit,
        )

    # Joining Page
    def on_cancel_joining_btn_clicked(self, btn):
        if not self.joining_process_pid:
            return

        dialog = Gtk.MessageDialog(
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=_("Are you sure?"),
            secondary_text=_("Do you want to cancel the joining process?"),
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            subprocess.run(
                ["pkexec", f"{CWD}/Actions.py", "cancel", str(self.joining_process_pid)]
            )

        dialog.hide()

    # In Domain page
    def on_leave_domain_btn_clicked(self, btn):
        self.stderr_text = ""

        def on_stderr(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            print("stderr", line)
            if line:
                self.stderr_text += line + "\n"

            return True

        def on_exit(pid, status):
            if status == 0:
                self.main_stack.set_visible_child_name("main")

            else:
                dialog = Gtk.MessageDialog(
                    buttons=Gtk.ButtonsType.OK,
                    text=_("An error occured on leaving the domain."),
                    secondary_text=self.stderr_text,
                )
                dialog.run()
                dialog.hide()

        self.spawn_process(
            ["pkexec", f"{CWD}/Actions.py", "leave"],
            None,
            on_stderr,
            on_exit,
        )
