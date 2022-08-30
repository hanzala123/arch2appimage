import platform

USE_AUR = True # set to False to disable AUR Support

OUT_DIR = "out"
APP_DIR = "AppDir"
RES_DIR = "resources"

ARCH = platform.machine()

AUR_URL         = f"https://cdn-mirror.chaotic.cx/chaotic-aur/{ARCH}"
ARCH_URL        = "https://archlinux.org/packages/{repo}/{arch}/{pkg}/download"
ARCH_SEARCH_URL = "https://archlinux.org/packages/search/json/?name={pkg}"

LDP_URL          = "https://github.com/project-portable/libunionpreload/releases/download/amd64/libunionpreload.so"
APPIMAGETOOL_URL = f"https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-{ARCH}.AppImage"