#!/usr/bin/python3

import sys
import signal
import os
from pardus_domain_core import domain_operations

if len(sys.argv) >= 2:
    cmd = sys.argv[1]

    if cmd == "hostname":
        hostname = sys.argv[2]

        domain_operations.config_manager.set_hostname(hostname)

    elif cmd == "join":
        hostname = sys.argv[2]
        domain = sys.argv[3]
        user = sys.argv[4]
        password = sys.argv[5]
        ouaddress = sys.argv[6]
        connection_type = sys.argv[7]

        domain_operations.join(
            hostname,
            domain,
            user,
            password,
            ouaddress,
            None,
            connection_type == "sssd",
            connection_type == "winbind",
        )
    elif cmd == "leave":
        domain_operations.leave(realmd=True)
    elif cmd == "check_domain":
        joined_domain_name = domain_operations.list(realmd=True)

        if joined_domain_name:
            print(joined_domain_name)
            exit(0)

        joined_domain_name = domain_operations.list(winbind=True)
        if joined_domain_name:
            print(joined_domain_name)
    elif cmd == "cancel":
        pid = int(sys.argv[2])

        os.kill(pid, signal.SIGKILL)
