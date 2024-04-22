#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import apt

def main():

    def list():
        cache = apt.cache.Cache()
        pagkage = cache["realmd"]

        if not pagkage.is_installed:
            pagkage.mark_install()
            cache.commit()
        command = subprocess.check_output(["realm", "list"]).decode("utf-8")

        with open("/tmp/realmlist", "w") as realmfile:
            realmfile.write(command)

    def id_check(id):
        command = subprocess.check_output(["id", id]).decode("utf-8")
        with open("/tmp/idcheck", "w") as idfile:
            idfile.write(command)

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list()
        elif sys.argv[1] == "id_check":
            id_check(sys.argv[2])
        else:
            print("arg error")
            sys.exit(1)
    else:
        print("no argument passed")

if __name__ == "__main__":
    main()