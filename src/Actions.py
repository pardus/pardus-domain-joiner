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
            if os.path.isfile("/etc/krb5.conf"):
                print(_("Packages are installed."))
            else:
                print(_("Packages are not installed."))
                exit()

            # to check file /etc/hostname 
            hostname_file = "/etc/hostname"
            with open(hostname_file, 'r') as file:
                current_hostname = file.readline().strip()
                print(_("checking /etc/hostname file..."))
                if comp_name+"."+domain not in current_hostname:
                    print(_("added domain name to /etc/hostname file"))
                    with open(hostname_file, 'w') as file:
                        new_hostname = "{}.{}".format(comp_name,domain)
                        file.write(new_hostname)
                else:
                    print(_("done"))
                        
            # to check file /etc/hosts 
            hosts_file = "/etc/hosts"
            with open(hosts_file, 'r') as file:
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
            with open(hosts_file, 'w') as file:
                file.writelines(new_hosts_file)
            if domain_exists:
                print(_("done"))
            else:
                print(_("added domain name to /etc/hosts file"))
                     
            result = subprocess.run(["realm", "discover"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if result.returncode != 0:
                print(_("Not reachable, check your DNS address"), file=sys.stdout)
                exit()
            else:
                output_lines = result.stdout.split('\n')

                if len(output_lines)>0:
                    if domain == output_lines[0]:
                        print(_("joining the domain..."))
                    else:
                        print(_("Not reachable, check your DNS address"), file=sys.stdout)
                        exit()
            
            command = "realm join -v --computer-ou=\""+ouaddress+"\" --user=\""+user+"@"+domain.upper()+"\" "+domain.lower()
            proc = subprocess.Popen([command],stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
            proc.communicate(passwd.encode('utf-8'))

            password_check = proc.returncode
            if password_check == 1:
                print(_("Domain username or password check: False"), file=sys.stdout)

            # to check and rewrite file /etc/sssd/sssd.conf
            sssd_file = "/etc/sssd/sssd.conf"
            settings = {
                "use_fully_qualified_names": "False",
                "ad_gpo_access_control":"permissive",
                "ad_gpo_ignore_unreadable":"True"
            }
            if os.path.exists(sssd_file):
                new_sssd_conf = []
                with open(sssd_file,"r") as sfile:
                    contents = sfile.readlines()

                    for line in contents:
                        for key, value in settings.items():
                            if line.strip().startswith(f"{key}"):
                                if value not in line:
                                    new_sssd_conf.append(f"{key} = {value}\n")
                                break
                        else:
                            new_sssd_conf.append(line)
                # to add missing variables
                for key,value in settings.items():
                    if f"{key} = {value}\n" not in new_sssd_conf:
                        new_sssd_conf.append(f"{key} = {value}\n")

                with open(sssd_file,"w") as sfile:
                    for item in new_sssd_conf:
                        sfile.write(item)
            else:
                with open(sssd_file,"w") as sfile:
                    sfile.write(
                        """
[sssd]
domains = {}
config_file_version = 2
services = nss, pam

[domain/{}]
default_shell = /bin/bash
ad_server = {}
krb5_store_password_if_offline = True
cache_credentials = True
krb5_realm ={}
realmd_tags = manages-system joined-with-adcli 
id_provider = ad
fallback_homedir = /home/%u@%d
ad_domain ={}
use_fully_qualified_names = False
ldap_id_mapping = True
access_provider = ad
ad_gpo_access_control = permissive
ad_gpo_ignore_unreadable = True
""".format(domain,domain,domain,domain.upper(),domain)
                    )
            subprocess.call(["chmod", "600", sssd_file])   
            subprocess.call(["pam-auth-update", "--enable ", "pardus-pam-config"],env={**os.environ, 'DEBIAN_FRONTEND': 'noninteractive'}) 
            subprocess.call(["systemctl", "restart ", "sssd"])          

            if password_check==0:
                print(_("This computer has been successfully added to the domain."))
        except Exception as e:
            print(e)

    def permit():
        subprocess.call(["realm","permit","-a"])

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