'''PCFC CHI Transfer from SFTP'''
import os
import sys
from datetime import datetime
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

class Main(methods.Transfer):
    '''transfer from sftp'''
    def __init__(self, facility, bypass:str=None):
        print(__doc__)
        super().__init__(facility)
        self.bypass:str = bypass
        self.pdf_list:list = self.check(self.client['sftp_pdfs'])
        self.csv_list:list = self.check(self.client['sftp_csvs'])
        self.date:datetime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.main()

    def download(self, arg_list:list, folder:str, source:str) -> None:
        '''download files'''
        item:list
        for item in arg_list:
            try:
                name:str = os.path.basename(item[0])
                mod_time:datetime = item[1]
                if datetime.fromtimestamp(mod_time) > self.date:
                    continue
                source_file:os.PathLike = os.path.join(source, name)
                dest_file:os.PathLike = os.path.join(self.root, folder, name)
                self.sftp.get(source_file, dest_file)
                os.utime(dest_file, (mod_time, mod_time))
                self.track_files(name)
                print(name)
            except Exception as exception:
                if self.bypass:
                    methods.send_email(name+"\n\n"+traceback.format_exc(), __doc__)
                    continue
                print(name)
                raise exception

    def main(self) -> None:
        '''main trigger'''
        if not self.pdf_list and self.bypass:
            methods.send_email(
                "No PDFs were pulled from the SFTP Server",
                "PCFC CHI Missing PDFs"
                )
        self.download(self.pdf_list, self.client["pdf_dir"], self.client['sftp_pdfs'])

        if not self.csv_list and self.bypass:
            methods.send_email(
                "No CSV was pulled from the SFTP Server",
                "PCFC CHI Missing CSVs"
                )
        self.download(self.csv_list, self.client["csv_dir"], self.client['sftp_csvs'])

        self.sftp.close()
        self.transport.close()

if __name__ == "__main__":
    Main("PCFC_CHI")
