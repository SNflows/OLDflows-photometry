import os, sys, time, logging

from getpass import getpass
from requests import Session
from pathlib import Path
from functools import wraps, partial
from bs4 import BeautifulSoup
from astropy.io import fits

from flows import config, api, photometry
from flows_photometry import run_photometry

CONFIG = config.load_config()
ARCHIVE = CONFIG["photometry"]["archive_local"]

class FileDownloader:

    _instance = None

    username, password = None, None

    def __new__(cls):

        if cls._instance:
            return cls._instance

        cls._instance = super().__new__(cls)

        cls._instance.session, cls._instance.logged_in = Session(), False
        if not cls.username is None and not cls.password is None:
            cls._instance.login(cls.username, cls.password)

        return cls._instance

    def login(self, username, password):

        soup = BeautifulSoup(self.session.get("https://flows.phys.au.dk").content, "html.parser")
        token = soup.find("form", id="loginform").find("input", dict(name="token")).get("value")

        params = dict(token=token, username=username, password=password)
        page = self.session.post("https://flows.phys.au.dk/login/login.php", params)

        if page.url != "https://flows.phys.au.dk/index.php":
            raise Exception("Login failed")

        self.logged_in = True

    def download(self, fileid, filename):

        if not self.logged_in:
            raise Exception(f"Can't download {fileid}, not logged in")

        logging.getLogger('flows').info("Downloading image %s", filename)

        params = dict(fileid=fileid)
        fitsfile = self.session.get("https://flows.phys.au.dk/catalog/download_file.php", params=params)

        Path(os.path.dirname(filename)).mkdir(parents=True, exist_ok=True)
        with open(filename, "wb") as fd:
            fd.write(fitsfile.content)

def photometry_decorator(function):

    def wrapper(fileid, *args, **kwargs):

        file_downloader = FileDownloader()
        datafile = api.get_datafile(fileid)

        filename = f"""{ARCHIVE}/{datafile["path"]}"""
        if not os.path.isfile(filename):
            file_downloader.download(fileid, filename)

        if not datafile["diffimg"]:
            return function(fileid, *args, **kwargs)

        filename = f"""{ARCHIVE}/{datafile["diffimg"]["path"]}"""
        if not os.path.isfile(filename):
            file_downloader.download(datafile["diffimg"]["fileid"], filename)

        return function(fileid, *args, **kwargs)

    return wraps(function)(wrapper)

def main():

    if "--no-auto-download" in sys.argv:
        sys.argv.remove("--no-auto-download")
        return run_photometry.main()

    print("flows.phys.au.dk login (leave empty if not needed)")
    username, password = input("Username: "), getpass("Password: ")

    if username and password:
        FileDownloader.username = username
        FileDownloader.password = password

    run_photometry.photometry = photometry_decorator(photometry)
    return run_photometry.main()

if __name__ == "__main__":
    main()
