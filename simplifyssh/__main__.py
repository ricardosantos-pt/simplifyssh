#!/usr/bin/env python3
import os
from os import path, mkdir
from getpass import getpass
from simplifyssh.ssh import SSH
import simplifyssh.infoOS as info_os
import subprocess
from pathlib import Path


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
                                     shell=info_os.use_shell(),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            _, stderr = sub_p.communicate()
            sub_p.kill()
            if stderr.decode("utf-8") == "\n":
                return id_rsa_path
            else:
                stderr_string = stderr.decode('utf-8').strip('\n')
                print(f"Error creating id_rsa: {stderr_string}\n")
                return create_get_id_rsa(ssh_folder)
    else:
        return create_get_id_rsa(ssh_folder)


def main():
    os_name = info_os.get_os_name()
    username_local = info_os.get_username()
    home_dir = info_os.get_homedir_user()

    print(
        f"SSH install key on remote:\n\nRunning on {os_name} as {username_local}\nHome directory: {home_dir}"
    )

    ssh_folder = create_get_ssh_folder(home_dir)

    print("\nRemote settings:")
    while True:
        try:
            hostname_remote = input("IP remote machine: ")
            username_remote = input("Username: ")
        except KeyboardInterrupt:
            exit()

        ssh = SSH(hostname_remote, username_remote)

        already_logged_in = ssh.already_logged_in()
        if already_logged_in == 1:
            password_remote = getpass("Password: ")
            ssh.set_password(password_remote)
            valide = ssh.validate_password()
            if valide is None:
                print("You had a ssh key already for that ip.")
                print(
                    f"Please remove it and run simplifyssh again:\n\n\tssh-keygen -f {path.join(Path.home(), '.ssh/known_hosts')} -R \"{hostname_remote}\"\n"
                )
                break
            elif not valide:
                print("Wrong ip, username or password. Please enter them again:")
            elif valide:
                print("\nValid Password!")
                id_rsa = create_get_id_rsa(ssh_folder)
                if ssh.create_ssh_folder_on_remote():
                    userhome_remote = ssh.get_user_homedir_from_remote()
                    print(f"User home in the remote machine: {userhome_remote}")
                    if ssh.copy_id_rsa_pub(id_rsa):
                        if ssh.build_authorized_keys():
                            if ssh.already_logged_in(True) == 2:
                                break
        elif already_logged_in == 2:
            print("Already logged in!")
            break


if __name__ == "__main__":
    main()
