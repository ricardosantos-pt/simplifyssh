import os
import platform
from getpass import getuser
from pathlib import Path


def get_os_name():
    """
        get OS name and version
    """
    if platform.system() == "Windows":
        return f"{platform.system()} {platform.release()}"
    elif platform.system() == "MacOS":
        return f"{platform.system()} {platform.mac_ver()}"
    elif platform.system() == "Linux":
        name, version, *_ = platform.linux_distribution()
        return f"{platform.system()} - {name} {version}"
    else:
        return f"{platform.system()}"


def get_username():
    """
        get username
    """
    return getuser()


def get_homedir_user():
    """
        get path from local user
    """
    return Path.home()


def use_shell():
    if platform.system() == "Windows":
        return True
    else:
        return False
