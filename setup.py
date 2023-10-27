#!/usr/bin/env python3
from setuptools import setup, find_packages, os
from shutil import copyfile

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
    ("/usr/share/applications/", ["tr.org.pardus.domain-joiner.desktop"]),
    ("/usr/share/pam-configs/", ["pardus-pam-config"]),
    ("/usr/share/locale/tr/LC_MESSAGES/", ["po/tr/LC_MESSAGES/domain-joiner.mo"]),
    ("/usr/share/pardus/domain-joiner/src", ["src/MainWindow.py", "src/Actions.py","src/Checks.py","src/__version__"]),
    ("/usr/share/pardus/domain-joiner/ui", ["ui/MainWindow.glade"]),
    ("/usr/share/polkit-1/actions", ["tr.org.pardus.pkexec.domain-joiner.policy"])
]

setup(
    name="domain-joiner",
    version=version,
    packages=find_packages(),
    scripts=["domain-joiner"],
    install_requires=["PyGObject"],
    data_files=data_files,
    author="Büşra ÇAĞLIYAN",
    author_email="busra.cagliyan@pardus.org.tr",
    description="UI application that helps to joins or leaves your computer to the domain",
    license="GPLv3",
    keywords="domain joiner",
    url="https://www.pardus.org.tr",
)