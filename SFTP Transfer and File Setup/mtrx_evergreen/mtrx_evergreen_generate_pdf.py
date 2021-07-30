'''generate the pdf'''
import os
import PyPDF2
import io
import base64
import pathlib
from PIL import Image


def main(root, anes_path, encounter_dict):
    '''generate file from bytes'''
    dos = encounter_dict['DOS'].strftime('%Y-%m-%d')
    csn = encounter_dict['CSN']
    mrn = encounter_dict['MRN']
    lname = encounter_dict['LName']
    fname = encounter_dict['FName']
    name_ = f"DOS_{dos}_CSN_{csn}_MRN_{mrn}_{lname}, {fname}.pdf"
    target_name = os.path.join(anes_path, name_)

    if os.path.exists(target_name):
        return target_name

    node = root.find("./case/case-info")
    files = node.findall(".//file-contents")
    pdf_path = os.path.join(pathlib.Path(__file__).parent.absolute(), "pdfs")
    if not os.path.exists(pdf_path):
        os.makedirs(pdf_path)
    for idx, file in enumerate(files):
        filename = os.path.join(pdf_path, f"{idx}.pdf")
        writer = PyPDF2.PdfFileWriter()
        decoded = base64.b64decode(file.text)
        try:
            reader = PyPDF2.PdfFileReader(io.BytesIO(decoded))
            for page in range(reader.numPages):
                writer.addPage(reader.getPage(page))
            with open(filename, 'wb') as outfile:
                writer.write(outfile)
        except PyPDF2.utils.PdfReadError:
            image = Image.open(io.BytesIO(decoded))
            image.save(filename)

    

    file_list = sorted(os.listdir(pdf_path))
    file_list = [os.path.join(pdf_path, item) for item in file_list]
    merger = PyPDF2.PdfFileMerger()
    for pdf in file_list:
        merger.append(pdf, 'rb')
    with open(target_name, 'wb') as outfile:
        merger.write(outfile)
    merger.close()
    for pdf in file_list:
        os.remove(pdf)

    return target_name