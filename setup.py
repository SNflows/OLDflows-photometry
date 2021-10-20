import os, urllib.request, tarfile
from setuptools import setup, find_packages

COMMIT = "59d7914a3457a12be76ae92d13c31861df90fa99"

url = f"https://github.com/rhandberg/flows/tarball/{COMMIT}"
filename, _ = urllib.request.urlretrieve(url)

tar = tarfile.open(filename)
directory = tar.getmembers()[0].name
tar.extractall()

os.system(f"mv {directory} flows_photometry")
os.system(f"touch flows_photometry/__init__.py")
os.system(f"cp photometry.py flows_photometry")

setup(
    name = "flows-photometry",
    version = "0.1a0",
    packages = ["flows_photometry"],
    entry_points = {
        "console_scripts": [
            "flows-photometry = flows_photometry.photometry:main",
        ]
    }
)
