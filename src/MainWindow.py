#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import subprocess
import platform
import locale
from locale import gettext as _

import gi
gi.require_version("GLib", "2.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import GLib, Gtk, Vte

# Translation Constants:
APPNAME = "pardus-domain-joiner"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.set_translation_domain(APPNAME)
        self.builder.add_from_file(os.path.dirname(
            os.path.abspath(__file__)) + "/../ui/MainWindow.glade")
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("main_window")
        self.window.set_application()
        self.window.set_title(_("Pardus Domain Settings"))
        self.window.connect("destroy", self.onDestroy)

        self.define_components()

        self.check_realm_list()

        self.window.show_all()

    def define_components(self):
        # stacks
        self.main_stack = self.builder.get_object("main_stack")
        self.second_stack = self.builder.get_object("second_stack")

        # labels
        self.compname_label = self.builder.get_object("compname_label")
        self.domain_title_label = self.builder.get_object("domain_title_label")
        self.domain_details_label = self.builder.get_object("domain_details_label")
        self.message_label = self.builder.get_object("message_label")
        self.required_label = self.builder.get_object("required_label")
        self.id_label = self.builder.get_object("id_label")
        self.domain_details_label.set_visible(False)

        # entrys
        self.comp_name_entry = self.builder.get_object('comp_name_entry')
        self.domain_name_entry = self.builder.get_object('domain_name_entry')
        self.user_name_entry = self.builder.get_object('user_name_entry')
        self.password_entry = self.builder.get_object('password_entry')
        self.id_entry = self.builder.get_object("id_entry")

        # organizational unit part
        self.ou_default_rb = self.builder.get_object(
            "ou_default_path_rb")
        self.ou_specific_rb = self.builder.get_object(
            "ou_specific_path_rb")
        self.ou_specific_entry= self.builder.get_object(
            "ou_specific_path_entry")
        self.ou_warning_label= self.builder.get_object(
            "ou_warning_label")

        # buttons
        self.reboot_button = self.builder.get_object("reboot_button")
        self.smb_check_button = self.builder.get_object("smb_check_button")

        # vte
        self.vtebox = self.builder.get_object("vte_box")
        self.vtetextview  = self.builder.get_object("vte_text_view")

        # id check
        self.id_dialog = self.builder.get_object("id_dialog")
        self.id_dialog.set_title(_("Information"))

        # dialogs
        self.leave_dialog = self.builder.get_object("leave_dialog")
        self.leave_dialog.set_title(_("Warning"))

        # domain detail
        self.details_revealer = self.builder.get_object("details_revealer")
        self.details_revealer.set_reveal_child(False)
        self.domain_details_label.set_visible(False)

        # used to control button clicks
        self.id_clicked=False
        self.smb_check_clicked="False"

        # checking for errors when joining the domain
        self.password_check = ""
        self.domain_check = ""
        self.domain_name_check = ""
        self.join_check = ""

    def onDestroy(self,Widget):
        Gtk.main_quit()

    def on_dialog_close(self, widget):
        self.id_dialog.hide()
        self.leave_dialog.hide()

    def on_window_delete_event(self, widget, event):
        self.id_dialog.hide()
        self.leave_dialog.hide()
        return True

    def set_password_icon_press(self, Widget, icon_pos, event):
        self.password_entry.set_visibility(True)
        self.password_entry.set_icon_from_icon_name(1,'view-reveal-symbolic')

    def set_password_icon_release(self, Widget, icon_pos, event):
        self.password_entry.set_visibility(False)
        self.password_entry.set_icon_from_icon_name(1,'view-conceal-symbolic')

    def on_restart_button(self,Widget):
        subprocess.call(["/sbin/reboot"])
    
    def on_force_restart_button(self,Widget):
        os.system('echo 1 > /proc/sys/kernel/sysrq')
        os.system('sync')
        os.system('echo b > /proc/sysrq-trigger')

    def on_details_button(self,button):
        self.details_revealer.set_reveal_child(button.get_active())

    def check_realm_list(self):
        cmd = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Checks.py", "list"]
        self.expid = self.startCheckProcess(cmd)

    def on_id_check_button(self,Widget):
        self.id_name = self.id_entry.get_text()
        self.id_clicked = True
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Checks.py", "id_check", self.id_name]
        pid = self.startCheckProcess(command)

    def on_leave_button(self,Widget):
        self.leave_dialog.run()

    def on_leave_and_restart_button(self,Widget):
        command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py", "leave"]
        pid = self.startLeaveProcess(command)

    def hostname(self):
        return platform.node().split(".")[0] # just for comp name

    def on_join_button(self,Widget):
        self.comp = self.comp_name_entry.get_text()
        self.domain = self.domain_name_entry.get_text()
        self.user = self.user_name_entry.get_text()
        self.passwd = self.password_entry.get_text()
        self.ouaddress = ""

        if self.comp == "" or self.domain == "" or self.user == "" or self.passwd == "":
            self.required_label.set_markup("<span color='red'>{}</span>".format(_("All blanks must be filled!")))
        elif self.ou_specific_rb.get_active() and self.ouaddress == "":
            self.ou_warning_label.set_markup("<span color='red'>{}</span>".format(_("The specific organizational unit path was not entered!")))
        else:
            if self.smb_check_button.get_active():
                self.smb_check_clicked = "True"

            self.comp_name_entry.set_text("")
            self.domain_name_entry.set_text("")
            self.user_name_entry.set_text("")
            self.password_entry.set_text("")
            self.required_label.set_text("")

            fulldn = ", dc=" + self.domain.replace(".", ", dc=")
            if (self.ou_default_rb.get_active()):
                self.ouaddress = "cn=Computers" + fulldn
            else:
                self.ouaddress = self.ou_specific_entry.get_text() + fulldn
            self.ou_warning_label.set_text("")

            if self.ou_specific_rb.get_active() and self.ouaddress == ",dc="+fulldn:
                self.ou_warning_label.set_markup("<span color='red'>{}</span>".format(_("The specific ou path was not entered!")))

            self.main_stack.set_visible_child_name("join_page")
            self.second_stack.set_visible_child_name("message_page")
            self.message_label.set_text("")
            self.reboot_button.set_sensitive(False)
            try:
                command = ["/usr/bin/pkexec", os.path.dirname(os.path.abspath(__file__))
                           + "/Actions.py","join", self.comp, self.domain,self.user,self.passwd, self.ouaddress,self.smb_check_clicked]
                self.startJoinProcess(command)
            except Exception as e:
                print(_("Error: domain failed to join realm"))
                self.message_label.set_markup("<span color='red'>{}</span>".format(_("Not reachable, check your DNS address.")))
                self.reboot_button.set_sensitive(True)
                self.reboot_button.set_label(_("Close"))

    def on_reboot_button(self,Widget):
        if self.reboot_button.get_label() == _("Back"):
            comp_name = self.hostname()
            self.comp_name_entry.set_text(comp_name)
            self.second_stack.set_visible_child_name("domain_join_page")
            start, end = self.vtetextview.get_buffer().get_bounds()
            self.vtetextview.get_buffer().delete(start,end)
        elif self.reboot_button.get_label() == _("Close"):
            Gtk.main_quit()
        else:
            self.on_restart_button(Widget)

    def startJoinProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onJoinProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onJoinProcessStderr)
        GLib.child_watch_add(GLib.PRIORITY_DEFAULT_IDLE, pid, self.onJoinProcessExit)

    def onJoinProcessStdout(self, source, condition):
        if condition == GLib.IO_HUP:
            return False
        line = source.readline()
        print(line)

        if line.strip()==_("Not reachable, check your DNS address."):
            self.domain_check = "False"
        if line.strip()==_("Domain name check: False"):
            self.domain_name_check = "False"
        if line.strip() == _("Domain username or password check: False"):
            self.password_check = "False"
        if line.strip() == _("This computer has been successfully added to the domain."):
            self.join_check = "True"
        self.vtetextview.get_buffer().insert(self.vtetextview.get_buffer().get_end_iter(), line)
        self.vtetextview.scroll_to_iter(self.vtetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

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

        self.reboot_button.set_label(_("Reboot"))
        self.vtetextview.scroll_to_iter(self.vtetextview.get_buffer().get_end_iter(), 0.0, False, 0.0, 0.0)

        if status == 32256:
            self.message_label.set_markup("<span color='red'>{}</span>".format(_("You don't enter the password. Try again!")))
        else:
            if self.domain_check == "False":
                self.message_label.set_markup("<span color='red'>{}</span>".format(_("Not reachable, check your DNS address.")))
                self.reboot_button.set_label(_("Close"))
                self.domain_check = ""
            elif self.domain_name_check == "False":
                self.message_label.set_markup("<span color='red'>{}</span>".format(_("Domain name is incorrect.")))
                self.reboot_button.set_label(_("Back"))
                self.domain_name_check = ""
            elif self.password_check == "False":
                self.message_label.set_markup("<span color='red'>{}</span>".format(_("Your password or username is incorrect.")))
                self.reboot_button.set_label(_("Back"))
                self.password_check = ""
            elif self.join_check == "True":
                self.message_label.set_markup("<span color='green'>{}</span>".format(_("This computer has been successfully added to the domain.")))
                self.status = True
            else:
                self.message_label.set_markup("<span color='red'>{}</span>".format(_("Error: domain failed to join realm")))
                self.reboot_button.set_label(_("Close"))

    def startCheckProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onCheckProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onCheckProcessStderr)
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

            if domain_name == '':
                self.main_stack.set_visible_child_name("join_page")
                self.second_stack.set_visible_child_name("domain_join_page")
            else:
                domain_name = domain_name.split("\n")
                self.main_stack.set_visible_child_name("leave_page")
                self.compname_label.set_markup("\n{} <b>{}</b>".format( _("Your computer"), comp_name))
                self.domain_title_label.set_text(domain_name[0])
                self.domain_details_label.set_text(domain_details)

        if self.id_clicked:
            self.id_name = self.id_entry.get_text()
            if os.path.exists("/tmp/idcheck"):
                with open("/tmp/idcheck","r") as idfile:
                    id_group = idfile.readline()
                    self.id_entry.set_text("")
                    if status == 0:
                        self.id_label.set_markup("<b>{}</b>\n{}".format(self.id_name,id_group))
                    elif status == 256:
                        self.id_label.set_markup(
                            "<b>{}</b> {}".format(self.id_name, _("user not found. Try again!")))
                    else:
                        self.id_label.set_text(_("No such user"))
            else:
                self.id_label.set_text(_("Error!"))
            self.id_dialog.run()

    def startLeaveProcess(self, params):
        pid, stdin, stdout, stderr = GLib.spawn_async(params, flags=GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                      standard_output=True, standard_error=True)
        GLib.io_add_watch(GLib.IOChannel(stdout), GLib.IO_IN | GLib.IO_HUP, self.onLeaveProcessStdout)
        GLib.io_add_watch(GLib.IOChannel(stderr), GLib.IO_IN | GLib.IO_HUP, self.onLeaveProcessStderr)
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

if __name__ == "__main__":
    app = MainWindow()
    Gtk.main()