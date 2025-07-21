#!/usr/bin/python3

import sys
import signal
import os
from pardus_domain_core import domain_operations

if len(sys.argv) >= 2:
    cmd = sys.argv[1]

    if cmd == "hostname":
        hostname = sys.argv[2].strip()

        domain_operations.config_manager.set_hostname(hostname)

    elif cmd == "join":
        hostname = sys.argv[2].strip()
        domain = sys.argv[3].strip()
        user = sys.argv[4].strip()
        password = sys.argv[5].strip()
        ouaddress = sys.argv[6].strip()
        connection_type = sys.argv[7].strip()

        domain_operations.join(
            hostname,
            domain,
            user,
            password,
            ouaddress,
            connection_type == "sssd",
            connection_type == "winbind",
        )
    elif cmd == "leave":
        username = sys.argv[2].strip()
        password = sys.argv[3].strip()
        is_winbind = True if sys.argv[4].strip() == "winbind" else False

        domain_operations.leave(
            user=username,
            password=password,
            winbind=is_winbind,
            realmd=(not is_winbind),
        )
    elif cmd == "check_domain":
        joined_domain_name = domain_operations.list(realmd=True)

        if joined_domain_name:
            print(f"joined={joined_domain_name}")
            exit(0)

        joined_domain_name = domain_operations.list(winbind=True)
        if joined_domain_name:
            print(f"joined={joined_domain_name}")

    elif cmd == "cancel":
        pid = int(sys.argv[2])

        os.kill(pid, signal.SIGKILL)
