'''VALL VMC Transfer'''
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from common import methods

def main(facility:str, bypass:str=None) -> None:
    '''transfer from sftp server'''
    print("Transferring files from SFTP...")
    transfer:object = methods.Transfer(facility)

    check_list:list = transfer.check()

    if not check_list and bypass:
        methods.send_email("VALL VMC Missing CSVs", __doc__)

    for csv in check_list:
        print(csv)
        try:
            name:str = os.path.basename(csv[0])
            mod_time:int = csv[1]
            source_file:os.PathLike = os.path.join(transfer.client['sftp_dir'], name)
            csv:os.PathLike = os.path.join(transfer.root, transfer.client["csv_dir"], name)
            transfer.sftp.get(source_file, csv)
            os.utime(csv, (mod_time, mod_time))
            transfer.track_files(name)
        except Exception as exception:
            if bypass:
                methods.send_email(methods.traceback.format_exc(), __doc__)
                continue
            print(name)
            raise exception

    transfer.sftp.close()
    transfer.transport.close()

if __name__ == "__main__":
    main("VALL_VMC")
