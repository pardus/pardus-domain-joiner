import argparse
import getpass
import os
import locale
from locale import gettext as _
import subprocess

# translation constants:
APPNAME =  "domain-joiner-cli"
TRANSLATIONS_PATH =  "/usr/share/locale"
SYSTEM_LANGUAGE =  os.environ.get("LANG")

# Translation functions:
locale.bindtextdomain(APPNAME, TRANSLATIONS_PATH)
locale.textdomain(APPNAME)
locale.setlocale(locale.LC_ALL, SYSTEM_LANGUAGE)

def main():
    parser = argparse.ArgumentParser(description=
                                 "This app is simple domain joiner CLI application.")
    parser.add_argument('-j', '--join', action="store_true", help=_('joins your computer to the domain'))
    parser.add_argument('-d', '--domain', action="store", help=_('domain name'))
    parser.add_argument('-c', '--computer', action="store", help=_('computer name'))
    parser.add_argument('-u', '--username', action="store", help=_('domain User name'))
    parser.add_argument('-ou', '--organizationalunit', action="store",metavar='"ou=Computers"', help=_('organizational unit'))
    parser.add_argument('-p', '--password', action="store", help=_('password of domain user'))
    parser.add_argument('-l', '--leave', action="store_const",const="leave", help=_('to leaves domain'))
    parser.add_argument('--list', action="store_const",const="list", help=_('lists domain Information'))
    parser.add_argument("-id", '--idcheck', action="store", help=_('shows the users ids in the domain'))

    args = parser.parse_args()
    # print(args.join)
    domain_name = str(args.domain)
    computer_name = str(args.computer)
    username = str(args.username)
    ou_location = str(args.organizationalunit)
    password = str(args.password)
    idname = str(args.idcheck)

    if args.idcheck:
        subprocess.call(["id", idname])

    if args.list:
        subprocess.call(["sudo", "realm", "list"])

    if args.leave:
        subprocess.call(["sudo", "realm", "leave", "-v" ])
        print(_("Successfully left to the domain."))
        print(_("Please restart your computer"))

    if args.join:
        # print("please enter other command")
        if  args.domain or args.computer or args.username:
                domain_name = str(args.domain)
                computer_name = str(args.computer)
                username = str(args.username)
                ou_location = str(args.organizationalunit)
                password = str(args.password)
                if domain_name =="None" or computer_name == "None" or username=="None":
                    print(_("error: the following arguments are required: --domain/-d, --computer/-c, --username/-u"))
                else:
                    if(password == "None"):
                        domain_password = getpass.getpass(_("Enter the password of domain: "))
                    else:
                        domain_password = password

                    if(ou_location == "None"):
                        fulldn = domain_name.replace(".",",dc=")
                        ouaddress = "cn=Computers,dc="+fulldn
                    else:
                        fulldn = domain_name.replace(".",",dc=")
                        ouaddress = ou_location + ",dc="+fulldn

                    try:
                        print(_("Joining Domain..."))
                        subprocess.call(["sudo", "python3", "Actions.py","join", computer_name, domain_name, username,domain_password,ouaddress])
                        print(_("Please reboot your computer!"))
                    except Exception as err:
                        print(err)
        

if __name__ == "__main__":
    main()

