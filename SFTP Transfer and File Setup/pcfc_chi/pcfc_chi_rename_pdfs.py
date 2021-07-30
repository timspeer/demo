'''PCFC CHI Rename PDFs'''
import os
import sys
import re
from datetime import datetime
from fnmatch import fnmatch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

def main(facility:str, bypass:str=None) -> None:
    '''rename pdfs in directory'''
    fp_class:object = methods.FileProcess(facility, sftp=False)

    pdf_dir:os.PathLike = os.path.join(fp_class.root, "PDFs")

    for pdf in os.listdir(pdf_dir):
        try:
            if not fnmatch(pdf, "Date*"):
                continue
            pdf:os.PathLike = os.path.join(pdf_dir, pdf)
            raw:str = methods.pdf_to_text(pdf, 'raw')
            csn:str = re.findall(r'(?<=Contact Serial#:).*', raw)[0].strip()
            csn:str = fp_class.client['client']+fp_class.client['location']+csn
            mrn:str = re.findall(r'(?<=MRN:).*', raw)[0].strip()
            name:str = re.findall(r'(?<=Patient Name\r\n)[\s\S]*?(?=Sex\r\n)', raw)[0].strip()
            name:str = name.replace("\r\n", " ")
            dos:str = re.findall(r'(?<=Encounter Date:).*', raw)[0].strip()
            dos:datetime = datetime.strptime(dos, "%m/%d/%Y").strftime("%Y-%m-%d")
            filename:str = f"DOS_{dos}_NAME_{name}_MRN_{mrn}_CSN_{csn}_.pdf"
            filename:os.PathLike = os.path.join(pdf_dir, filename)
            os.replace(pdf, filename)
        except Exception as exception:
            if bypass:
                methods.send_email(methods.traceback.format_exc(), __doc__)
                continue
            print(pdf)
            raise exception


if __name__ == "__main__":
    main("PCFC_CHI")
