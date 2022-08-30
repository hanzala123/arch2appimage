import re
import os
import sys
import time
import glob
import shutil

from config import *
from utils import Utils

if os.path.exists(APP_DIR):
    print(f"{APP_DIR}/ already exists. Please remove it then run the script again.")
    sys.exit(1)

print()
print("Convert any Arch linux package (official/AUR) to AppImage!!")
utils = Utils()
main_pkg = None

while True:
    main_pkg = utils.user_text("Enter the name of the package (leave empty to quit)")

    if not main_pkg:
        print("Exiting...")
        sys.exit(1)
    
    main_pkg_url = utils.get_pkg(main_pkg)

    if main_pkg_url:
        break

    print("Package not found. Please check the name and try again")
    print()


print()
os.mkdir(APP_DIR)

utils.download(main_pkg_url, "download", main_pkg)
utils.extract_zst("download", APP_DIR)
utils.rm("download")

desktop_file = glob.glob(os.path.join(APP_DIR, "usr/share/applications/*.desktop"))

if not desktop_file:
    print("No .desktop file was found in the package.")
    desktop_file = utils.user_path("Please enter the path to a .desktop file", required=True)

elif len(desktop_file) == 1:
    desktop_file = desktop_file[0]

else:
    desktop_file = utils.user_select("Select the .desktop file to be used", desktop_file)


while True:
    vfd, msg = utils.validate_desktop_file(desktop_file)
    if vfd:
        break
    
    print()
    print(".desktop file validation failed due to the error below:")
    print(msg)
    desktop_file = utils.user_path("Please enter the path to a valid .desktop file", required=True)


utils.copy_file(desktop_file, APP_DIR)

with open(desktop_file, "r") as f:
    icon_name = re.findall('Icon=(.*)', f.read())
    if icon_name:
        icon_name = icon_name[0]
    else:
        icon_name = None


icon_file = None

if not icon_name:
    print("The .desktop file doesn't have an Icon attribute")
    icon_file = utils.user_path("Please enter the path to the icon file to be used", required=True)
    if icon_file is not None:
        icon_name = ".".join(icon_file.split("/")[-1].split(".")[:-1])
        utils.set_icon_desktop_file(desktop_file, icon_name)

else:
    i_files = os.path.join(APP_DIR, f"usr/share/icons/**/*.*")
    icon_file = glob.glob(i_files, recursive=True)

    if not icon_file:
        print(f"No icon file was found in {APP_DIR}/usr/share/icons/")
        icon_file = utils.user_path("Please enter the path to the icon file to be used", required=True)

    elif len(icon_file) == 1:
        icon_file = icon_file[0]

    else:
        icon_file = utils.user_select("Please select the icon file to be used", sorted(icon_file))


utils.copy_file(icon_file, APP_DIR)

file_name = icon_file.split("/")[-1]
file_ext = file_name.split(".")[-1]
if file_name != f"{icon_name}.{file_ext}":
    os.rename(
        os.path.join(APP_DIR, file_name), 
        os.path.join(APP_DIR, f"{icon_name}.{file_ext}")
    )

pkgs = {}

with open(os.path.join(APP_DIR, ".PKGINFO"), "r") as f:
    lines = f.read().splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("depend ="):
            pkgs[line.replace("depend =", "").strip()] = None


while True:
    not_found = []
    for pkg in pkgs:
        if pkgs[pkg]:
            continue

        url = utils.get_pkg(pkg)
        if url:
            pkgs[pkg] = url
        
        else:
            not_found.append(pkg)

    print()
    print("These packages (and their dependencies) will be downloaded:")

    for i, p in enumerate(pkgs):
        if pkgs[p]:
            print(f"{i+1}. {p}")

    if not_found:
        print()
        print("These packages could not be found: " + " ".join(not_found))


    new_pkgs = utils.user_text("If you would like to add additional packages " +
        "please enter them below (space seperated). Leave empty to start downloading")

    if not new_pkgs.strip():
        break

    for i in new_pkgs.split(" "):
        if i not in pkgs:
            pkgs[i] = None


for name, url in pkgs.items():
    if url:
        utils.download(url, "download", name)
        utils.extract_zst("download", APP_DIR)
        utils.rm("download")


files_to_delete = [".BUILDINFO", ".MTREE", ".PKGINFO", ".INSTALL"]
for i in files_to_delete:
    utils.rm(os.path.join(APP_DIR, i))


utils.copy_file(os.path.join(RES_DIR, "AppRun"), APP_DIR)
utils.make_executable(os.path.join(APP_DIR, "AppRun"))

ldp_file = os.path.join(RES_DIR, "libunionpreload.so")
if utils.user_confirm("Would you like to download the latest \
libunionpreload.so? If you select No the existing one will be used."):
    utils.download(LDP_URL, ldp_file, "libunionpreload.so")

utils.copy_file(ldp_file, APP_DIR)
utils.make_executable(os.path.join(APP_DIR, "libunionpreload.so"))

while True:
    print("AppDir is ready. Please take a look into the directory to ensure everything is OK.")
    print("Exec the AppRun (command './AppRun') to test if everything works.")
    yn = utils.user_confirm(
        "What would you like to do next?", 
        "Build the AppImage", 
        "Add more packages"
    )
    if yn:
        break

    pkgs = {}
    while True:
        new_pkgs = utils.user_text("If you would like to add additional packages " +
            "please enter them below (space seperated). Leave empty to start downloading")

        if not new_pkgs.strip():
            break

        for i in new_pkgs.split(" "):
            if i not in pkgs:
                pkgs[i] = None

        not_found = []
        for pkg in pkgs:
            if pkgs[pkg]:
                continue

            url = utils.get_pkg(pkg)
            if url:
                pkgs[pkg] = url
            
            else:
                not_found.append(pkg)

        print()
        print("These packages will be downloaded:")

        for i, p in enumerate(pkgs):
            if pkgs[p]:
                print(f"{i+1}. {p}")

        if not_found:
            print()
            print("These packages could not be found: " + " ".join(not_found))

    if pkgs:
        for name, url in pkgs.items():
            if url:
                utils.download(url, "download", name)
                utils.extract_zst("download", APP_DIR)
                utils.rm("download")
     

appimagetool = os.path.join(RES_DIR, "appimagetool")

if utils.user_confirm("Would you like to download the \
latest AppImageTool? If you select No the existing one will be used."):
    utils.download(APPIMAGETOOL_URL, appimagetool, "AppImageTool")
    utils.make_executable(appimagetool)

while True:
    print("Running AppImageTool...")
    print()
    if not os.path.exists(OUT_DIR):
        os.mkdir(OUT_DIR)

    cmd = f"./{appimagetool} -n {APP_DIR} {OUT_DIR}/{main_pkg}-{ARCH}.AppImage"
    utils.run_cmd(cmd)

    time.sleep(5)
    yn = utils.user_confirm("Would you like to re-build it?")
    if not yn:
        break

if utils.user_confirm(f"Would you like to remove {APP_DIR}/"):
    shutil.rmtree(APP_DIR)

print("Exiting...")