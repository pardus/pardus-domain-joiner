import argparse
import getpass
import os
import sys
import locale
from locale import gettext as _
import subprocess

# translation constants:
APPNAME = "domain-joiner"
TRANSLATIONS_PATH = "/usr/share/locale"
SYSTEM_LANGUAGE = os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

def join(computer_name,domain_name,username,password,ou_location,smb_settings):
    if domain_name =="None" or computer_name == "None" or username=="None":
        print(_("Error: The following arguments are required!"))
        print(_("Please enter other commands:\n"), 
               _("\t\t [-d/--domain DOMAIN] [-c/--computer COMPUTER]\n"),
               _("\t\t [-u/--username USERNAME] [--organizationalunit \"ou=Computers\"]\n"),
               _("\t\t [--password PASSWORD]\n"))
    else:
        if(password == "None"):
            domain_password = getpass.getpass(_("Enter the password of domain: "))
        else:
            domain_password = password

        fulldn = ", dc=" + domain_name.replace(".",",dc=")
        if(ou_location == "None"):
            ouaddress = "cn=Computers" + fulldn
        else:
            ouaddress = ou_location + fulldn
                        
        try:
            print(_("Joining Domain..."))
            subprocess.call(["sudo", "python3", os.path.dirname(os.path.abspath(__file__)) + "/Actions.py","join", computer_name, domain_name, username,domain_password,ouaddress,smb_settings])
        except Exception as err:
            print(err)

def check_domain_list(domain):  
    output = subprocess.check_output(["sudo", "realm", "list"], stderr=subprocess.STDOUT, text=True)

    if domain in output:
        return True
    else:
        return False


def main():
    parser = argparse.ArgumentParser(
        description=_("This application is a simple CLI application that joins your computer to the domain or leaves it from the domain.")
        )
    
    parser.add_argument('-j', '--join', action="store_true", help=_('joins your computer to the domain'))
    parser.add_argument('-d', '--domain', action="store", help=_('domain name'))
    parser.add_argument('-c', '--computer', action="store", help=_('computer name'))
    parser.add_argument('-u', '--username', action="store", help=_('domain user name'))
    parser.add_argument('-ou', '--organizationalunit', action="store",metavar='"ou=Computers"', help=_('organizational unit'))
    parser.add_argument('-p', '--password', action="store", help=_('password of domain user'))
    parser.add_argument('-s', '--samba-settings', action="store_true", help=_('adds samba settings when joining your computer to the domain, it is used with join'))
    parser.add_argument('-l', '--leave', action="store_const",const="leave", help=_('to leave the domain'))
    parser.add_argument('--list', action="store_const",const="list", help=_('lists domain information'))
    parser.add_argument("-id", '--idcheck', action="store", help=_('shows the users ids in the domain'))
    parser.add_argument("-dis", '--discover', action="store_const", const="discover", help=_('discovers whether the domain is reachable or not'))

    args = parser.parse_args()
    
    domain_name = str(args.domain)
    computer_name = str(args.computer)
    username = str(args.username)
    ou_location = str(args.organizationalunit)
    password = str(args.password)
    idname = str(args.idcheck)
    
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    else:
        if args.idcheck:
            subprocess.call(["id", idname])

        if args.discover:
            subprocess.call(["sudo", "realm", "discover"])

        if args.list:
            subprocess.call(["sudo", "realm", "list"])
            
        if args.leave:
            subprocess.call(["sudo", "realm", "leave", "-v" ])
            print(_("Successfully left the domain."))
            print(_("Please restart your computer"))

        if args.join:
            domain_name = str(args.domain)
            computer_name = str(args.computer)
            username = str(args.username)
            ou_location = str(args.organizationalunit)
            password = str(args.password)

            smb_settings = "True" if args.samba_settings else "False"

            cl = check_domain_list(domain_name)
            if cl:
                print(_("Already joined to this domain"))
            else:
                join(computer_name,domain_name,username,password,ou_location,smb_settings)


if __name__ == "__main__":
    main()