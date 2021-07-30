'''BLDR Case Logs download sharefile files via API'''
from common import methods

def main() -> None:
    '''main function'''
    sweep_name:str = "BLDR_Case_Logs"

    try:
        sweep = methods.Sweep(sweep_name, bypass=True, test=False, custom_destination=True)
        sweep.dir_walk(["Archive"])
    except Exception as exception:
        if sweep.bypass:
            methods.send_email(methods.traceback.format_exc(), sweep_name+" Traceback")
        else:
            raise exception

if __name__ == "__main__":
    main()
