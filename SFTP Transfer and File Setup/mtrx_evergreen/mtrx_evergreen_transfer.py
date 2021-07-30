'''mtrx evergreen transfer'''
import sys
import os
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..')))
from common import methods


def main(facility):
    '''runs the file'''
    fp_class = methods.FileProcess(facility, bypass=True, test=False, day=True)

    check_list = fp_class.check(fp_class.client["sftp_table"], fp_class.client['sftp_dir'], sftp=fp_class.sftp)

    if not check_list:
        methods.send_email("No XMLs have been transfered today", "MTRX Evergreen Missing Files")

    for file in check_list:
        try:
            name = os.path.basename(file[0])
            mod_time = file[1]
            sftp_file = os.path.join(fp_class.client['sftp_dir'], name)
            local_file = os.path.join(fp_class.root, "XML", name)
            fp_class.sftp.get(sftp_file, local_file)
            os.utime(local_file, (mod_time, mod_time))
            print(sftp_file)
            fp_class.track_files(name, fp_class.client['sftp_table'])
        except Exception as exception:
            if fp_class.bypass:
                methods.send_email(file+"\n\n"+traceback.format_exc(), "MTRX Evergreen SFTP Transfer")
                continue
            else:
                print(sftp_file)
                raise exception
   
    fp_class.sftp.close()
    fp_class.transport.close()

if __name__ == "__main__":
    main("MTRX_Evergreen")