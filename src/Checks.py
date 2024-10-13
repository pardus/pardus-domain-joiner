#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import subprocess
import apt

def main():

    def list():
        cache = apt.cache.Cache()
        package = cache["realmd"]

        if not package.is_installed:
            package.mark_install()
            cache.commit()

        command = subprocess.check_output(["realm", "list"]).decode("utf-8")

        with open("/tmp/realmlist", "w") as realmfile:
            realmfile.write(command)

    def id_check(id):
        idfile = open("/tmp/idcheck", "w")
        command = subprocess.check_output(["id", id]).decode("utf-8")
        idfile.write(command)

    if len(sys.argv) > 1:
        match sys.argv[1]:
            case "list":
                list()
            case "id_check":
                id_check(sys.argv[2])
            case _:
                print("arg error")
                sys.exit(1)
    else:
        print("no argument passed")

if __name__ == "__main__":
    main()
