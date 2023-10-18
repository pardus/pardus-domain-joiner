#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import apt_pkg
from locale import gettext as _

def main():

    def control_lock():
        apt_pkg.init_system()
        try:
            apt_pkg.pkgsystem_lock()
        except SystemError:
            return False
        apt_pkg.pkgsystem_unlock()
        return True

    def join(comp_name,domain,user,passwd,ouaddress):
        try:
            # to update
            subprocess.call(["apt", "update", "-o", "APT::Status-Fd=2"],
                            env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})

            # to install packages
            packagelist = ["krb5-user", "samba", "sssd", "libsss-sudo",
                        "realmd", "packagekit", "adcli", "sssd-tools", "cifs-utils", "smbclient"]
            for p in  packagelist:
                subprocess.call(["apt", "install", p, "-yq", "-o", "APT::Status-Fd=2"],
                            env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'})
            
            # to join domain
            if (os.path.isfile("/etc/sssd/sssd.conf") and os.path.isfile("/etc/krb5.conf")):
                print(_("Packages are installed."))
            else:
                print(_("Packages are not installed."))
                exit()
                        
            subprocess.call(["sudo","realm","discover","-v"])
            print(_("joining the domain..."))

            command = "echo " + passwd + " | sudo realm join -v --computer-ou=\""+ouaddress+"\" --user=\""+user+"@"+domain.upper()+"\" "+domain.lower()
            proc = subprocess.run([command], stdout=subprocess.PIPE, shell=True)
            password_check = proc.returncode
            if password_check == 1:
                print(_("Domain username or password check: False"), file=sys.stdout)
            
            # 
            with open("/etc/sssd/sssd.conf","w") as sssd_file:
                sssd_file.write("""
[sssd]
domains = lawad.local
config_file_version = 2
services = nss, pam

[domain/lawad.local]
default_shell = /bin/bash
ad_server = lawad.local
krb5_store_password_if_offline = True
cache_credentials = True
krb5_realm = LAWAD.LOCAL
realmd_tags = manages-system joined-with-adcli 
id_provider = ad
fallback_homedir = /home/%u@%d
ad_domain = lawad.local
use_fully_qualified_names = False
ldap_id_mapping = True
access_provider = ad
ad_gpo_access_control = permissive
ad_gpo_ignore_unreadable = True
""")
                
            with open("/etc/pam.d/common-session","a") as pam_file:
                pam_file.write("""
session required pam_mkhomedir.so skel=/etc/skel umask=0077
""")
            subprocess.call(["systemctl", "restart ", "sssd"])          

            if password_check==0:
                print(_("This computer has been successfully added to the domain."))
        except Exception as e:
            print(e)

    def permit():
        command1="realm permit -a"        
        cmd = subprocess.Popen(command1, shell=True)
        cmd.communicate()

    def leave():
        subprocess.call(["realm", "leave", "-v"])

    if len(sys.argv) > 1:
        if control_lock():
            if sys.argv[1] == "join":
                join(sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5],sys.argv[6])
                permit()
            elif sys.argv[1] == "leave":
                leave()
        else:
            print("lock error")
            sys.exit(1)
    else:
        print("no argument passed")

if __name__ == "__main__":
    main()