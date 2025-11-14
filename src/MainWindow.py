#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import locale
import ldap
from locale import gettext as _

import Version

from pardus_domain_joiner import domain_operations
from pardus_domain_joiner import domain_joiner_ldap
import managers.ConfigManager as ConfigManager

import subprocess
import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Gdk, Gio

# Translation Constants:
APPNAME = "pardus-domain-joiner"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)

CWD = os.path.dirname(os.path.abspath(__file__))
ACTIONS_PY = f"{CWD}/Actions.py"

HOSTNAME_REGEX = (
    r"""^([a-zA-Z0-9](?:(?:[a-zA-Z0-9-]*|(?<!-)\.(?![-.]))*[a-zA-Z0-9]+)?)$"""
)


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

        # Spinner Page
        self.spinner_label = UI("spinner_label")

        # Main Page
        self.domain_entry = UI("domain_entry")
        self.username_entry = UI("username_entry")
        self.password_entry = UI("password_entry")
        self.prejoin_btn = UI("prejoin_btn")

        # Advanced Settings Page
        self.hostname_entry = UI("hostname_entry")

        self.sssd_radio = UI("sssd_radio")
        self.winbind_radio = UI("winbind_radio")

        self.ou_default_radio = UI("ou_default_radio")
        self.ou_specific_radio = UI("ou_specific_radio")
        self.ou_path_entry = UI("ou_path_entry")

        # Prejoin Page
        self.domain_prejoin_label = UI("domain_prejoin_label")
        self.username_prejoin_label = UI("username_prejoin_label")
        self.hostname_prejoin_label = UI("hostname_prejoin_label")
        self.service_prejoin_label = UI("service_prejoin_label")
        self.ou_prejoin_label = UI("ou_prejoin_label")

        # Joining Page
        self.steps_box = UI("steps_box")
        self.joining_viewport = UI("joining_viewport")
        self.joining_log_label = UI("joining_log_label")
        # self.joining_spinner = UI("joining_spinner")
        self.joining_title_label = UI("joining_title_label")
        self.cancel_btn_stack = UI("cancel_btn_stack")

        # Joined Page
        self.joined_domain_label = UI("joined_domain_label")
        self.joined_btn_stack = UI("joined_btn_stack")

        # AD Password asking dialog
        self.ad_dialog = UI("ad_dialog")
        self.ad_dialog_username_entry = UI("ad_dialog_username_entry")
        self.ad_dialog_password_entry = UI("ad_dialog_password_entry")
        self.ad_dialog_ok_btn = UI("ad_dialog_ok_btn")

        # AD Password asking dialog
        self.input_dialog = UI("input_dialog")
        self.input_dialog_lbl = UI("input_dialog_lbl")
        self.input_dialog_entry = UI("input_dialog_entry")
        self.input_dialog_ok_btn = UI("input_dialog_ok_btn")

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

        self.ou_path_entry.set_text(self.model.organizational_unit)
        self.ou_default_radio.set_active(self.model.organizational_unit == "")
        self.ou_specific_radio.set_active(self.model.organizational_unit != "")

        self.joining_process_pid = None

        # Steps box
        self.last_step_box = None
        self.last_step_spinner = None
        self.last_step_logs = ""
        # Step translations in libpardus:
        _("Starting sssd service...")
        _("Discovering kerberos domain...")
        _("Backup configuration files...")
        _("Joining the domain with sssd...")
        _("Updating configuration files...")
        _("Enabling Pardus PAM Config...")
        _("Success.")
        _("Starting winbind service...")
        _("Discovering the domain...")
        _("Joining the domain with winbind...")
        _("Organizational Unit format check...")

    def setup_about_dialog(self):
        self.about_dialog = self.builder.get_object("about_dialog")
        self.about_dialog.set_version(Version.VERSION)
        if self.about_dialog.get_titlebar is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("Pardus Domain Joiner"))
            about_headerbar.show_all()
            self.about_dialog.set_titlebar(about_headerbar)

    # == FUNCTIONS ==
    def clear_steps_box(self):
        # Clear steps box:
        def rm_box(b):
            self.steps_box.remove(b)

        self.steps_box.foreach(rm_box)

    def add_step_to_box(self, msg):
        if self.last_step_box and self.last_step_spinner:
            self.last_step_box.remove(self.last_step_spinner)

            img = Gtk.Image(icon_name="object-select-symbolic")
            img.get_style_context().add_class("success")

            self.last_step_box.add(img)
            self.last_step_box.reorder_child(img, 0)

        box = Gtk.Box(spacing=11, width_request=300)
        box.get_style_context().add_class("card")
        box.get_style_context().add_class("p-14")

        self.last_step_spinner = Gtk.Spinner(active=True)
        label = Gtk.Label(label=msg)

        box.add(self.last_step_spinner)
        box.add(label)

        self.steps_box.add(box)
        self.window.show_all()

        self.last_step_box = box

    def finish_last_step(self, success):
        if self.last_step_box and self.last_step_spinner:
            self.last_step_box.remove(self.last_step_spinner)
            self.last_step_spinner = None

        if success:
            img = Gtk.Image(icon_name="object-select-symbolic")
            img.get_style_context().add_class("success")
            self.last_step_box.add(img)
            self.last_step_box.reorder_child(img, 0)
        else:
            img = Gtk.Image(icon_name="dialog-error-symbolic")
            img.get_style_context().add_class("error")
            self.last_step_box.add(img)
            self.last_step_box.reorder_child(img, 0)

            # Log box
            box = Gtk.Box()
            box.get_style_context().add_class("card")
            box.get_style_context().add_class("p-14")

            label = Gtk.Label(
                wrap=True, wrap_mode=1, selectable=True, halign="start"
            )  # 1: Pango.WrapMode.CHAR
            label.set_markup(self.last_step_logs.strip())

            scrolledwindow = Gtk.ScrolledWindow(
                hexpand=True, max_content_height=230, max_content_width=700
            )
            scrolledwindow.add(label)
            label.connect(
                "size-allocate",
                self.on_last_step_log_label_size_allocate,
                scrolledwindow,
            )  # scroll to bottom

            box.add(scrolledwindow)
            self.steps_box.add(box)

        self.last_step_box = None

        self.window.show_all()

    def add_log(self, msg, color=""):
        lbl = self.joining_log_label

        if color:
            msg = f'<span color="{color}">{msg}</span>'

        self.last_step_logs += msg + "\n"
        lbl.set_markup("{}\n{}".format(lbl.get_label(), msg))

    def check_domain_already_joined(self):
        # Go to directly joined page if already joined
        self.stderr_text = ""
        self.stdout_text = ""
        self.spinner_label.set_text(_("Checking AD servers..."))

        def on_stdout(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            if line:
                self.stdout_text += line

            return True

        def on_stderr(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            if line:
                self.stderr_text += line + "\n"

            return True

        def on_exit(pid, status):
            if status == 0:
                output = self.stdout_text.strip()
                domain = ""
                if "joined=" in output:
                    domain = output.split("=")[1]

                    print(f"returned domain name: '{domain}'")

                if domain:
                    self.joined_domain_label.set_text(domain)
                    self.main_stack.set_visible_child_name("in_domain")
                else:
                    self.main_stack.set_visible_child_name("main")

            else:
                sys.stderr.write(self.stderr_text + "\n")

                self.application.quit()

        self.spawn_process(
            ["pkexec", ACTIONS_PY, "check_domain"],
            on_stdout,
            on_stderr,
            on_exit,
        )

    def check_credentials(self):
        is_valid = (
            len(self.username_entry.get_text()) != 0
            and len(self.password_entry.get_text()) != 0
            and len(self.domain_entry.get_text()) != 0
            and len(self.hostname_entry.get_text()) != 0
        )

        self.prejoin_btn.set_sensitive(is_valid)

    def save_config_to_file(self):
        config = vars(self.model).copy()

        # Delete unnecessary variables
        config.pop("password", None)
        config.pop("hostname", None)
        config.pop("computer_name", None)

        ConfigManager.save_config(config)

    def save_settings(self):
        if not self.change_hostname():
            return

        # Update model

        # self.model.hostname is set in self.change_hostname()

        self.model.connection_type = (
            "sssd" if self.sssd_radio.get_active() else "winbind"
        )

        if self.ou_specific_radio.get_active():
            self.model.organizational_unit = self.ou_path_entry.get_text().strip()
        else:
            self.model.organizational_unit = ""

        self.save_config_to_file()

    def change_hostname(self):
        current_hostname = self.model.hostname
        new_hostname = self.hostname_entry.get_text()

        if current_hostname == new_hostname:
            return True

        if len(new_hostname) > 63:
            self.show_info_dialog(
                _("Hostname is not valid!"),
                _("Maximum length is 63. Your hostname length is:")
                + str(len(new_hostname)),
            )
            return False

        if re.fullmatch(HOSTNAME_REGEX, new_hostname) is None:
            self.show_info_dialog(
                _("Hostname is not valid!"),
                _("Valid chars: Letters, numbers, '.', '-'."),
            )
            return False

        dialog = Gtk.MessageDialog(
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=_("Are you sure?"),
            secondary_text=_("Hostname will be changed.\n\nOld: {}\nNew: {}").format(
                current_hostname, new_hostname
            ),
        )

        response = dialog.run()
        dialog.hide()

        if response == Gtk.ResponseType.OK:
            p = subprocess.run(
                ["pkexec", ACTIONS_PY, "hostname", new_hostname],
                capture_output=True,
                text=True,
            )
            if p.returncode != 0 and p.returncode != 126:
                self.show_info_dialog(_("Couldn't change hostname"), p.stderr)
                return False

            self.show_info_dialog(
                _("Hostname changed."),
                _("Old: {}\nNew: {}").format(current_hostname, new_hostname),
            )
            self.model.hostname = new_hostname

            return True

        return False

    def spawn_process(self, params, on_stdout, on_stderr, on_exit):
        pid, _stdin, stdout, stderr = GLib.spawn_async(
            params,
            flags=GLib.SPAWN_SEARCH_PATH
            # | GLib.SPAWN_LEAVE_DESCRIPTORS_OPEN
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

    def show_input_dialog(self, title):
        self.input_dialog_lbl.set_text(title)

        response = self.input_dialog.run()
        self.input_dialog.hide()
        if response == Gtk.ResponseType.OK:
            return self.input_dialog_entry.get_text()
        else:
            return ""

    def show_info_dialog(self, title, subtitle):
        dialog = Gtk.MessageDialog(
            buttons=Gtk.ButtonsType.OK,
            text=title,
            secondary_use_markup=True,
            secondary_text=subtitle,
        )
        dialog.run()
        dialog.hide()

    def show_spinner(self, text=None):
        if text:
            self.spinner_label.set_text(text)

        self.main_stack.set_visible_child_name("spinner")

    def spawn_joining_process(self, workgroup):
        self.clear_steps_box()

        def on_stdout(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            if line == "":
                return True

            lbl = self.joining_log_label
            lbl.set_markup(lbl.get_label() + line + "\n")

            if line[0:7] == "STEP===":
                # New step
                msg = line[7:]

                self.last_step_logs = ""
                self.add_step_to_box(_(msg))
            else:
                self.last_step_logs += line + "\n"

            return True

        def on_stderr(source, condition):
            if condition == GLib.IO_HUP:
                return False

            line = source.readline().strip()
            if line == "":
                return True

            self.add_log(line, color="gray")

            return True

        def on_exit(pid, status):
            self.joining_process_pid = None
            lbl = self.joining_log_label

            # Success
            if status == 0:
                # Successfully joined to the domain
                self.finish_last_step(True)
                self.joined_btn_stack.set_visible_child_name("restart_button")
                self.main_stack.set_visible_child_name("in_domain")
                self.joined_domain_label.set_text(self.model.domain)

                self.save_config_to_file()
                return

            # Failed
            if status == 15 or status == 32256 or status == 32512 or status == 126:
                # Cancelled pkexec dialog
                self.main_stack.set_visible_child_name("prejoin")
            else:
                self.joining_title_label.set_text(_("Joining Failed"))
                # self.joining_spinner.stop()
                self.cancel_btn_stack.set_visible_child_name("back")

                logs = lbl.get_text()

                if (
                    "BAD_NAME" in logs
                    or "failed to precreate account in ou" in logs
                    or "Couldn't lookup computer container" in logs
                    or "but is not in the desired organizational unit" in logs
                ):
                    # Not valid OU name like 'computers' instead of 'CN=computers'
                    self.last_step_logs = ""
                    self.add_log(_("Invalid Organizational Unit") + ":", color="red")
                    self.add_log(self.model.organizational_unit)

                elif "The organizational unit does not exist" in logs:
                    self.last_step_logs = ""

                    # OU does not exist
                    self.add_log(
                        _("Organizational Unit does not exist") + ":", color="red"
                    )
                    self.add_log(self.model.organizational_unit)

                elif "authentic" in logs and ("failed" in logs or "Couldn't" in logs):
                    self.last_step_logs = ""

                    self.add_log(_("Username or Password is wrong."), color="red")

            self.finish_last_step(False)

        self.joining_process_pid = self.spawn_process(
            [
                "pkexec",
                ACTIONS_PY,
                "join",
                self.model.hostname,
                self.model.domain,
                self.model.username,
                self.model.password,
                self.model.organizational_unit,
                self.model.connection_type,
                workgroup,
            ],
            on_stdout,
            on_stderr,
            on_exit,
        )

    def check_workgroup(self, task, source_object, task_data, cancellable):
        workgroup = domain_operations.get_netbios_name(self.model.domain)

        if not workgroup:
            # Workgroup not found automatically, ask from user:
            workgroup = self.show_input_dialog(_("Enter WORKSPACE value."))

            if not workgroup:
                workgroup = ""

        task.return_value(workgroup)

    def check_workgroup_finish(self, source, result):
        (status, workgroup) = result.propagate_value()

        if not status:
            workgroup = ""

        self.spawn_joining_process(workgroup)

    # === CALLBACKS ===
    def on_destroy(self, win):
        win.get_application().quit()

    def on_about_btn_clicked(self, btn):
        self.about_dialog.run()
        self.about_dialog.hide()

    # Main Page
    def on_prejoin_btn_clicked(self, btn):
        self.save_settings()

        domain = self.domain_entry.get_text().strip()
        if domain.endswith(".local"):
            self.show_info_dialog(
                _("Warning"),
                _(
                    "Domains that end with '.local' can cause mDNS to resolve and the domain to not be found."
                ),
            )

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

    def on_reset_advanced_settings_clicked(self, btn):
        self.hostname_entry.set_text(self.model.hostname)
        self.ou_path_entry.set_text(self.model.organizational_unit)
        self.ou_specific_radio.set_active(self.model.organizational_unit != "")
        self.sssd_radio.set_active(self.model.connection_type == "sssd")

    def on_back_to_main_btn_clicked(self, btn):
        self.clear_steps_box()
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
        self.check_credentials()

    def on_ou_specific_radio_toggled(self, radiobutton):
        enabled = radiobutton.get_active()
        self.ou_path_entry.set_sensitive(enabled)

    # Pre Join
    def on_join_btn_clicked(self, btn):
        # Clear UI
        # self.joining_spinner.start()
        self.joining_title_label.set_text(_("Joining to the domain..."))
        self.joining_log_label.set_text("")
        self.cancel_btn_stack.set_visible_child_name("cancel")

        self.main_stack.set_visible_child_name("joining")

        if self.model.connection_type == "winbind":
            self.joining_log_label.set_text(_("Checking WORKGROUP...") + "\n")

            task = Gio.Task.new(callback=self.check_workgroup_finish)
            GLib.idle_add(task.run_in_thread, self.check_workgroup)
        else:
            self.spawn_joining_process("")

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
                ["pkexec", ACTIONS_PY, "cancel", str(self.joining_process_pid)]
            )

        dialog.hide()

    def on_joining_log_label_size_allocate(self, label, allocation):
        # Use this signal to scroll logs bottom
        adj = self.joining_viewport.get_vadjustment()
        adj.set_value(adj.get_upper())

    def on_last_step_log_label_size_allocate(self, label, allocation, scrolledwindow):
        # Use this signal to scroll logs bottom
        adj = scrolledwindow.get_vadjustment()
        adj.set_value(adj.get_upper())

    # In Domain page
    def authenticate_and_leave(self, task, source_object, task_data, cancellable):
        # Authenticate on LDAP
        if not self._temp_ldap_username_password:
            return

        print("Authenticating the user on LDAP...")
        self.show_spinner(_("Checking credentials..."))

        (username, password) = self._temp_ldap_username_password

        ldap_username = f"{username}@{self.model.domain.upper()}"
        ldap_client = domain_joiner_ldap.LDAP(
            self.model.domain, ldap_username, password
        )

        # remove temporary value from global context.
        self._temp_ldap_username_password = None

        # Validate credentials, return if false
        try:
            ldap_client.authenticate()

        except ldap.INVALID_CREDENTIALS:
            print(_("Invalid credentials."))

            self.show_info_dialog(_("Error"), _("Invalid credentials."))
            ldap_client._unbind_connection()

            self.main_stack.set_visible_child_name("in_domain")
            return
        except ldap.SERVER_DOWN:
            print(_("Server is not reachable."))

            self.show_info_dialog(_("Error"), _("Server is not reachable."))
            ldap_client._unbind_connection()

            self.main_stack.set_visible_child_name("in_domain")
            return
        except ldap.LDAPError as err:
            print("Other LDAPError:", err)
            self.show_info_dialog(_("Error"), f"LDAP Error:\n{err}")
            ldap_client._unbind_connection()

            self.main_stack.set_visible_child_name("in_domain")
            return
        except Exception as e:
            print("LDAP Authenticate Exception:", e)
            self.show_info_dialog(_("Error"), f"Exception: {e}")

            ldap_client._unbind_connection()
            self.main_stack.set_visible_child_name("in_domain")
            return

        # Credentials are valid, continue...
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
                # Check if hostname still exists in AD
                print(f"Checking if '{self.model.hostname}' still exists in the AD")
                is_hostname_in_ad = ldap_client.check_computer_exists_in_ad(
                    self.model.hostname
                )
                print("is hostname exists in AD:", is_hostname_in_ad)

                if is_hostname_in_ad:
                    self.show_info_dialog(
                        _("Information"),
                        _(
                            "You have successfully left the domain. But your computer still exists in Active Directory."
                        ),
                    )

                ldap_client._unbind_connection()

                # Inform for logout
                env = os.environ["PATH"]
                new_env = env + ":/sbin:/usr/sbin"

                dialog = Gtk.MessageDialog(
                    buttons=Gtk.ButtonsType.OK_CANCEL,
                    text=_("Reboot the computer?"),
                    secondary_text=_(
                        "Please don't forget to save your progress in other applications before the reboot."
                    ),
                )
                response = dialog.run()
                if response == Gtk.ResponseType.OK:
                    subprocess.run(["shutdown", "-r", "now"], env={"PATH": new_env})

                dialog.hide()

                self.main_stack.set_visible_child_name("main")

            else:
                self.show_info_dialog(_("Leaving Failed"), self.stderr_text)

                sys.stderr.write(self.stderr_text + "\n")

                self.main_stack.set_visible_child_name("in_domain")

        args = [
            "pkexec",
            ACTIONS_PY,
            "leave",
            ldap_client.username,
            ldap_client.password,
            self.model.connection_type,
        ]

        self.spawn_process(
            args,
            None,
            on_stderr,
            on_exit,
        )

        self.show_spinner(_("Leaving the domain..."))

    def on_restart_computer_btn_clicked(self, btn):
        env = os.environ["PATH"]
        new_env = env + ":/sbin:/usr/sbin"

        dialog = Gtk.MessageDialog(
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=_("Reboot the computer?"),
            secondary_text=_(
                "Please don't forget to save your progress in other applications before the reboot."
            ),
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            subprocess.run(["shutdown", "-r", "now"], env={"PATH": new_env})

        dialog.hide()

    def on_leave_domain_btn_clicked(self, btn):
        self.stderr_text = ""

        username = ""
        password = ""

        self.ad_dialog_username_entry.set_text("")
        self.ad_dialog_password_entry.set_text("")

        response = self.ad_dialog.run()
        self.ad_dialog.hide()

        if response == Gtk.ResponseType.OK:
            username = self.ad_dialog_username_entry.get_text()
            password = self.ad_dialog_password_entry.get_text()
        else:
            return

        # We set this useless temporary variable because set_task_data is broken. (pardus23)
        self._temp_ldap_username_password = (username, password)
        task = Gio.Task.new()
        GLib.idle_add(task.run_in_thread, self.authenticate_and_leave)

    # AD Leave Dialog
    def on_ad_dialog_username_entry_changed(self, entry):
        is_sensitive = (
            len(entry.get_text()) != 0
            and len(self.ad_dialog_password_entry.get_text()) != 0
        )
        self.ad_dialog_ok_btn.set_sensitive(is_sensitive)

    def on_ad_dialog_password_entry_changed(self, entry):
        is_sensitive = (
            len(entry.get_text()) != 0
            and len(self.ad_dialog_username_entry.get_text()) != 0
        )
        self.ad_dialog_ok_btn.set_sensitive(is_sensitive)

    def on_input_dialog_entry_changed(self, entry):
        self.input_dialog_ok_btn.set_sensitive(len(entry.get_text()) != 0)

    def on_ad_dialog_password_entry_icon_press(self, entry, icon_pos, event):
        entry.set_visibility(True)
        entry.set_icon_from_icon_name(1, "view-reveal-symbolic")

    def on_ad_dialog_password_entry_icon_release(self, entry, icon_pos, event):
        entry.set_visibility(False)
        entry.set_icon_from_icon_name(1, "view-conceal-symbolic")
