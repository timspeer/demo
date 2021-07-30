'''BLDR BCH Webscrape'''
import os
import sys
from fnmatch import fnmatch
from datetime import datetime
import subprocess
import PyPDF2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common import methods

class Main(methods.Webscrape):
    '''class for webscraping'''
    def __init__(self, site:str, kiosk:bool=True,
                 browser_session:bool=True, browser_quit:bool=True):
        super().__init__(site, kiosk, browser_session)
        self.conn:object = self.sql_connection()
        self.record_list:list = self.generate_query()
        self.root:os.PathLike = os.path.join(self.common["server"], self.specific["root"])
        self.patient:dict = dict()
        self.bldr_sftp:os.PathLike = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            '..',
            '..',
            "SFTP Transfer and File Setup",
            self.specific['finish'])
        )
        self.main()
        if browser_quit:
            self.browser.quit()

    def generate_query(self) -> list:
        '''generate list'''
        statement:list = [
            "SELECT MRN, DOS, LName, FName, DOB, Sex, CSN FROM #REMOVED#",
            "WHERE Client = :client AND Location = :location",
            "AND Filename is NULL AND DOB IS NOT NULL"
        ]
        query_text:str = methods.sqlalchemy.text(" ".join(statement)) #Sanitized
        query:set = self.conn.execute(
            query_text,
            client=self.specific["client"],
            location=self.specific["location"]
            )
        query:list = [dict(row) for row in query]
        return query

    def login(self) -> None:
        '''login to website'''
        self.browser.get(self.specific["url"])
        self.key('//*[@id="Account_ID"]', self.username)
        self.key('//*[@id="Account_Password"]', self.password)
        self.click('//*[@id="LoginButton"]')

    def find_patient(self) -> str:
        '''find patient record'''
        self.switch('//*[@id="sHeaderFrame"]')
        self.click('//*[@id="patientTab"]')

        try:
            dob:str = self.patient["DOB"].strftime("%#m/%#d/%Y")
        except AttributeError:
            dob:str = datetime.strptime(self.patient["DOB"], "%Y-%m-%d").strftime("%#m/%#d/%Y")
        sex:str = self.patient["Sex"]
        lname:str = self.patient["LName"]

        self.switch('//*[@id="sBodyFrame"]')
        self.click('//*[contains(text(),  "Search All Patients")]')
        self.key('//*[@id="txtName"]', lname)
        self.key('//*[@id="txt2061"]', self.patient["MRN"]) #MRN
        self.key('//*[@id="txt110"]', dob) #DOB
        self.click(f'//*[text()="{sex}"]') #sex dropdown
        self.click('//*[@id="tbBottombutton1"]') #search button

        self.switch('//*[@id="sBodyFrame"]', '//*[@id="frameResults"]') #search results frame

        try:
            self.wait(f'//*[@id="DefaultWTableID"]//*[text()="{dob}"]', 3)
        except methods.TimeoutException:
            self.click('//*[@id="lnktblBigButton_1"]') #cancel
            return "No Match"
        self.click(f'//*[@id="DefaultWTableID"]//*[contains(text(), "{lname.upper()}")]')

        self.switch('//*[@id="sBodyFrame"]', '//*[@id="frameFAConfirmation"]') #search results frame
        self.click('//*[@id="selReason5"]') #reason=other
        self.key('//*[@id="txtComment"]', "Billing")
        self.click('//*[@id="tblConfirmbutton1"]') #accept
        return None

    def download_pdfs(self) -> None:
        '''download patient pdfs'''
        try:
            dos:str = self.patient["DOS"].strftime("%m/%d/%Y")
        except AttributeError:
            dos:str = datetime.strptime(self.patient["DOS"], "%Y-%m-%d").strftime("%m/%d/%Y")
        self.switch('//*[@id="sMenuFrame"]')
        try:
            self.click('//*[@id="navContainer"]//*[contains(text(), "SnapShot")]', 3) #snapshot
        except methods.ElementClickInterceptedException:
            try: #break the glass
                self.switch()
                self.click('//*[button]/*[text()="Open Record"]', 3)
                self.switch('//*[@id="sMenuFrame"]')
                self.click('//*[@id="navContainer"]//*[contains(text(), "SnapShot")]') #snapshot
            except methods.TimeoutException:
                self.switch('//*[@id="BTGiframeLB"]')
                self.click('//*[@id="Reason"]/option[2]') #billing dropdown
                self.key('//*[@id="Password"]', self.password)
                self.click('//*[@id="BTGToolBarbutton1"]') #accept
                self.switch('//*[@id="sMenuFrame"]')
                self.click('//*[@id="navContainer"]//*[contains(text(), "SnapShot")]') #snapshot

        self.switch('//*[@id="sBodyFrame"]')
        try:
            self.click('//*[@id="tbSnapshotRepsbutton2"]/a', 3) #demo link
        except methods.TimeoutException:
            self.switch()
            self.click('//*[button]/*[text()="Open Record"]')
            self.switch('//*[@id="sBodyFrame"]')
            self.click('//*[@id="tbSnapshotRepsbutton2"]/a') #demo link

        self.click('//*[@id="FrameHeaderPrint"]')

        self.switch('//*[@id="sMenuFrame"]')
        self.click('//*[@id="navContainer"]//*[contains(text(), "Chart Review")]') #chart review

        self.switch('//*[@id="sBodyFrame"]')
        try:
            self.click(f'//*[text()="Anesthesia Event"]/../..//*[text()="{dos}"]/..') #anes link
            try:
                self.switch('//*[@id="BTGiframeLB"]')
                self.click('//*[@id="Reason"]/*[text()="Billing"]')
                self.key('//*[@id="Password"]', self.password)
                self.click('//*[@id="BTGToolBarbutton1"]') #accept button
                self.switch('//*[@id="sBodyFrame"]')
            except methods.TimeoutException:
                pass
            self.switch('//*[@id="sBodyFrame"]')
            self.click('//*[@id="FrameHeaderPrint"]')
        except methods.TimeoutException:
            pass

        self.switch('//*[@id="sMenuFrame"]')
        self.click(
            '//*[@id="navContainer"]//*[contains(text(), "Coverages & Benefits")]'
            ) #coverage

        self.switch('//*[@id="sBodyFrame"]')
        eles:list = self.browser.find_elements_by_xpath('//*[@id="DefaultWTableID"]//*[input]')
        num:int
        for num in range(1,len(eles)+1):
            try:
                self.click(f'//*[@id="DefaultWTableID"]//*[input][{num}]')
            except methods.TimeoutException:
                javascript:list = [
                    'var table = document.getElementById("DefaultWTableID")',
                    f'table.getElementsByTagName("input")[{num-1}].click()'
                ]
                self.script(javascript)
            self.click('//*[@id="toolbar1button2"]/a') #coverage detail report
            self.click('//*[@id="FrameHeaderPrint"]')
            self.click('//*[@id="ToolBarbutton1"]') #back button

        self.switch('//*[@id="sHeaderFrame"]')
        self.click('//*[@id="ClosePatient"]')

    def concat(self) -> None:
        '''combine pdfs'''
        target:os.PathLike = os.path.join(self.root, "Billing and Compliance PDFs")
        hospital_pdfs:os.PathLike = os.path.join(self.root, "Hospital PDFs")
        carelink_pdfs:os.PathLike = os.path.join(self.root, "Carelink PDFs")

        try:
            dos:str = self.patient["DOS"].strftime("%y-%m-%d")
        except AttributeError:
            dos:str = self.patient["DOS"]

        filename:str = "_".join([
            "DOS_"+dos,
            "MRN_"+self.patient["MRN"]+"",
            self.patient["LName"]+", "+self.patient["FName"],
            "CSN_"+self.patient["CSN"]+".pdf"
        ])
        filename:os.PathLike = os.path.join(target, filename)

        merger:object = PyPDF2.PdfFileMerger()

        pdf:str
        for pdf in os.listdir(hospital_pdfs):
            if fnmatch(pdf, f"*{self.patient['CSN']}*"):
                merger.append(os.path.join(hospital_pdfs, pdf), 'rb')

        pdf:str
        for pdf in os.listdir(carelink_pdfs):
            if fnmatch(pdf, f"{self.patient['LName']}*"):
                merger.append(os.path.join(carelink_pdfs, pdf), 'rb')

        with open(filename, 'wb') as outfile:
            merger.write(outfile)

        merger.close()

        pdf:str
        for pdf in os.listdir(carelink_pdfs):
            os.remove(os.path.join(carelink_pdfs, pdf))

        return filename

    def main(self) -> None:
        '''main trigger'''
        try:
            if self.record_list:
                self.login()
                patient:dict
                for patient in self.record_list:
                    if not patient["DOB"]:
                        continue
                    print(len(self.record_list)-self.record_list.index(patient))
                    self.patient:dict = patient
                    result:str = self.find_patient()
                    if not result:
                        self.download_pdfs()
                    filename:os.PathLike = self.concat()
                    statement:list = [
                        "UPDATE #REMOVED#",
                        "SET Filename = :file WHERE CSN = :csn"
                    ]
                    query_text:str = methods.sqlalchemy.text(" ".join(statement))
                    self.conn.execute(query_text, csn=patient["CSN"], file=filename)
            subprocess.Popen(["python", self.bldr_sftp, "True"])
        except Exception as exception:
            self.browser.quit()
            methods.send_email(self.patient["CSN"]+"\n\n"+methods.traceback.format_exc(), "BLDR BCH Webscrape")
            raise exception


if __name__ == "__main__":
    try:
        Main("BLDR_BCH", kiosk=True, browser_quit=True)
    except Exception as exception:
        methods.send_email(methods.traceback.format_exc(), __doc__)
        raise exception
