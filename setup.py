#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess

from setuptools import setup, find_packages


 	
def create_mo_files():
    podir = "po"
    mo = []
    for po in os.listdir(podir):
        if po.endswith(".po"):
            os.makedirs("{}/{}/LC_MESSAGES".format(podir, po.split(".po")[0]), exist_ok=True)
            mo_file = "{}/{}/LC_MESSAGES/{}".format(podir, po.split(".po")[0], "domain-joiner.mo")
            msgfmt_cmd = 'msgfmt {} -o {}'.format(podir + "/" + po, mo_file)
            subprocess.call(msgfmt_cmd, shell=True)
            mo.append(("/usr/share/locale/" + po.split(".po")[0] + "/LC_MESSAGES",
                       ["po/" + po.split(".po")[0] + "/LC_MESSAGES/domain-joiner.mo"]))
    return mo


changelog = 'debian/changelog'
if os.path.exists(changelog):
    head = open(changelog).readline()
    try:
        version = head.split("(")[1].split(")")[0]
    except:
        print("debian/changelog format is wrong for get version")
        version = ""
    f = open('src/__version__', 'w')
    f.write(version)
    f.close()

data_files = [
    ("/usr/bin/", ["domain-joiner","domain-joiner-cli"]),
    ("/usr/share/applications/", ["data/tr.org.pardus.domain-joiner.desktop"]),
    ("/usr/share/pam-configs/", ["data/pardus-pam-config"]),
    ("/usr/share/locale/tr/LC_MESSAGES/", ["po/tr/LC_MESSAGES/domain-joiner.mo"]),
    ("/usr/share/pardus/domain-joiner/src", [
        "src/MainWindow.py", 
        "src/DomainJoinerCli.py", 
        "src/Actions.py","src/Checks.py",
        "src/__version__"
      ]),
    ("/usr/share/pardus/domain-joiner/data", [
        "data/pardus-domain-joiner.svg"
        ]),
    ("/usr/share/pardus/domain-joiner/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/polkit-1/actions", ["data/tr.org.pardus.pkexec.domain-joiner.policy"]),
    ("/usr/share/icons/hicolor/scalable/apps/", ["data/pardus-domain-joiner.svg"])
]

setup(
    name="domain-joiner",
    version=version,
    packages=find_packages(),
    scripts=["domain-joiner","domain-joiner-cli"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Büşra ÇAĞLIYAN",
    author_email="busra.cagliyan@pardus.org.tr",
    description="This application is a simple ui/cli application that joins your computer to the domain or leaves it from the domain.",
    license="GPLv3",
    keywords="domain joiner",
    url="https://www.pardus.org.tr",
)