import requests
import wget
import json
import re
import os
import argparse
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("package", nargs="*", help="Download and install a package")
parser.add_argument("-all", action="store_true", help="Download and install all packages")
parser.add_argument("-l", "--list", action="store_true", help="List available packages")
parser.add_argument("-q", "--quiet", action="store_false", help="Quiet mode")
args = parser.parse_args()

folder_name = os.path.expandvars("%temp%/WinApt/")
packages_url = "https://raw.githubusercontent.com/MehdiRtal/WinApt/main/packages.json"

if not os.path.exists(folder_name):
  os.makedirs(folder_name)
if not os.path.exists(folder_name + "packages.json"):
  wget.download(packages_url, folder_name, bar=None)
data = json.load(open(folder_name + "packages.json", "r"))

def download_page(arg):
  return "https://filehippo.com/download_{}/post_download/".format(arg)

def download_link(arg):
  get = requests.get(download_page(arg)).text
  soup = BeautifulSoup(get, "lxml")
  download_link = soup.find("script", {"type": "text/javascript", "data-qa-download-url": True})["data-qa-download-url"]
  if arg == "spotify":
    download_link = "https://download.spotify.com/SpotifyFullSetup.exe"
  return download_link

def version(arg):
  get = requests.get(download_page(arg)).text
  soup = BeautifulSoup(get, "lxml")
  version = "".join(re.findall("\d|[.]", soup.find("p", class_="program-header-inline__version").text))
  return version

def download(arg):
  if args.quiet:
    print("\nDownloading {} v{}".format(arg, version(arg)))
    wget.download(download_link(arg), folder_name)
  else:
    wget.download(download_link(arg), folder_name, bar=None)

def install(arg):
  if args.quiet:
    print("\nInstalling {} v{}".format(arg, version(arg)))
  if data[arg]["installer"] == "custom":
    os.system("cmd /c start {} {}".format(file_path(arg), data[arg]["arguments"]))
  if data[arg]["installer"] == "msi":
    os.system("cmd /c msiexec /i {} /qn /norestart".format(file_path(arg)))
  if data[arg]["installer"] == "innosetup":
    os.system("cmd /c start {} /VERYSILENT /NORESTART".format(file_path(arg)))
  if data[arg]["installer"] == "installshield":
    os.system("cmd /c start {} /s".format(file_path(arg)))
  if data[arg]["installer"] == "nsis":
    os.system("cmd /c start {} /S".format(file_path(arg)))
  if data[arg]["installer"] == "squirrel":
    os.system("cmd /c start {} -s".format(file_path(arg)))

def file_path(arg):
  file_name = wget.filename_from_url(download_link(arg))
  return folder_name + file_name

def deploy():
  for package in data if args.all or args.list else data and args.package:
    try:
      if "version" not in data or data[package]["version"] != version(package):
        data[package]["version"] = version(package)
        json.dump(data, open(folder_name + "packages.json", "w"), indent = 2)
      if args.list:
        print(package + " v" + version(package))
      else:
        if data[package]["version"] == version(package) and os.path.exists(file_path(package)):
          install(package)
        else:
          if os.path.exists(file_path(package)):
            os.remove(file_path(package))
          download(package)
          install(package)
    except AttributeError:
      if args.quiet:
        print("\n{} not found.".format(package))

if __name__ == "__main__":
	deploy()
