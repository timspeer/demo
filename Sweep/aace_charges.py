'''AACE download sharefile files via API'''
from common import methods

def main() -> None:
    '''main function'''
    sweep_name:str = "AACE_Charges"

    try:
        sweep:object = methods.Sweep(sweep_name, bypass=True, test=False)
        sweep.download_files()
    except Exception as exception:
        if sweep.bypass:
            sweep.send_email(methods.traceback.format_exc(), sweep_name+" Traceback")
        else:
            raise exception

if __name__ == "__main__":
    main()
