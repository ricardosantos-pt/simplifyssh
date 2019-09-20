#!/usr/bin/env python3
import os
from os import path, mkdir
from getpass import getpass
from .ssh import SSH
from .infoOS import *
import subprocess


def create_get_ssh_folder(root_directory):
    """
    Create ssh folder on local user
    """
    ssh_folder = path.join(root_directory, ".ssh")
    if path.exists(ssh_folder):
        print(f".ssh folder in {ssh_folder}")
    else:
        mkdir(ssh_folder)
        print(f".ssh folder created at {ssh_folder}")

    return ssh_folder


def create_get_id_rsa(ssh_folder):
    """
    Create or choose an id_rsa 
    """
    print("\nID RSA configuration:\n(Attention we assume that the pub key from the id_rsa will be id_rsa.pub)")
    id_rsa_path = path.join(ssh_folder, "id_rsa")
    answer = input(
        f"Do you want to use the default 'id_rsa' at {id_rsa_path}? (y/n): "
    )

    if answer in ["y", "n", "Y", "N"]:
        if answer in ["n", "N"]:
            print("You want to change the default path for the 'id_rsa' key. Please enter the path or enter b to go back")
            path_temp = None
            while True:
                path_temp = input("Path: ")
                if path_temp in ["b", "B"]:
                    return create_get_id_rsa(ssh_folder)
                else:
                    if path.exists(path_temp):
                        id_rsa_path = path_temp
                    else:
                        print("Path don't exist! Try other")

        if path.exists(id_rsa_path):
            return id_rsa_path
        else:
            email = input("Email for ssh key: ")
            sub_p = subprocess.Popen(["ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email, "-P", "", "-f", id_rsa_path],
                                     shell=True,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            _, stderr = sub_p.communicate()
            sub_p.kill()
            if stderr.decode("utf-8") == "":
                return id_rsa_path
            else:
                stderr_string = stderr.decode('utf-8').strip('\n')
                print(f"Error creating id_rsa: {stderr_string}\n")
                return create_get_id_rsa(ssh_folder)
    else:
        return create_get_id_rsa(ssh_folder)


def main():
    os_name = get_os_name()
    username_local = get_username()
    home_dir = get_homedir_user()

    print(
        f"SSH install key on remote:\n\nRunning on {os_name} as {username_local}\nHome directory: {home_dir}"
    )

    ssh_folder = create_get_ssh_folder(home_dir)

    print("\nRemote settings:")
    while True:
        hostname_remote = input("IP remote machine: ")
        username_remote = input("Username: ")
        ssh = SSH(hostname_remote, username_remote)

        if ssh.already_logged_in():
            password_remote = getpass("Password: ")
            ssh.set_password(password_remote)
            if not ssh.validate_password():
                print("Wrong ip, username or password. Please enter them again:")
            else:
                print("\nValid Password!")
                id_rsa = create_get_id_rsa(ssh_folder)
                if ssh.create_ssh_folder_on_remote():
                    if ssh.copy_id_rsa_pub(id_rsa):
                        if ssh.build_authorized_keys():
                            if ssh.already_logged_in():
                                print("Connection done!")
                                break
                            else:
                                print("Please try again later something happen")
                        else:
                            print("Couldn't conclude ssh configuration")
                    else:
                        print("Couldn't copy id_rsa.pub")
                else:
                    print("Couldn't create ssh folder")
        else:
            print("You are already logged in!")
            break


if __name__ == "__main__":
    main()
