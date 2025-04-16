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
        self.connection_type = "winbind"


class MainWindow:
    def __init__(self, application):
        self.application = application

        self.setup_ui_builder()

        self.setup_window()

        self.setup_widgets()

        self.setup_variables()

        self.setup_about_dialog()

        self.setup_css()

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
        self.main_stack = self.builder.get_object("main_stack")

        # labels
        # self.compname_label = self.builder.get_object("compname_label")
        # self.domain_title_label = self.builder.get_object("domain_title_label")
        # # self.domain_details_label = self.builder.get_object("domain_details_label")
        # self.message_label = self.builder.get_object("message_label")
        # self.required_label = self.builder.get_object("required_label")
        # self.id_label = self.builder.get_object("id_label")
        # self.domain_details_label.set_visible(False)

        # Page: User Credentials
        self.username_entry = self.builder.get_object("username_entry")
        self.password_entry = self.builder.get_object("password_entry")
        self.join_btn = self.builder.get_object("join_btn")

        # Page: Settings
        # self.ou_default_rb = self.builder.get_object("ou_default_path_rb")
        # self.ou_specific_rb = self.builder.get_object("ou_specific_path_rb")
        self.ou_specific_entry = self.builder.get_object("ou_specific_entry")
        # self.ou_warning_label = self.builder.get_object("ou_warning_label")

        # buttons
        self.reboot_button = self.builder.get_object("reboot_button")
        self.smb_check_button = self.builder.get_object("smb_check_button")

        # vte
        self.vtebox = self.builder.get_object("vte_box")
        self.vtetextview = self.builder.get_object("vte_text_view")

        # id check
        self.id_dialog = self.builder.get_object("id_dialog")
        self.id_dialog.set_title(_("Information"))

        # dialogs
        self.leave_dialog = self.builder.get_object("leave_dialog")
        self.leave_dialog.set_title(_("Warning"))

        # about dialog
        self.about_dialog = self.builder.get_object("about_dialog")

        # domain detail
        # self.details_revealer = self.builder.get_object("details_revealer")
        # self.details_revealer.set_reveal_child(False)
        # self.domain_details_label.set_visible(False)

    def setup_variables(self):
        self.model = Model()

        # used to control button clicks
        self.id_clicked = False
        self.smb_check_clicked = "False"

        self.client = ""

        # checking for errors when joining the domain
        self.user_password_check = False
        self.domain_check = False
        self.domain_name_check = False
        self.ou_address_check = False
        self.join_check = False

    def setup_about_dialog(self):
        if self.about_dialog.get_titlebar is None:
            about_headerbar = Gtk.HeaderBar.new()
            about_headerbar.set_show_close_button(True)
            about_headerbar.set_title(_("Pardus Domain Settings"))
            about_headerbar.show_all()
            self.about_dialog.set_titlebar(about_headerbar)

            try:
                version = open(
                    os.path.dirname(os.path.abspath(__file__)) + "/__version__"
                ).readline()
                self.about_dialog.set_version(version)
            except Exception:
                pass

    # == CALLBACKS ==
    def on_destroy(self, win):
        self.window.get_application().quit()

    def on_dialog_close(self, widget):
        self.id_dialog.hide()
        self.leave_dialog.hide()

    def on_ui_about_button_clicked(self, button):
        self.about_dialog.run()
        self.about_dialog.hide()

    def on_subwindow_delete_event(self, widget, event):
        self.id_dialog.hide()
        self.leave_dialog.hide()
        return True

    # == Page 1: Domain Name ==
    def on_domain_entry_activate(self, entry):
        if len(entry.get_text()) != 0:
            # check entry
            self.model.domain = entry.get_text()
            self.main_stack.set_visible_child_name("settings_page")
            print(vars(self.model))

    # == Page 2: Settings ==
    def on_winbind_rb_toggled(self, btn):
        if btn.get_active():
            self.model.connection_type = "winbind"

        print(vars(self.model))

    def on_sssd_rb_toggled(self, btn):
        if btn.get_active():
            self.model.connection_type = "sssd"

        print(vars(self.model))

    def on_ou_default_rb_toggled(self, btn):
        if btn.get_active():
            self.model.organizational_unit = ""

        print(vars(self.model))

    def on_ou_specific_rb_toggled(self, btn):
        self.ou_specific_entry.set_sensitive(btn.get_active())

        print(vars(self.model))

    def on_next_page_hostname_btn_clicked(self, btn):
        if self.ou_specific_entry.get_sensitive():
            self.model.organizational_unit = self.ou_specific_entry.get_text()

        self.main_stack.set_visible_child_name("hostname_page")
        print(vars(self.model))

    # == Page 3: Computer Name ==
    def on_hostname_entry_activate(self, entry):
        if len(entry.get_text()) != 0:
            self.model.computer_name = entry.get_text()
            self.main_stack.set_visible_child_name("credentials_page")
            print(vars(self.model))

    # == Page 4: User Credentials ==

    def on_username_entry_changed(self, entry):
        self.check_credentials()

    def on_password_entry_changed(self, entry):
        self.check_credentials()

    def on_join_btn_clicked(self, btn):
        # check entry
        self.model.username = self.username_entry.get_text()
        self.model.password = self.password_entry.get_text()

        self.main_stack.set_visible_child_name("progress_page")

        print(vars(self.model))

    def on_password_entry_icon_press(self, entry, icon_pos, event):
        self.password_entry.set_visibility(True)
        self.password_entry.set_icon_from_icon_name(1, "view-reveal-symbolic")

    def on_password_entry_icon_release(self, entry, icon_pos, event):
        self.password_entry.set_visibility(False)
        self.password_entry.set_icon_from_icon_name(1, "view-conceal-symbolic")

    def check_credentials(self):
        is_valid = (
            len(self.username_entry.get_text()) != 0
            and len(self.password_entry.get_text()) != 0
        )

        self.join_btn.set_sensitive(is_valid)

    # == Page 5: Joining Progress ==

    # == Page 6: Successfully in Domain ==
    def on_leave_btn_clicked(self, btn):
        self.main_stack.set_visible_child_name("leave_success_page")

    def on_restart_button(self, Widget):
        command = [
            "/usr/bin/pkexec",
            os.path.dirname(os.path.abspath(__file__)) + "/restart.sh",
        ]
        pid = self.startRestartProcess(command)

    def on_details_button(self, button):
        self.details_revealer.set_reveal_child(button.get_active())

    def check_realm_list(self):
        cmd = [
            "/usr/bin/pkexec",
            os.path.dirname(os.path.abspath(__file__)) + "/Checks.py",
            "list",
        ]
        self.expid = self.startCheckProcess(cmd)

    def on_id_check_button(self, Widget):
        self.id_name = self.id_entry.get_text()
        self.id_clicked = True
        command = [
            "/usr/bin/pkexec",
            os.path.dirname(os.path.abspath(__file__)) + "/Checks.py",
            "id_check",
            self.id_name,
        ]
        pid = self.startCheckProcess(command)

    def on_leave_button(self, Widget):
        self.leave_dialog.run()

    def on_leave_and_restart_button(self, Widget):
        command = [
            "/usr/bin/pkexec",
            os.path.dirname(os.path.abspath(__file__)) + "/Actions.py",
            "leave",
        ]
        pid = self.startLeaveProcess(command)

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

    def on_join_button(self, Widget):
        comp = self.comp_name_entry.get_text()
        domain = self.domain_name_entry.get_text()
        user = self.user_name_entry.get_text()
        passwd = self.password_entry.get_text()
        ouaddress = ""

        if comp == "" or domain == "" or user == "" or passwd == "":
            self.required_label.set_markup(
                "<span color='red'>{}</span>".format(_("All blanks must be filled!"))
            )
        elif (
            self.ou_specific_rb.get_active() and self.ou_specific_entry.get_text() == ""
        ):
            self.ou_warning_label.set_markup(
                "<span color='red'>{}</span>".format(
                    _("The specific organizational unit path was not entered!")
                )
            )
        else:
            if self.smb_check_button.get_active():
                self.smb_check_clicked = "True"

            self.comp_name_entry.set_text("")
            self.domain_name_entry.set_text("")
            self.user_name_entry.set_text("")
            self.password_entry.set_text("")
            self.required_label.set_text("")

            ouaddress = self.generate_ouaddress(domain)
            self.ou_warning_label.set_text("")

            self.client = user + "@" + domain.upper()

            self.main_stack.set_visible_child_name("join_page")
            self.second_stack.set_visible_child_name("message_page")
            self.message_label.set_text("")
            self.reboot_button.set_sensitive(False)
            try:
                domain_user = user + "@" + domain
                ldap_search = LDAP(domain, domain_user, passwd)
                result = ldap_search.check_computer_exists_in_ad(comp)
                if not result:
                    command = [
                        "/usr/bin/pkexec",
                        os.path.dirname(os.path.abspath(__file__)) + "/Actions.py",
                        "join",
                        comp,
                        domain.upper(),
                        user,
                        passwd,
                        ouaddress,
                        self.smb_check_clicked,
                    ]
                    self.startJoinProcess(command)
                    self.vtetextview.get_buffer().insert(
                        self.vtetextview.get_buffer().get_end_iter(),
                        _("Please wait...") + "\n",
                    )
                    self.vtetextview.scroll_to_iter(
                        self.vtetextview.get_buffer().get_end_iter(),
                        0.0,
                        False,
                        0.0,
                        0.0,
                    )
                else:
                    self.vtetextview.get_buffer().insert(
                        self.vtetextview.get_buffer().get_end_iter(),
                        _(
                            f"Hostname {comp} already exists in Active Directory!\nPlease change hostname..."
                        )
                        + "\n",
                    )
                    self.message_label.set_markup(
                        "<span color='red'>{}</span>".format(
                            _("Please change hostname...")
                        )
                    )
                    self.reboot_button.set_sensitive(True)
                    self.reboot_button.set_label(_("Back"))
            except Exception as e:
                print(_("Error: domain failed to join realm"))
                print(_(f"Error: {e}"))
                self.message_label.set_markup(
                    "<span color='red'>{}</span>".format(
                        _("Not reachable, check your DNS address.")
                    )
                )
                self.reboot_button.set_sensitive(True)
                self.reboot_button.set_label(_("Close"))

    def on_reboot_button(self, Widget):
        if self.reboot_button.get_label() == _("Back"):
            comp_name = self.hostname()
            self.comp_name_entry.set_text(comp_name)
            self.second_stack.set_visible_child_name("domain_join_page")
            start, end = self.vtetextview.get_buffer().get_bounds()
            self.vtetextview.get_buffer().delete(start, end)
        elif self.reboot_button.get_label() == _("Close"):
            self.window.get_application().quit()
        else:
            self.on_restart_button(Widget)

    def startJoinProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(
            params,
            flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            standard_output=True,
            standard_error=True,
        )
        GLib.io_add_watch(
            GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onJoinProcessStdout
        )
        GLib.io_add_watch(
            GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onJoinProcessStderr
        )
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid, self.onJoinProcessExit)

    def onJoinProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)

        if line.strip() == _(f"No such realm found {self.client.split('@')[1]}"):
            self.domain_check = True
        if line.strip() == _("Domain name check: False."):
            self.domain_name_check = True
        if line.strip() == _("Preauthentication failed!"):
            self.user_password_check = True
        if line.strip() == _(f"Client '{self.client}' not found in Kerberos database!"):
            self.user_password_check = True
        if line.strip() == _("The organizational unit does not exist."):
            self.ou_address_check = True
        if line.strip() == _("Not in the desired organizational unit."):
            self.ou_address_check = True
        if line.strip() == _(
            "This computer has been successfully added to the domain."
        ):
            self.join_check = True
        self.vtetextview.get_buffer().insert(
            self.vtetextview.get_buffer().get_end_iter(), line
        )
        self.vtetextview.scroll_to_iter(
            self.vtetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0
        )

        return True

    def onJoinProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onJoinProcessExit(self, pid, status):
        print("onJoinProcessExit - status: {}".format(status))
        self.reboot_button.set_sensitive(True)

        self.reboot_button.set_label(_("Restart"))
        self.vtetextview.scroll_to_iter(
            self.vtetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0
        )

        if status == 32256:
            self.message_label.set_markup(
                "<span color='red'>{}</span>".format(
                    _("You don't enter the password. Try again!")
                )
            )
        else:
            if self.domain_check:
                self.message_label.set_markup(
                    "<span color='red'>{}</span>".format(
                        _(f"No such realm found {self.client.split('@')[1]}")
                    )
                )
                self.reboot_button.set_label(_("Back"))
                self.domain_check = False
            elif self.domain_name_check:
                self.message_label.set_markup(
                    "<span color='red'>{}</span>".format(_("Domain name is incorrect."))
                )
                self.reboot_button.set_label(_("Back"))
                self.domain_name_check = False
            elif self.user_password_check:
                self.message_label.set_markup(
                    "<span color='red'>{}</span>".format(
                        _("Username or password is incorrect!")
                    )
                )
                self.reboot_button.set_label(_("Back"))
                self.user_password_check = False
            elif self.ou_address_check:
                self.message_label.set_markup(
                    "<span color='red'>{}</span>".format(
                        _("The organizational unit does not exist or is incorrect")
                    )
                )
                self.reboot_button.set_label(_("Back"))
                self.ou_address_check = False
            elif self.join_check:
                self.message_label.set_markup(
                    "<span color='green'>{}</span>".format(
                        _("This computer has been successfully added to the domain.")
                    )
                )
            else:
                self.message_label.set_markup(
                    "<span color='red'>{}</span>".format(
                        _("Error: domain failed to join realm")
                    )
                )
                self.reboot_button.set_label(_("Close"))

    def startCheckProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(
            params,
            flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            standard_output=True,
            standard_error=True,
        )
        GLib.io_add_watch(
            GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onCheckProcessStdout
        )
        GLib.io_add_watch(
            GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onCheckProcessStderr
        )
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid, self.onCheckProcessExit)

    def onCheckProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onCheckProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onCheckProcessExit(self, pid, status):
        print("onCheckProcessExit - status: {}".format(status))
        comp_name = self.hostname()
        self.comp_name_entry.set_text(comp_name)

        if os.path.exists("/tmp/realmlist"):
            with open("/tmp/realmlist") as realmfile:
                domain_name = realmfile.readline()
                domain_details = realmfile.read()

            if domain_name == "":
                self.main_stack.set_visible_child_name("join_page")
                self.second_stack.set_visible_child_name("domain_join_page")
            else:
                domain_name = domain_name.split("\n")
                self.main_stack.set_visible_child_name("leave_page")
                self.compname_label.set_markup(
                    "\n{} <b>{}</b>".format(_("Your computer"), comp_name)
                )
                self.domain_title_label.set_text(domain_name[0])
                self.domain_details_label.set_text(domain_details)

        if self.id_clicked:
            self.id_name = self.id_entry.get_text()
            if os.path.exists("/tmp/idcheck"):
                with open("/tmp/idcheck", "r") as idfile:
                    id_group = idfile.readline()
                    self.id_entry.set_text("")
                    if status == 0:
                        self.id_label.set_markup(
                            "<b>{}</b>\n{}".format(self.id_name, id_group)
                        )
                    elif status == 256:
                        self.id_label.set_markup(
                            "<b>{}</b> {}".format(
                                self.id_name, _("user not found. Try again!")
                            )
                        )
                    else:
                        self.id_label.set_text(_("No such user"))
            else:
                self.id_label.set_text(_("Error!"))
            self.id_dialog.run()

    def startLeaveProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(
            params,
            flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            standard_output=True,
            standard_error=True,
        )
        GLib.io_add_watch(
            GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onLeaveProcessStdout
        )
        GLib.io_add_watch(
            GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onLeaveProcessStderr
        )
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid, self.onLeaveProcessExit)

        return pid

    def onLeaveProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onLeaveProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onLeaveProcessExit(self, pid, status):
        print("onLeaveProcessExit - status: {}".format(status))
        self.leave_dialog.hide()
        if status == 0:
            self.main_stack.set_visible_child_name("end_page")

    def startRestartProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(
            params,
            flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            standard_output=True,
            standard_error=True,
        )
        GLib.io_add_watch(
            GLib.IOChannel(stdout),
            GLib.IO_IN | GLib.IO_HUP,
            self.onRestartProcessStdout,
        )
        GLib.io_add_watch(
            GLib.IOChannel(stderr),
            GLib.IO_IN | GLib.IO_HUP,
            self.onRestartProcessStderr,
        )
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid, self.onRestartProcessExit)

        return pid

    def onRestartProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onRestartProcessStderr(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)
        return True

    def onRestartProcessExit(self, pid, status):
        print("onRestartProcessExit - status: {}".format(status))

        if status == 0:
            print(_("Successful"))
        else:
            subprocess.call(["gnome-session-quit", "--no-prompt", "--force"])
