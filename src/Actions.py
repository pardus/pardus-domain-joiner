#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import os
import sys
import subprocess
import apt_pkg
import locale
from locale import gettext as _

# Translation Constants:
APPNAME = "pardus-domain-joiner"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)


def main():
    def control_lock():
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError:
            return False
        apt_pkg.pkgsystem_unlock()
        return True

    def update():
        subprocess.call(
            ["apt", "update", "-o", "APT::Status-Fd=2"],
            env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
        )

    def install(package_list):
        for package in package_list:
            subprocess.call(
                ["apt", "install", package, "-yq", "-o", "APT::Status-Fd=2"],
                env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
            )

    def set_hostname(comp_name):
        subprocess.call(["hostnamectl", "hostname", comp_name])
        print("changed hostname: ", comp_name)

    def update_hostname_file(comp_name, domain):
        # to check file /etc/hostname
        hostname_file = "/etc/hostname"
        with open(hostname_file, "r") as file:
            current_hostname = file.readline().strip()
            print(_("checking /etc/hostname file..."))
            if comp_name + "." + domain not in current_hostname:
                print(_("added domain name to /etc/hostname file"))
                with open(hostname_file, "w") as file:
                    new_hostname = "{}.{}".format(comp_name, domain)
                    file.write(new_hostname)
            else:
                print(_("done"))

    def update_hosts_file(comp_name, domain):
        # to check file /etc/hosts
        hosts_file = "/etc/hosts"
        with open(hosts_file, "r") as file:
            lines = file.readlines()
        print(_("checking /etc/hosts file..."))
        new_hosts_file = []
        domain_exists = False

        for line in lines:
            if line.strip().startswith("127.0.1.1"):
                if f"{comp_name}.{domain}" not in line:
                    line = f"127.0.1.1 {comp_name}.{domain} {comp_name}\n"
                domain_exists = True
            new_hosts_file.append(line)

        if not domain_exists:
            new_hosts_file.append(f"127.0.1.1 {comp_name}.{domain} {comp_name}\n")

        with open(hosts_file, "w") as file:
            file.writelines(new_hosts_file)

        if domain_exists:
            print(_("done"))
        else:
            print(_("added domain name to /etc/hosts file"))

    def rewrite_conf(file, settings):
        config = configparser.RawConfigParser()
        config.optionxform = str  # This prevents it from converting keys to lowercase

        if os.path.exists(file):
            config.read(file)

        for section, options in settings.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in options.items():
                config.set(section, key, value)

        with open(file, "w") as configfile:
            config.write(configfile)

    def join(comp_name, domain, user, passwd, ouaddress, smb_settings):
        try:
            # to update
            update()

            # to install packages
            package_list = [
                "krb5-user",
                "samba",
                "sssd",
                "libsss-sudo",
                "realmd",
                "packagekit",
                "adcli",
                "sssd-tools",
                "cifs-utils",
                "smbclient",
            ]
            install(package_list)

            # to join domain
            if not os.path.isfile("/etc/krb5.conf"):
                print(_("Packages are not installed."))
                sys.exit(1)

            update_hostname_file(comp_name, domain)
            update_hosts_file(comp_name, domain)

            try:
                result = subprocess.check_output(["realm", "discover"]).decode("utf-8")

                for line in result.split("\n"):
                    if line.strip().startswith("domain-name:"):
                        if line.split(":")[1] == " " + domain:
                            print(_("joining the domain..."))
                        else:
                            print(_("Domain name check: False"))
                            sys.exit(1)

            except subprocess.CalledProcessError as e:
                print(_("An error occurred! Exit Code:"), e.returncode)
                print(_("Not reachable, check your DNS address."), file=sys.stdout)
                sys.exit(1)

            process = subprocess.Popen(
                ['realm join -v --computer-ou="' + ouaddress + '" --user="' + user + "@" + domain.upper() + '" ' + domain.lower()], stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True
            )
            process.communicate(passwd.encode("utf-8"))

            password_check = process.returncode
            if password_check == 1:
                print(_("Domain username or password check: False"), file=sys.stdout)

            if smb_settings == "True":
                # Samba Authentication
                # rewrite file /etc/samba/smb.conf
                smb_file = "/etc/samba/smb.conf"
                samba_settings = {
                    "global": {
                        "unix charset": "UTF-8",
                        "workgroup": domain.split(".")[0].upper(),
                        "client signing": "yes",
                        "client use spnego": "yes",
                        "dedicated keytab file": "/etc/krb5.keytab",
                        "kerberos method": "secrets and keytab",
                        "realm": domain,
                        "dns proxy": "no",
                        "map to guest": "Bad User",
                        "log file": "/var/log/samba/log.%m",
                        "max log size": 1000,
                        "syslog": 0,
                    },
                }
                rewrite_conf(smb_file, samba_settings)

            # to check and rewrite file /etc/sssd/sssd.conf
            sssd_file = "/etc/sssd/sssd.conf"
            sssd_settings = {
                "sssd": {
                    "domains": domain,
                    "config_file_version": 2,
                    "services": "nss, pam",
                },
                f"domain/{domain}": {
                    "default_shell": "/bin/bash",
                    "ad_server": domain,
                    "krb5_store_password_if_offline": True,
                    "cache_credentials": True,
                    "krb5_realm": domain,
                    "realmd_tags": "manages-system joined-with-adcli",
                    "id_provider": "ad",
                    "fallback_homedir": "/home/%u@%d",
                    "ad_domain": domain.upper(),
                    "use_fully_qualified_names": False,
                    "ldap_id_mapping": True,
                    "access_provider": "ad",
                    "ad_gpo_access_control": "permissive",
                    "ad_gpo_ignore_unreadable": True,
                },
            }
            rewrite_conf(sssd_file, sssd_settings)
            os.chmod(sssd_file, 600)
            
            subprocess.call(
                ["pam-auth-update", "--enable ", "pardus-pam-config"],
                env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"},
            )
            subprocess.call(["systemctl", "restart ", "sssd"])

            if password_check == 0:
                print(_("This computer has been successfully added to the domain."))
        except Exception as e:
            print(e)

    def permit():
        subprocess.call(["realm", "permit", "-a"])

    def leave():
        subprocess.call(["realm", "leave", "-v"])

    if len(sys.argv) > 1:
        if control_lock():
            if sys.argv[1] == "join":
                set_hostname(sys.argv[2])
                join(
                    sys.argv[2],
                    sys.argv[3],
                    sys.argv[4],
                    sys.argv[5],
                    sys.argv[6],
                    sys.argv[7],
                )
                permit()
            elif sys.argv[1] == "host":
                update_hostname_file(sys.argv[2], sys.argv[3])
                update_hosts_file(sys.argv[2], sys.argv[3])
            elif sys.argv[1] == "leave":
                leave()
        else:
            print("lock error")
            sys.exit(1)
    else:
        print("no argument passed")


if __name__ == "__main__":
    main()
