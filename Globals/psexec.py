'''run script remotely'''
import os
import sys
import subprocess
import password_encryption

def psexec(computer_name:os.PathLike, script_target:os.PathLike, username:str="#REMOVED#", wait:bool=False):
    '''uses psexec to command remotely'''
    password:str = password_encryption.get_password(username,  "Network")
    exe:os.PathLike = r'#REMOVED#'
    args:list = [
        exe,
        computer_name,
        "-u", username,
        "-p", password,
        "-i",
        "1",    # this is the session ID that may need to be adjusted after claims resets/reboots
        "-d",
        r'C:\Users\SMI_Admin\AppData\Local\Programs\Python\Python37\pythonw.exe',
        script_target
    ]
    if wait:
        del args[args.index("-d")]
    subprocess.call(args)

if __name__ == "__main__":
    psexec(sys.argv[1], sys.argv[2])
