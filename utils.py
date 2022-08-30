import re
import os
import shlex
import shutil
import urllib
import tarfile
import inquirer
import requests
import tempfile
import zstandard 
import subprocess

from pathlib import Path
from functools import partial
from urllib.request import urlopen
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from config import *

class Utils:
    def __init__(self) -> None:
        self.aur_pkgs = {}
        if USE_AUR:
            self.get_all_pkgs_aur()

    def new_progress(self):
        return Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            "  "
        )
        
    def get_pkg(self, pkg_name):
        output = None
        data = requests.get(ARCH_SEARCH_URL.format(pkg=pkg_name)).json()
        res = data["results"]

        if len(res) > 0:
            output = ARCH_URL.format(
                repo = res[0]["repo"],
                arch = res[0]["arch"],
                pkg  = res[0]["pkgname"]
            )
            return output

        aur_matches = {}
        for pkg in self.aur_pkgs:
            if pkg.startswith(pkg_name):
                aur_matches[pkg] = self.aur_pkgs[pkg]
        
        if len(aur_matches) == 1:
            output = os.path.join(AUR_URL, list(aur_matches.values())[0])

        elif len(aur_matches) > 1:
            choices = list(aur_matches.keys())
            choices.append("None of the above")
            s = self.user_select("Multiple Packages were found. Please select which one to use", choices)
            if s != "None of the above":
                output = os.path.join(AUR_URL, aur_matches[s])

        return output


    def user_select(self, que, choices):
        print()
        print(que)
        q = [inquirer.List('a', message=">>", choices=choices)]
        return inquirer.prompt(q)["a"]


    def user_text(self, que):
        print()
        print(que)
        q = [inquirer.Text('a', message=">>")]
        return inquirer.prompt(q)["a"]


    def user_confirm(self, que, y_otp="Yes", n_opt="No"):
        ans = self.user_select(que, [y_otp, n_opt])
        if ans == y_otp:
            return True
        else:
            return False

    def user_path(self, que, required=False):
        while True:
            print()
            print(que)
            q = [inquirer.Text('a', message=">>")]
            p = inquirer.prompt(q)["a"]
            if not p:
                if required:
                    print("This field is required.")
                    continue
                else:
                    p = None
                    break

            if os.path.exists(p):
                break

            print("File does not exist. Please try again.")
            print()

        return p

    def get_all_pkgs_aur(self):
        print("Loading Chaotic AUR package list...")
        txt = requests.get(AUR_URL).text
        x = re.findall('href="(.*tar.zst)"', txt)

        for i in x:
            name = urllib.parse.unquote(i, encoding='utf-8', errors='replace').replace(".pkg.tar.zst", "")
            self.aur_pkgs[name] = i


    def download(self, url, dest, name):
        progress = self.new_progress()
        with progress:
            print(f"Downloading {name}...")
            task_id = progress.add_task("download", filename="  ", start=False)
            response = urlopen(url)
            progress.update(task_id, total=int(response.info()["Content-length"]))
            with open(dest, "wb") as dest_file:
                progress.start_task(task_id)
                for data in iter(partial(response.read, 32768), b""):
                    dest_file.write(data)
                    progress.update(task_id, advance=len(data))


    def extract_zst(self, zst_file, out_path):
        zst_file = Path(zst_file).expanduser()
        out_path = Path(out_path).expanduser().resolve()
        dctx = zstandard.ZstdDecompressor()

        with tempfile.TemporaryFile(suffix=".tar") as ofh:
            with zst_file.open("rb") as ifh:
                dctx.copy_stream(ifh, ofh)
            ofh.seek(0)
            with tarfile.open(fileobj=ofh) as z:
                z.extractall(out_path)

    def validate_desktop_file(self, file_path):
        out = self.run_cmd(f"desktop-file-validate {file_path}", True)
        if out:
            return False, out
        else:
            return True, None

    def copy_file(self, src_file, dest_dir):
        file_name = src_file.split("/")[-1]
        dest_file = os.path.join(dest_dir, file_name)
        if src_file != dest_file:
            shutil.copyfile(src_file, dest_file)

    def run_cmd(self, cmd, record_output=False):
        if record_output:
            proc = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE)
            return proc.stdout.decode("utf-8").strip()
        else:
            subprocess.run(shlex.split(cmd))
            
    def set_icon_desktop_file(self, desktop_file, icon_name):
        self.run_cmd(f"desktop-file-edit {desktop_file} --set-icon={icon_name}")

    def make_executable(self, file_path):
        self.run_cmd(f"chmod +x {file_path}")

    def rm(self, f):
        if os.path.exists(f):
            os.remove(f)

    def extract_deps(self, pkginfo_file):
        pkgs = {}
        with open(pkginfo_file, "r") as f:
            lines = f.read().splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("depend ="):
                    pkgs[line.replace("depend =", "").strip()] = None

        return pkgs

    def max_len(self, lst):
        max1 = len(lst[0])
        for i in lst:
            if(len(i) > max1):
                max1 = len(i)

        return max1