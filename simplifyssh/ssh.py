import socket
import subprocess
from typing import Tuple
from simplifyssh.randomString import randomString
from simplifyssh.infoOS import use_shell
import os
from paramiko import SSHClient, AutoAddPolicy, BadHostKeyException
from pathlib import Path
from enum import Enum
from os import path


class SSHExecuteResponse(Enum):
    OK = 1
    ERROR = 2
    BADHOSTKEY = 3


class OSRemote(Enum):
    WINDOWS = 1
    LINUX = 2


class SSH:
    __hostname = None
    __username = None
    __password = None
    __os_remote: OSRemote = None
    __user_home_path: str = None

    def __init__(self, hostname, username):
        self.__hostname = hostname
        self.__username = username

    def set_password(self, password):
        self.__password = password

    def __isOpen(self, ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.settimeout(4)
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except Exception:
            return False

    def already_logged_in(self, after_build_authorization_keys: bool = False):
        """
            Verify if user is already logged via authorized_keys
        """
        random_string = randomString(15)
        if self.__isOpen(self.__hostname, 22):
            with subprocess.Popen((f"ssh -oConnectTimeout=8 -oPasswordAuthentication=No {self.__username}@{self.__hostname} echo {random_string}").split(),
                                  shell=use_shell(),
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE) as sub_p:
                stdout, stderr = sub_p.communicate()
            stdout_string = stdout.decode("utf-8").strip("\n").strip("\r")
            stderr_string = stderr.decode("utf-8").strip("\n").strip("\r")
        else:
            print("Cannot connect to this ip/port!")
            return 0

        if self.__os_remote == OSRemote.WINDOWS and after_build_authorization_keys and stdout_string != randomString:
            print("""
            Please comment in C:\\ProgramData\\ssh\\sshd_config:
                # Match Group administrators                                                    
                #       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys  
            Then Stop-Service sshd and Start-Service sshd in powershell admin on windows remote machine.
            """)
            return 2

        if stdout_string == random_string:
            print("Connection done!")
            return 2
        else:
            return 1

    def __execute_command(self, command) -> Tuple[SSHExecuteResponse, str]:
        """
            Execute command on remote
        """
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(self.__hostname, username=self.__username, password=self.__password)

            _, stdout, stderr = client.exec_command(command)

            stdout_text = stdout.read().decode().replace("\r", "")
            stderr_text = stderr.read().decode().replace("\r", "")

            if stderr_text != "":
                return (SSHExecuteResponse.ERROR, stdout_text)

            if stderr_text == "":
                return (SSHExecuteResponse.OK, stdout_text)
        except BadHostKeyException as e:
            client.close()
            return (SSHExecuteResponse.BADHOSTKEY, e)
        except Exception:
            client.close()
        finally:
            client.close()

        return (SSHExecuteResponse.ERROR, None)

    def validate_password(self) -> bool:
        """
            Validate password on remote
        """
        random_string = randomString(15)

        result, stdout = self.__execute_command(f"echo {random_string} && echo %OS%")
        list_stdout = str(stdout).split("\n")
        list_stdout = [i.replace(" ", "") for i in list_stdout]
        if result == SSHExecuteResponse.OK and list_stdout[0] == random_string:
            if(list_stdout[1] == "Windows_NT"):
                self.__os_remote = OSRemote.WINDOWS
            else:
                self.__os_remote = OSRemote.LINUX
            return True
        elif result == SSHExecuteResponse.ERROR:
            return False
        elif result == SSHExecuteResponse.BADHOSTKEY:
            return False

    def create_ssh_folder_on_remote(self):
        """
            Create .ssh/temp folder on remote
        """
        print("\nTrying to create ssh folder on remote!")
        if(self.__os_remote == OSRemote.LINUX):
            result, stdout = self.__execute_command("mkdir -p ~/.ssh/temp")
        else:
            result, stdout = self.__execute_command("powershell New-Item -ItemType Directory -Force -Path ~/.ssh/temp")

        if result == SSHExecuteResponse.OK:
            print("SSH path created with success!")
            return True
        elif result == SSHExecuteResponse.ERROR:
            print("Couldn't create ssh folder on remote!")
            return False

    def __copy_file(self, file_path, remotefilepath):
        """
            Copy file from local to remote
        """
        try:
            client = SSHClient()
            client.set_missing_host_key_policy(AutoAddPolicy())
            client.load_system_host_keys()
            client.connect(self.__hostname, username=self.__username, password=self.__password)

            sftp = client.open_sftp()
            sftp.put(file_path, remotefilepath)
            sftp.close()

            return True
        except BadHostKeyException as e:
            pass
        finally:
            client.close()

        return False

    def get_user_homedir_from_remote(self):
        """
            Get $HOME from remote machine
        """
        if(self.__os_remote == OSRemote.WINDOWS):
            result, stdout = self.__execute_command("echo %USERPROFILE%")
        else:
            result, stdout = self.__execute_command("echo $HOME")

        home_path_remote = str(stdout).split("\n")[0].replace("\r", "")

        self.__user_home_path = home_path_remote

        return home_path_remote

    def copy_id_rsa_pub(self, id_rsa_path):
        """
            Copy the id_rsa.pub to the remote .ssh/temp folder
        """
        id_rsa_path_pub = id_rsa_path + ".pub"
        id_rsa_path_pub_remote = join_path(self.__user_home_path, "/.ssh/temp/id_rsa.pub")

        result = self.__copy_file(id_rsa_path_pub, id_rsa_path_pub_remote)

        if not result:
            print("Couldn't copy id_rsa.pub")

        return result

    def build_authorized_keys(self):
        """
            Concatenate id_rsa.pub with the authorized_keys and delete .ssh/temp
        """

        if(self.__os_remote == OSRemote.WINDOWS):
            id_rsa_path_remote = join_path(self.__user_home_path, "/.ssh/temp/id_rsa.pub")
            authorizated_keys_path_remote = join_path(self.__user_home_path, "/.ssh/authorized_keys")
            result, std = self.__execute_command(f"powershell type {id_rsa_path_remote} >> {authorizated_keys_path_remote}")
        else:
            result, std = self.__execute_command("cat ~/.ssh/temp/id_rsa.pub >> ~/.ssh/authorized_keys")

        if result == SSHExecuteResponse.OK:
            if(self.__os_remote == OSRemote.LINUX):
                result, _ = self.__execute_command("rm -rf ~/.ssh/temp")
            elif(self.__os_remote == OSRemote.WINDOWS):
                id_rsa_path_remote = join_path(self.__user_home_path, "/.ssh/temp")
                result, _ = self.__execute_command(f"rd /S /Q {id_rsa_path_remote}")

            return True

        print("Couldn't conclude ssh configuration")
        return False


def join_path(initial_path: str, path: str):
    if not initial_path.startswith("/"):
        path = path.replace("/", "\\")

    return initial_path + path
