'''convert pdf to text'''
import os
import subprocess

def pdf_to_text(pdf:os.PathLike, output_format:str, nopgbrk:bool=False, output:str="-") -> str:
    '''uses pdftotext to convert pdf to text'''
    exe:os.PathLike = os.path.join(os.path.dirname(__file__), "pdftotext.exe")
    arg_list:list = [
        exe, #program name
        f"-{output_format}", #argument for output ie layout/table/simple/raw
        pdf, #pdf to read
        output #forces output to stdout otherwise it would go to file
    ]
    if nopgbrk:
        arg_list.insert(2, "-nopgbrk")

    result:str = subprocess.check_output(arg_list).decode("iso-8859-1")
    return result
