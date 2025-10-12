#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from os import mkdir, chmod, rename, popen
from os.path import exists, dirname
from six.moves import range
import subprocess
import sys
import threading
import zipfile

PY3 = sys.version_info.major >= 3

if PY3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen


script_path = "/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Centrum/Tools/FCA.sh"

# Files for personal lines
PERSONAL_LINES_DIR = "/etc/personal_lines/"
CCCAM_PERSONAL = PERSONAL_LINES_DIR + "cccamx"
OSCAM_PERSONAL = PERSONAL_LINES_DIR + "oscamx"
NCAM_PERSONAL = PERSONAL_LINES_DIR + "ncamx"


# recoded from lululla
def ensure_personal_lines_dir():
    """Create directory for personal lines if not exists"""
    if not exists(PERSONAL_LINES_DIR):
        mkdir(PERSONAL_LINES_DIR, 0o755)
        print("DEBUG: Created personal lines directory:", PERSONAL_LINES_DIR)


def save_personal_lines_from_files():
    """Copy personal line files to personal_lines directory"""
    ensure_personal_lines_dir()

    print("DEBUG: ===== SAVE PERSONAL LINES START =====")
    print("DEBUG: Personal lines dir:", PERSONAL_LINES_DIR)

    files_copied = []

    personal_files = [
        ('/tmp/cccamx.txt', CCCAM_PERSONAL),
        ('/tmp/oscamx.txt', OSCAM_PERSONAL),
        ('/tmp/ncamx.txt', NCAM_PERSONAL),
        ('/etc/personal_lines/cccamx.txt', CCCAM_PERSONAL),
        ('/etc/personal_lines/oscamx.txt', OSCAM_PERSONAL),
        ('/etc/personal_lines/ncamx.txt', NCAM_PERSONAL),
    ]

    print("DEBUG: Searching for personal line files...")
    for source, destination in personal_files:
        print("DEBUG: Checking source:", source, "-> exists:", exists(source))
        if exists(source):
            try:
                with open(source, 'r') as f:
                    content = f.read().strip()
                print("DEBUG: Found file:", source, "Content length:", len(content))

                if content:
                    with open(destination, 'w') as f:
                        f.write(content)
                    files_copied.append(source)
                    print("DEBUG: Copied %s to %s" % (source, destination))
                else:
                    print("DEBUG: File", source, "is empty")
            except Exception as e:
                print("DEBUG: Error copying %s: %s" % (source, str(e)))
        else:
            print("DEBUG: Source not found:", source)

    print("DEBUG: Files copied:", files_copied)
    print("DEBUG: CCCAM_PERSONAL exists:", exists(CCCAM_PERSONAL))
    print("DEBUG: OSCAM_PERSONAL exists:", exists(OSCAM_PERSONAL))
    print("DEBUG: NCAM_PERSONAL exists:", exists(NCAM_PERSONAL))
    print("DEBUG: ===== SAVE PERSONAL LINES END =====")

    return files_copied


def add_personal_lines_to_cccam_only():
    """Add personal lines to CCcam.cfg ONLY - no conversion"""
    ensure_personal_lines_dir()
    print("DEBUG: Adding personal lines to CCcam.cfg ONLY")

    if exists(CCCAM_PERSONAL):
        with open(CCCAM_PERSONAL, 'r') as f:
            cccam_content = f.read().strip()

        if cccam_content:
            cccam_paths = findCccam()
            for cccam_path in cccam_paths:
                cccam_path = cccam_path.strip()
                if exists(cccam_path):
                    with open(cccam_path, 'r') as f:
                        current_content = f.read()

                    # Remove previous personal sections
                    lines = current_content.split('\n')
                    filtered_lines = []
                    skip_section = False

                    for line in lines:
                        if '# Personal CCCam Lines' in line:
                            skip_section = True
                            continue
                        elif skip_section and line.strip() and not line.startswith('#'):
                            continue
                        elif skip_section and not line.strip():
                            skip_section = False
                            continue
                        else:
                            filtered_lines.append(line)

                    new_content = '\n'.join(filtered_lines).strip()

                    if cccam_content not in new_content:
                        if new_content:
                            new_content += '\n\n# Personal CCCam Lines\n'
                        else:
                            new_content = '# Personal CCCam Lines\n'
                        new_content += cccam_content

                    with open(cccam_path, 'w') as f:
                        f.write(new_content + '\n')

                    print("DEBUG: Added personal CCCam lines to %s" % cccam_path)


def convert_personal_lines_if_needed():
    """Convert personal lines to OSCam/NCam and append to files - CLEAN FIRST"""
    print("DEBUG: Converting and appending personal lines to OSCam/NCam...")

    if not exists(CCCAM_PERSONAL):
        print("DEBUG: No personal lines to convert")
        return

    # Read current personal lines
    with open(CCCAM_PERSONAL, 'r') as f:
        current_personals = f.read().strip()

    if not current_personals:
        print("DEBUG: Personal lines file is empty")
        return

    # 1. CLEAN OSCam/NCam files first (remove duplicate free servers)
    clean_oscam_ncam_files()

    # 2. Convert personal lines and append them
    print("DEBUG: Converting personal lines to reader format...")
    convert_only_personal_c_lines()


def clean_oscam_ncam_files():
    """Clean OSCam/NCam files by removing duplicate free servers"""
    print("DEBUG: Cleaning OSCam/NCam files...")

    # Paths to clean
    paths_to_clean = [
        '/etc/tuxbox/config/oscam/oscam.server',
        '/etc/tuxbox/config/oscam-emu/oscam.server',
        '/etc/tuxbox/config/oscam_atv_free/oscam.server',
        '/etc/tuxbox/config/oscam.server',
        '/etc/tuxbox/config/oscam-stable/oscam.server',
        '/var/tuxbox/config/oscam.server',
        '/etc/tuxbox/config/gcam.server',
        '/etc/tuxbox/config/ncam.server',
        '/etc/tuxbox/config/ncam/ncam.server',
        '/etc/tuxbox/config/supcam-emu/oscam.server',
        '/etc/tuxbox/config/oscamicam/oscam.server',
        '/etc/tuxbox/config/oscamicamnew/oscam.server'
    ]

    for file_path in paths_to_clean:
        if exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()

                # Remove ALL free readers (those without "_personal")
                lines = content.split('\n')
                cleaned_lines = []
                current_reader = []
                in_reader = False
                is_personal = False

                for line in lines:
                    if line.strip().startswith('[reader]'):
                        # New reader started
                        if current_reader and is_personal:
                            # If it was a personal reader, keep it
                            cleaned_lines.extend(current_reader)
                        current_reader = [line]
                        in_reader = True
                        is_personal = False
                    elif in_reader and line.strip().startswith('label =') and '_personal' in line:
                        # It's a personal reader
                        is_personal = True
                        current_reader.append(line)
                    elif in_reader and line.strip() and not line.strip().startswith('['):
                        # Continue current reader
                        current_reader.append(line)
                    elif in_reader and (not line.strip() or line.strip().startswith('[')):
                        # End of the reader
                        if current_reader and is_personal:
                            cleaned_lines.extend(current_reader)
                            cleaned_lines.append('')  # Empty line
                        current_reader = []
                        in_reader = False
                        is_personal = False
                        if line.strip():
                            cleaned_lines.append(line)
                    elif not in_reader:
                        cleaned_lines.append(line)

                # Add the last reader if personal
                if current_reader and is_personal:
                    cleaned_lines.extend(current_reader)

                # Rebuild the content
                cleaned_content = '\n'.join(cleaned_lines).strip()

                # Write the cleaned file
                with open(file_path, 'w') as f:
                    f.write(cleaned_content + '\n')

                print("DEBUG: Cleaned %s" % file_path)

            except Exception as e:
                print("DEBUG: Error cleaning %s: %s" % (file_path, str(e)))


def save_personal_cccam_line():  # not used
    """Save the personal CCCam line from the CCcam.cfg file"""
    ensure_personal_lines_dir()
    cccam_paths = findCccam()

    personal_lines_found = False

    for cccam_path in cccam_paths:
        cccam_path = cccam_path.strip()
        if exists(cccam_path):
            print("DEBUG: Reading CCCam file: %s" % cccam_path)
            with open(cccam_path, 'r') as f:
                content = f.read()

            # Manually search for personal lines (without extract_personal_cccam_lines)
            lines = content.split('\n')
            personal_lines = []

            for line in lines:
                line = line.strip()
                # Keep only C: lines that are not comments and do not contain free server keywords
                if (line.startswith('C: ') and
                        not line.startswith('#') and
                        'free' not in line.lower() and
                        'test' not in line.lower() and
                        'server' not in line.lower()):
                    personal_lines.append(line)

            if personal_lines:
                with open(CCCAM_PERSONAL, 'w') as f:
                    f.write('\n'.join(personal_lines))
                print("DEBUG: Personal CCCam lines saved to: %s" % CCCAM_PERSONAL)
                print("DEBUG: Found %s personal CCCam lines" % len(personal_lines))
                personal_lines_found = True
                break  # Take only from the first valid file
            else:
                print("DEBUG: No personal CCCam lines found in: %s" % cccam_path)

    # If no personal lines are found but the file already exists, keep it
    if not personal_lines_found and exists(CCCAM_PERSONAL):
        print("DEBUG: Keeping existing personal CCCam file")
        return True

    return personal_lines_found


def add_personal_lines_to_configs():
    """Add personal lines to configuration files - NO conversion"""
    ensure_personal_lines_dir()
    print("DEBUG: Adding personal lines to configs - NO conversion")

    # Just add to CCcam.cfg - NO conversion
    add_personal_lines_to_cccam_only()

    print("DEBUG: Personal lines addition completed - conversion handled separately")


def convert_only_personal_c_lines():
    """Convert ONLY personal C-lines to OSCam/NCam reader format"""
    print("DEBUG: ===== CONVERT PERSONAL LINES START =====")
    print("DEBUG: CCCAM_PERSONAL exists:", exists(CCCAM_PERSONAL))

    if not exists(CCCAM_PERSONAL):
        print("DEBUG: No personal CCCam lines found to convert")
        return

    # Read personal C-lines
    with open(CCCAM_PERSONAL, 'r') as f:
        cccam_content = f.read()

    print("DEBUG: Personal content:", cccam_content)
    print("DEBUG: Content length:", len(cccam_content))

    # Convert ONLY personal C-lines to OSCam format
    oscam_servers = []
    lines = cccam_content.split('\n')

    print("DEBUG: Lines to process:", len(lines))

    for line in lines:
        line = line.strip()
        print("DEBUG: Processing line:", line)
        # Convert ONLY personal C-lines
        if line.startswith('C: ') and not line.startswith('#'):
            print("DEBUG: Found C-line:", line)
            # Parse C-line and convert to OSCam reader
            parts = line.split()
            print("DEBUG: Line parts:", parts)
            if len(parts) >= 5:
                hostname = parts[1]
                port = parts[2]
                username = parts[3]
                password = parts[4]

                oscam_server = """[reader]
label = %s_%s_personal
protocol = cccam
device = %s,%s
user = %s
password = %s
group = 2
ccckeepalive = 1
inactivitytimeout = 30
reconnecttimeout = 5
disablecrccws = 1
disablecrccws_only_for = 0E00:000000,0500:030B00,050F00;098C:000000;09C4:000000
audisabled = 0
""" % (hostname, port, hostname, port, username, password)
                oscam_servers.append(oscam_server)
                print("DEBUG: Created reader for:", hostname)

    print("DEBUG: Servers created:", len(oscam_servers))

    # Append personal servers to OSCam/NCam files
    if oscam_servers:
        # OSCam files
        oscam_paths = findOscam()
        for oscam_path in oscam_paths:
            oscam_path = oscam_path.strip()
            if exists(oscam_path):
                append_personal_servers(oscam_path, oscam_servers)

        # NCam files
        ncam_paths = [
            '/etc/tuxbox/config/ncam.server',
            '/etc/tuxbox/config/ncam/ncam.server'
        ]
        for ncam_path in ncam_paths:
            if exists(ncam_path):
                append_personal_servers(ncam_path, oscam_servers)

        print("DEBUG: Successfully converted personal C-lines to OSCam/NCam")
    else:
        print("DEBUG: No personal C-lines to convert")


def append_personal_servers(file_path, servers):
    """APPEND personal servers to config file - ALWAYS add"""
    try:
        # Read existing content
        existing_content = ""
        if exists(file_path):
            with open(file_path, 'r') as f:
                existing_content = f.read()

        # Remove OLD personal sections to avoid duplicates
        lines = existing_content.split('\n')
        filtered_lines = []
        skip_personal = False

        for line in lines:
            if '# Personal Converted CCcam servers' in line:
                skip_personal = True
                continue
            elif skip_personal and line.strip() and not line.startswith('['):
                continue
            elif skip_personal and (line.startswith('[') or not line.strip()):
                skip_personal = False
                if line.strip():  # Add only if not empty
                    filtered_lines.append(line)
            elif not skip_personal:
                filtered_lines.append(line)

        # Rebuild base content
        base_content = '\n'.join(filtered_lines).strip()

        # ALWAYS append personal servers at the end
        new_content = base_content
        if new_content:
            new_content += '\n\n'

        new_content += '# Personal Converted CCcam servers\n'
        for server in servers:
            new_content += server + '\n'

        # Write the file
        with open(file_path, 'w') as f:
            f.write(new_content)

        print("DEBUG: Appended personal servers to %s" % file_path)

    except Exception as e:
        print("DEBUG: Error writing to %s: %s" % (file_path, str(e)))


def confirmSavePersonalLines(self, confirmed):
    if confirmed:
        success = save_personal_lines_from_files()

        if success:
            message = "Personal lines saved successfully!\n\n"
            if exists(CCCAM_PERSONAL):
                with open(CCCAM_PERSONAL, 'r') as f:
                    content = f.read().strip()
                if content:
                    message += "CCCam lines: ✓ (%s lines)\n" % len(content.split('\n'))
            if exists(OSCAM_PERSONAL):
                message += "OSCam config: ✓\n"
            if exists(NCAM_PERSONAL):
                message += "NCam config: ✓\n"
            message += "\nThese lines will be automatically added after each update."
        else:
            message = "No personal line files found!\n\nPlease create one of these files:\n- /tmp/cccamx.txt\n- /etc/personal_lines/cccamx.txt\n\nwith your personal C-lines and try again."

        self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=10)


def findCccam():
    search_dirs = ['/etc']
    paths = []
    for directory in search_dirs:
        cmd = 'find %s -name "CCcam.cfg"' % directory
        try:
            if PY3:
                res = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE).decode().strip()
            else:
                res = subprocess.check_output(cmd, shell=True, stderr=subprocess.PIPE).strip()
            if res:
                paths.extend(res.splitlines())
        except subprocess.CalledProcessError:
            continue
    if not paths:
        paths.append("/etc/CCcam.cfg")
    return paths


def findOscam():
    paths = [
        '/etc/tuxbox/config/oscam/oscam.server',
        '/etc/tuxbox/config/oscam-emu/oscam.server',
        '/etc/tuxbox/config/oscam_atv_free/oscam.server',
        '/etc/tuxbox/config/oscam.server',
        '/etc/tuxbox/config/oscam-stable/oscam.server',
        '/var/tuxbox/config/oscam.server',
        '/etc/tuxbox/config/gcam.server',
        '/etc/tuxbox/config/ncam.server',
        '/etc/tuxbox/config/ncam/ncam.server',
        '/etc/tuxbox/config/supcam-emu/oscam.server',
        '/etc/tuxbox/config/oscamicam/oscam.server',
        '/etc/tuxbox/config/oscamicamnew/oscam.server'
    ]
    return paths


def saveFileContent(file_pathx):
    """Returns the contents of the file if it exists."""
    if exists(file_pathx):
        with open(file_pathx, 'r') as f:
            return f.read()
    return ""


def prependToFile(file_pathx):
    """
    Reads (and creates if necessary) the original backup of the file,
    adding markers to avoid duplication.
    Returns the original content (with markers).
    """
    directory = dirname(file_pathx)
    if not exists(directory):
        print("DEBUG: Directory not exists", file_pathx)
        return ""

    backup_path = file_pathx + "Orig"
    original_content = ""

    if not exists(backup_path) and exists(file_pathx):
        with open(file_pathx, 'r') as f:
            original_content = f.read()
        with open(backup_path, 'w') as f:
            f.write(original_content)
        print("DEBUG: Made backup for %s" % file_pathx)
    elif exists(backup_path):
        with open(backup_path, 'r') as f:
            original_content = f.read()
        print("DEBUG: Read backup %s" % file_pathx)

    marker_start = "### ORIGINAL START ###"
    marker_end = "### ORIGINAL END ###"
    if marker_start not in original_content:
        original_content = marker_start + "\n" + original_content.strip() + "\n" + marker_end + "\n"
        print("DEBUG: Added marker to backup %s" % file_pathx)
    else:
        print("DEBUG: Marker present in backup %s" % file_pathx)

    return original_content


def remove_backup_block(content):
    """
    If the content starts with the backup block (marker),
    removes it and returns only the new content.
    """
    marker_start = "### ORIGINAL START ###"
    marker_end = "### ORIGINAL END ###"
    if content.startswith(marker_start):
        end_index = content.find(marker_end)
        if end_index != -1:
            return content[end_index + len(marker_end):].strip()
    return content


def ensure_directory_exists(file_path):
    """Ensures that the file directory exists; otherwise, creates it."""
    directory = dirname(file_path)
    if not exists(directory):
        return


# Main menu screen class that provides the primary user interface
class MainMenus(Screen):
    # Defining the skin (UI layout) of the MainMenus
    skin = """
            <screen name="MainMenus" position="648,363" size="750,350" title="Centrum">
                <!-- Cron -->
                <widget name="lab2" position="1,290" size="380,40" font="Regular; 30" halign="right" valign="center" backgroundColor="background" transparent="1" />
                <widget name="labstop" position="435,290" size="250,40" font="Regular;32" halign="center" valign="center" foregroundColor="white" backgroundColor="red" zPosition="1" />
                <widget name="labrun" position="435,290" size="250,40" font="Regular;32" halign="center" valign="center" foregroundColor="white" backgroundColor="green" zPosition="1" />
                <!-- Icon -->
                <widget name="icon1" position="12,62" size="130,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/icon1.png" transparent="1" alphatest="on" />
                <widget name="icon2" position="162,62" size="130,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/icon2.png" transparent="1" alphatest="on" />
                <widget name="icon3" position="312,62" size="130,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/icon3.png" transparent="1" alphatest="on" />
                <widget name="icon4" position="459,62" size="130,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/icon4.png" transparent="1" alphatest="on" />
                <widget name="icon5" position="604,62" size="130,130" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/icon5.png" transparent="1" alphatest="on" />
                <!-- Descriptions -->
                <widget name="desc1" position="12,195" size="130,30" font="Regular;20" halign="center" />
                <widget name="desc2" position="163,195" size="130,30" font="Regular;20" halign="center" />
                <widget name="desc3" position="313,195" size="130,30" font="Regular;20" halign="center" />
                <widget name="desc4" position="458,195" size="130,30" font="Regular;20" halign="center" />
                <widget name="desc5" position="608,195" size="130,30" font="Regular;20" halign="center" />
                <!-- Detail -->
                <widget name="detail" position="10,228" size="732,53" font="Regular; 28" halign="left" valign="center" />
                <eLabel name="" position="7,3" size="350,44" text="Simple ZOOM Panel 2.2.7" font="Regular; 26" foregroundColor="#707070" />
                <eLabel name="" position="445,1" size="66,26" text="created :" font="Regular; 15" foregroundColor="green" />
                <eLabel name="" position="517,2" size="81,23" text="E2W!zard" font="Regular; 16" />
                <eLabel name="" position="518,24" size="73,25" font="Regular; 16" text="HIUMAN" />
            </screen>"""

    # Constructor to initialize the MainMenus screen
    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)
        if not exists("/usr/script"):
            mkdir("/usr/script", 0o755)
        self.initUI()
        self.initActions()
        self.selectedIcon = 1
        self.script_running = threading.Event()
        self.updateSelection()
        self.my_crond_run = False
        self.on_init_cron()

    def initUI(self):
        # Set up cront
        self["lab2"] = Label(_("CronTime Current Status:"))
        self["labstop"] = Label(_("Stopped"))
        self["labrun"] = Label(_("Running"))
        self["labrun"].hide()

        # Set up icons
        self["icon1"] = Pixmap()
        self["icon2"] = Pixmap()
        self["icon3"] = Pixmap()
        self["icon4"] = Pixmap()
        self["icon5"] = Pixmap()

        # Set up descriptions
        self["desc1"] = Label("Tools")
        self["desc2"] = Label("Extras")
        self["desc3"] = Label("Settings")
        self["desc4"] = Label("CronTimer")
        self["desc5"] = Label("Help")

        # Set up detail label
        self["detail"] = Label("Select an option to view details")

        # Additional detail labels for each icon
        self["detail1"] = Label("A suite of utility tools.")
        self["detail2"] = Label("Additional features and enhancements.")
        self["detail3"] = Label("Customize plugin to your preference.")
        self["detail4"] = Label("Install CronTimer. Use Plugin Image")
        self["detail5"] = Label("Get assistance, support and help.")

    # Initialize the actions (key mappings)
    def initActions(self):
        self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions"], {
            "ok": self.okClicked,
            "cancel": self.close,
            "left": self.keyLeft,
            "right": self.keyRight,
            "red": self.redPressed,
            "green": self.greenPressed,
            "yellow": self.yellowPressed,
            "blue": self.bluePressed
        }, -1)

    # Handle OK button click
    def okClicked(self):
        # Determine action based on the selected icon
        if self.selectedIcon == 1:
            self.session.open(SubMenu, "Tools", [
                ("Free Cline Access", self.askForUserPreference),
                ("Update FCA Script", self.askForUpdateFca),
                ("Save Personal Lines", self.savePersonalLines)  # recoded from lululla
            ])
        elif self.selectedIcon == 2:
            self.session.open(SubMenu, "Extras", [
                ("Addons", [
                    ("Panels", [
                        ("AJpanel", self.runAJPanel),
                        ("Levi45 Addon", self.runLevi45Addon),
                        ("LinuxsatPanel addons", self.runLinuxsatPanel)
                    ]),
                ]),
                ("Media", [
                    ("ArchivCZSK", self.runArchivCZSK),
                    ("CSFD", self.runCSFD)
                ]),
                ("Dependencies", [
                    ("CCCAM.CFG/OSCAM.CFG/CCCAMDATAX/OSCAMDATAX", self.installCCCAMDATAX),
                    ("CURL", self.installCURL),
                    ("WGET", self.installWGET),
                    ("Python", self.installPython)

                ]),
                ("CAMs", [
                    ("SoftCAM feed", self.installSoftCAMFeed),
                    ("\"HomeMade\" config", self.installHomeMadeConfig)
                ])
            ])

        elif self.selectedIcon == 3:
            self.session.open(SubMenu, "Settings", [
                ("Panel", [
                    ("Update Panel", self.update)
                ])
            ])

        elif self.selectedIcon == 4:
            self.session.open(SubMenu, "Cronotabs", [
                ("CronTimer Install", self.installcron),
                ("CronTimer Start", self.crondStart),
                ("CronTimer Stop", self.crondStop),
            ])

        elif self.selectedIcon == 5:
            self.session.open(SubMenu, "Help", [
                ("FAQ", self.faq),
                ("Contact + Support", self.contactSupport),
                ("INFO", self.info)
            ])

    def savePersonalLines(self):
        """Save personal lines from text files"""
        self.session.openWithCallback(
            self.confirmSavePersonalLines,
            MessageBox,
            "This will copy your personal line files (cccamx.txt, oscamx.txt, ncamx.txt) to the personal lines directory.\n\nThese lines will be automatically added after each update.",
            MessageBox.TYPE_YESNO
        )

    def confirmSavePersonalLines(self, confirmed):
        if confirmed:
            files_copied = save_personal_lines_from_files()
            if files_copied:
                message = "Personal lines saved from:\n"
                for file in files_copied:
                    message += "- " + file + "\n"
                message += "\nThey will be automatically added after each update."
            else:
                message = "No personal line files found!\n\nPlease create one of these files:\n- /etc/cccamx.txt\n- /etc/oscamx.txt\n- /etc/ncamx.txt\n\nwith your personal C-lines and try again."
            self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=10)

    # recoded from lululla Prompts the user to confirm the installation of crontimer
    def installcron(self):
        self.askForConfirmation("Do you want to install Cron Script?", self.confirmInstallCron)

    def is_crond_running(self):
        output = popen("pgrep crond").read().strip()
        return bool(output)

    def on_init_cron(self):
        crond_process = self.is_crond_running()
        print("DEBUG: crond_process = %s" % crond_process)
        self["labrun"].hide()
        self["labstop"].hide()
        self.my_crond_run = crond_process
        if self.my_crond_run:
            self["labstop"].hide()
            self["labrun"].show()
            print("DEBUG: process cron running")
        else:
            self["labstop"].show()
            self["labrun"].hide()
            print("DEBUG: process cron stopped")

    def crondStart(self):
        from Components.Console import Console
        self.Console = Console()
        if not self.my_crond_run:
            print("DEBUG: Starting crond...")
            self.Console.ePopen("/usr/sbin/crond -c /var/spool/cron/crontabs", self.startStopCallback)
            self.session.open(MessageBox, "Please wait, starting crontimer!", MessageBox.TYPE_INFO, timeout=5)
        else:
            print("DEBUG: Stopping crond...")
            self.Console.ePopen("killall crond", self.startStopCallback)
            self.session.open(MessageBox, "Please wait, stopping crontimer!", MessageBox.TYPE_INFO, timeout=5)

    def startStopCallback(self, result=None, retval=None, extra_args=None):
        from time import sleep
        print("DEBUG: Callback triggered -> result=%s, retval=%s, extra_args=%s" % (result, retval, extra_args))
        sleep(3)
        self.on_init_cron()

    def confirmInstallCron(self, confirmed):
        if confirmed:
            source = "/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/root"
            destination = "/etc/cron/crontabs/root"
            command = "mkdir -p /etc/cron/crontabs;cp %s %s && chmod +x %s" % (source, destination, destination)
            self.session.open(Console, _("Installing cron job script..."), [command])

    def updateSelection(self):
        descriptions = ["Tools", "Extras", "Settings", "CronTimer", "Help"]
        self["detail"].hide()
        for i in range(1, 6):
            self["icon%s" % i].show()
            if i == self.selectedIcon:

                self["desc%s" % i].setText("^" + descriptions[i - 1] + "^")
                self["detail"].setText(self["detail%s" % i].getText())
                self["detail"].show()
            else:

                self["desc%s" % i].setText(descriptions[i - 1])

    # Handle Left key press # fixed lululla
    def keyLeft(self):
        # self.selectedIcon = 5 if self.selectedIcon == 1 else self.selectedIcon - 1
        self.selectedIcon = 5 if self.selectedIcon == 1 else self.selectedIcon - 1
        self.updateSelection()

    # Handle Right key press # fixed lululla
    def keyRight(self):
        # self.selectedIcon = 1 if self.selectedIcon == 5 else self.selectedIcon + 1
        self.selectedIcon = (self.selectedIcon % 5) + 1
        self.updateSelection()

    # Handle Red button press
    def redPressed(self):
        self.selectedIcon = 1
        self.updateSelection()
        self.okClicked()

    # Handle Green button press
    def greenPressed(self):
        self.selectedIcon = 2
        self.updateSelection()
        self.okClicked()

    # Handle Green button press
    def yellowPressed(self):
        self.selectedIcon = 3
        self.updateSelection()
        self.okClicked()

    # Handle Blue button press
    def bluePressed(self):
        self.selectedIcon = 5
        self.updateSelection()
        self.okClicked()

    # Prompt the user to confirm whether they want to update the script
    def askForUpdateFca(self):
        self.session.openWithCallback(self.UpdateFca, MessageBox, "Do you want to see the process?", MessageBox.TYPE_YESNO)

    # Handles the confirmation for installing FCA Script from Lululla git # fixed lululla
    def UpdateFca(self, confirmed):
        if confirmed:
            # First add personal lines if they exist
            add_personal_lines_to_configs()

            # Then update the script
            command = "wget -O %s 'https://raw.githubusercontent.com/Belfagor2005/SimpleZooomPanel/refs/heads/main/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Centrum/Tools/FCA.sh' && chmod +x %s" % (script_path, script_path)
            self.session.open(Console, _("Update FCA Script From Git..."), [command])

    # Prompt user to confirm whether they want to see the process (or background) for Free Cline Access # fixed lululla
    def askForUserPreference(self):
        self.session.openWithCallback(self.runScriptWithPreference, MessageBox, "Do you want to see the process?", MessageBox.TYPE_YESNO)

    # recoded from lululla # fixed lululla
    def runScriptWithPreference(self, confirmed):
        # First add personal lines if they exist
        add_personal_lines_to_configs()

        # Find configuration files
        print("DEBUG: Find CCcam file...")
        cccam_paths = findCccam()
        print("DEBUG: cccam_paths = %s" % cccam_paths)
        print("DEBUG: Find Oscam file...")
        oscam_paths = findOscam()
        print("DEBUG: oscam_paths = %s" % oscam_paths)

        # Step 1: Save backup before running script
        self.cccam_original_content = {}
        for cccam_path in set(cccam_paths):
            cccam_path = cccam_path.strip()
            if cccam_path:
                backup = prependToFile(cccam_path)
                self.cccam_original_content[cccam_path] = backup
                print("DEBUG: Backup for %s" % cccam_path)

        self.oscam_original_content = {}
        for oscam_path in set(oscam_paths):
            oscam_path = oscam_path.strip()
            if oscam_path:
                backup = prependToFile(oscam_path)
                self.oscam_original_content[oscam_path] = backup
                print("DEBUG: Backup for %s" % oscam_path)

        # Step 2: Execute script
        if confirmed:
            print("DEBUG: Execute script in console...")
            self.runScriptWithConsole()
        else:
            print("DEBUG: Execute script in background...")
            self.runScriptInBackground()

    def runScriptWithConsole(self):  # fixed lululla

        if exists(script_path):
            chmod(script_path, 0o777)
            self.session.open(Console,
                              title="Executing Free Cline Access Script",
                              cmdlist=[script_path],
                              finishedCallback=self.scriptFinished)

        else:
            self.session.open(MessageBox,
                              "Error: file not found\nSimpleZOOMPanel/Centrum/Tools/FCA.sh",
                              MessageBox.TYPE_ERROR,
                              timeout=10)

    def scriptFinished(self, result=None):  # fixed lululla
        print("DEBUG: Script finished, proceeding with file updates.")
        self.updateFilesWithBackup()

    def updateFilesWithBackup(self):
        for cccam_path, backup in self.cccam_original_content.items():
            ensure_directory_exists(cccam_path)
            new_content_raw = saveFileContent(cccam_path).strip()
            new_content = remove_backup_block(new_content_raw)
            final_content = backup.strip() + "\n" + new_content
            with open(cccam_path, 'w') as f:
                f.write(final_content.strip() + "\n")

        for oscam_path, backup in self.oscam_original_content.items():
            ensure_directory_exists(oscam_path)
            new_content_raw = saveFileContent(oscam_path).strip()
            new_content = remove_backup_block(new_content_raw)
            final_content = backup.strip() + "\n" + new_content
            if exists(oscam_path):
                with open(oscam_path, 'w') as f:
                    f.write(final_content.strip() + "\n")

        # 1. ADD personal lines to CCcam.cfg (always)
        add_personal_lines_to_cccam_only()

        # 2. CONVERT personal lines to OSCam/NCam (ALWAYS)
        convert_personal_lines_if_needed()

        print("DEBUG: EXECUTION FINISHED")

    # Run the script FCA in the background
    def runScriptInBackground(self):
        if self.script_running.is_set():
            self.session.open(MessageBox, "Please wait, the process is still running!", MessageBox.TYPE_INFO, timeout=5)
            return
        self.script_running.set()

        chmod(script_path, 0o777)
        threading.Thread(target=self.executeScript, args=(script_path,)).start()
        self.session.open(MessageBox, "Process has started. Please wait for completion!", MessageBox.TYPE_INFO, timeout=10)

    # Executes a script located at script_path
    def executeScript(self, script_path):
        try:
            # Run the script with shell access and capture the output
            result = subprocess.run(script_path, shell=True, capture_output=True, text=True)
            # Check if the script execution was successful
            if result.returncode != 0:
                self.session.open(MessageBox, "Error running script:\n" + result.stderr, MessageBox.TYPE_ERROR, timeout=15)
            else:
                # Split the output into pages to display
                PAGE_SIZE = 1000
                output_pages = [result.stdout[i:i + PAGE_SIZE] for i in range(0, len(result.stdout), PAGE_SIZE)]
                self.showOutputPages(output_pages, 0)
        except Exception as e:
            # Handle any exceptions and show an error message
            self.session.open(MessageBox, "Exception running script:" + str(e), MessageBox.TYPE_ERROR, timeout=15)
        finally:
            # Ensure the script_running flag is cleared after execution
            self.script_running.clear()

    # Dummy function to indicate unimplemented options
    def dummy(self):
        self.session.open(MessageBox, "This option is not yet implemented.", MessageBox.TYPE_INFO, timeout=5)

    # Prompts the user to confirm the installation of SoftCAM feed
    def installSoftCAMFeed(self):
        self.askForConfirmation("Do you want to install SoftCAM feed?", self.confirmInstallSoftCAMFeed)

    # Handles the confirmation for installing SoftCAM feed
    def confirmInstallSoftCAMFeed(self, confirmed):
        if confirmed:
            command = "wget -qO- --no-check-certificate http://updates.mynonpublic.com/oea/feed | bash"
            self.session.open(Console, _("Installing SoftCAM feed..."), [command])

    # Prompts the user to confirm the installation of HomeMade config
    def installHomeMadeConfig(self):
        self.askForConfirmation("Do you want to install \"HomeMade\" config?", self.confirmInstallHomeMadeConfig)

    # Handles the confirmation for installing HomeMade config
    def confirmInstallHomeMadeConfig(self, confirmed):
        if confirmed:
            try:
                # Define the download URL and path for the HomeMade config
                download_url = "https://drive.google.com/uc?export=download&id=1nWeOz_PncQ_kCRDkHO5E2xLt5OJ9fK6H"
                download_path = "/tmp/config.zip"

                # Download the config file
                with urlopen(download_url) as response, open(download_path, 'wb') as out_file:
                    out_file.write(response.read())

                # Define paths for old and new configuration files
                old_config_path = "/etc/tuxbox/config"
                new_config_path = "/etc/tuxbox/config_old"

                # Backup old config if it exists
                if exists(old_config_path):
                    rename(old_config_path, new_config_path)

                # Extract the new config file
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall("/etc/tuxbox/")

                self.session.open(MessageBox, "\"HomeMade\" config installed successfully. Please control your location of config. Default and also installed this way is /etc/tuxbox/config/!", MessageBox.TYPE_INFO, timeout=10)
            except Exception as e:
                # Handle errors during the installation process
                self.session.open(MessageBox, "Error installing HomeMade config:" + str(e), MessageBox.TYPE_ERROR, timeout=5)

    # Prompts the user to confirm the installation of CURL
    def installCURL(self):
        self.askForConfirmation("Do you want to install CURL?", self.confirmInstallCURL)

    # Handles the confirmation for installing CURL
    def confirmInstallCURL(self, confirmed):
        if confirmed:
            command = "opkg update && opkg install curl"
            self.session.open(Console, _("Installing CURL..."), [command])

    # Prompts the user to confirm the installation of WGET
    def installWGET(self):
        self.askForConfirmation("Do you want to install WGET?", self.confirmInstallWGET)

    # Handles the confirmation for installing WGET
    def confirmInstallWGET(self, confirmed):
        if confirmed:
            command = "opkg update && opkg install wget"
            self.session.open(Console, _("Installing WGET..."), [command])

    # Prompts the user to confirm the installation of Python
    def installPython(self):
        self.askForConfirmation("Do you want to install Python?", self.confirmInstallPython)

    # Handles the confirmation for installing Python
    def confirmInstallPython(self, confirmed):
        if confirmed:
            command = (
                "opkg update; "
                "opkg install python3; "
                "wget https://bootstrap.pypa.io/get-pip.py; "
                "python3 get-pip.py; "
                "pip3 install requests"
            )
            self.session.open(Console, _("Installing Python..."), [command])

    # Prompts the user to confirm the addition of CCCAM/CCCAMDATAX/OSCAMDATAX
    def installCCCAMDATAX(self):
        self.askForConfirmation("Do you want to add CCCAM.CFG/OSCAM.CFG/CCCAMDATAX/OSCAMDATAX?", self.confirmInstallCCCAMDATAX)

    # Handles the confirmation for adding CCCAM/CCCAMDATAX/OSCAMDATAX
    def confirmInstallCCCAMDATAX(self, confirmed):
        if confirmed:
            try:
                # Define paths for CCCAM/OSCAM and related config files
                cccam_cfg_path = "/etc/CCcam.cfg"
                oscam_cfg_path = "/etc/oscam.cfg"
                cccamdatax_cfg_path = "/etc/CCcamDATAx.cfg"
                oscamdatax_cfg_path = "/etc/OscamDATAx.cfg"

                # Check if the config files already exist
                if exists(cccam_cfg_path) and exists(cccamdatax_cfg_path):
                    self.session.open(MessageBox, "CCCAM/OSCAM/CCCAMDATAX/OSCAMDATAX already added.", MessageBox.TYPE_INFO, timeout=5)
                else:
                    # Create the config files if they do not exist
                    cfg_paths = [cccam_cfg_path, oscam_cfg_path, cccamdatax_cfg_path, oscamdatax_cfg_path]
                    for path in cfg_paths:
                        if not exists(path):
                            open(path, 'a').close()
                    self.session.open(MessageBox, "CCCAM.CFG/OSCAM.CFG/CCCAMDATAX/OSCAMDATAX added successfully.", MessageBox.TYPE_INFO, timeout=5)
            except Exception as e:
                # Handle errors during the addition process
                self.session.open(MessageBox, "Error installing CCCAM.CFG/OSCAM.CFG/CCCAMDATAX/OSCAMDATAX: " + str(e), MessageBox.TYPE_ERROR, timeout=15)

    # Installs AJPanel
    def runAJPanel(self):
        self.session.open(Console, _("Installing AJPanel..."), [
            "/bin/sh -c 'opkg install https://github.com/AMAJamry/AJPanel/raw/main/enigma2-plugin-extensions-ajpanel_v9.4.0_all.ipk'"
        ])

    # Installs Levi45Addon
    def runLevi45Addon(self):
        self.session.open(Console, _("Installing Levi45Addon..."), [
            'wget -q --no-check-certificate https://raw.githubusercontent.com/levi-45/Addon/main/installer.sh -O - | /bin/sh'
        ])

    # Installs LinuxsatPanel addons recoded from lululla
    def runLinuxsatPanel(self):
        self.session.open(Console, _("Installing LinuxsatPanel addons..."), [
            'wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/LinuxsatPanel/main/installer.sh -O - | /bin/sh'
        ])

    # Installs ArchivCZSK
    def runArchivCZSK(self):
        self.session.open(Console, _("Installing ArchivCZSK..."), [
            "/bin/sh -c 'wget -q --no-check-certificate https://raw.githubusercontent.com/archivczsk/archivczsk/main/build/archivczsk_installer.sh -O /tmp/archivczsk_installer.sh && /bin/sh /tmp/archivczsk_installer.sh'"
        ])

    # Installs CSFD
    def runCSFD(self):
        self.session.open(Console, _("Installing CSFD..."), [
            "/bin/sh -c 'opkg install https://github.com/skyjet18/enigma2-plugin-extensions-csfd/releases/download/v18.00/enigma2-plugin-extensions-csfd_18.00-20230919_all.ipk'"
        ])

    # simply the update
    def update(self):
        # First add your personal lines if they exist
        add_personal_lines_to_configs()

        self.session.open(Console, _("Updating package..."), [
            # "wget -O /tmp/package.ipk 'https://drive.google.com/uc?export=download&id=1c01xd-idAwPc6rDO8TqGijXG8niJ52Sv' > /dev/null 2>&1 && opkg install /tmp/package.ipk"
            'wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/SimpleZooomPanel/main/installer.sh -O - | /bin/sh'
        ])

    # Displays FAQ information in paginated format recoded from lululla
    def faq(self):
        faq_text = (
            ("General Questions\n") +
            ("Q1: What is the purpose of the Simple ZOOM Panel plugin?\n") +
            ("A1: The Simple ZOOM Panel plugin provides a user-friendly interface to access various tools, extras, settings, and help for your Enigma2-based system.\n\n") +
            ("Q2: How do I set up the automatic installation of servers?\n") +
            ("A2: Use CRON. In CRON, select the AUTFCA.sh script and choose your desired time.\n\n") +
            ("Personal Lines Management\n") +
            ("Q3: How do I set up and use my personal lines?\n") +
            ("A3: You have two options:\n\n") +
            ("OPTION 1 - Manual Files:\n") +
            ("• Create /etc/cccamx.txt with your C-lines (CCcam format)\n") +
            ("• Create /etc/oscamx.txt with your OSCam readers\n") +
            ("• Create /etc/ncamx.txt with your NCam readers\n") +
            ("• Use 'Save Personal Lines' in Tools menu to save them\n\n") +
            ("OPTION 2 - Automatic Extraction:\n") +
            ("• Use 'Save Personal Lines' to automatically extract personal lines\n") +
            ("• from your existing CCcam.cfg and oscam.server files\n") +
            ("• The system will filter out free servers and keep only personal lines\n\n") +
            ("Q4: When are my personal lines added?\n") +
            ("A4: Your personal lines are automatically added after:\n") +
            ("• Free Cline Access updates\n") +
            ("• FCA Script updates\n") +
            ("• Panel updates\n") +
            ("• Manual execution of Save Personal Lines\n\n") +
            ("Q5: I see duplicate readers in my config, what should I do?\n") +
            ("A5: This happens if you run 'Save Personal Lines' multiple times.\n") +
            ("Solution: Edit your config file and remove duplicate sections,\n") +
            ("then use Save Personal Lines again. The system will prevent\n") +
            ("future duplications.\n\n") +
            ("Installation and Setup\n") +
            ("Q6: How do I install the Simple ZOOM Panel plugin?\n") +
            ("A6: The plugin can be installed from the IPK. Ensure you have the necessary permissions and dependencies to install the plugin.\n\n") +
            ("Usage\n") +
            ("Q7: How do I navigate through the Simple ZOOM Panel menu?\n") +
            ("A7: Use the left and right arrow keys to navigate between different icons (Tools, Extras, Settings, Help). Press the OK button to select an option. The red, green, yellow, and blue buttons also correspond to specific menu options.\n\n") +
            ("Q8: What actions are available in each menu?\n") +
            ("A8:\n") +
            ("- Tools: Free Cline Access, Update FCA Script, Save Personal Lines\n") +
            ("- Extras: Install addons, media players, dependencies, and CAMs\n") +
            ("- Settings: Update the panel\n") +
            ("- CronTimer: Manage automatic script execution\n") +
            ("- Help: Access FAQs, support, and information\n\n") +
            ("Script Execution\n") +
            ("Q9: How do I execute scripts from the Simple ZOOM Panel?\n") +
            ("A9: Selecting certain tools or addons will prompt you to run scripts. You can choose to view the process in a console or let it run in the background. The plugin ensures you are informed about the status and completion of the scripts.\n\n") +
            ("Q10: What happens if a script is already running?\n") +
            ("A10: If a script is already running, you will receive a message informing you to wait until the current process is completed.\n\n") +
            ("Troubleshooting\n") +
            ("Q11: I encountered an error while running a script. What should I do?\n") +
            ("A11: If an error occurs during script execution, the plugin will display the error message. Check the message for details and ensure all dependencies are installed. You can also review the script output if necessary.\n\n") +
            ("Q12: My personal lines are not being saved/added. What's wrong?\n") +
            ("A12: Check the following:\n") +
            ("• File permissions: Ensure you can write to /etc/personal_lines/\n") +
            ("• File format: C-lines must start with 'C: ' for CCcam\n") +
            ("• File location: Place files in /etc/cccamx.txt or /usr/script/cccamx.txt\n") +
            ("• Content: Files must contain valid configuration lines\n\n") +
            ("Q13: The plugin says \"This option is not yet implemented.\" What does this mean?\n") +
            ("A13: This message indicates that the selected feature is planned but not yet available in the current version of the plugin.\n\n") +
            ("Advanced Features\n") +
            ("Q14: How do I install additional components like CURL, WGET, etc.? \n") +
            ("A14: Navigate to the Extras menu, select the component you wish to install, and follow the prompts. Confirm your action, and the plugin will handle the installation process.\n\n") +
            ("Q15: The \"HomeMade\" config is used for what?\n") +
            ("A15: It is an optimized OSCam config for free servers. Note that this config may not always be the best option, and you may need to configure your own.\n\n") +
            ("Q16: How does CronTimer work with personal lines?\n") +
            ("A16: When CronTimer runs automatic updates, it will preserve your\n") +
            ("personal lines and add them back after updating free servers.\n\n") +
            ("File Locations Reference\n") +
            ("Q17: Where are the personal line files stored?\n") +
            ("A17:\n") +
            ("• Input files: /etc/cccamx.txt, /etc/oscamx.txt, /etc/ncamx.txt\n") +
            ("• Backup files: /etc/personal_lines/cccamx, etc.\n") +
            ("• CCcam config: /etc/CCcam.cfg\n") +
            ("• OSCam config: /etc/tuxbox/config/oscam.server\n") +
            ("• NCam config: /etc/tuxbox/config/ncam.server\n\n") +
            ("Customization\n") +
            ("Q18: Can I customize the plugin's appearance or functionality?\n") +
            ("A18: Currently, the plugin does not support customization of its appearance. However, you can suggest new features or improvements to the developer.\n\n") +
            ("Development and Contribution\n") +
            ("Q19: I am a developer. How can I contribute to the Simple ZOOM Panel plugin?\n") +
            ("A19: Contributions are welcome. Review the plugin's source code to understand its structure and functionality. You can contribute by adding new features, fixing bugs, or improving documentation. Contact me for more details.\n\n") +
            ("Contact and Support\n") +
            ("Q20: Where can I get help if I encounter issues with the plugin?\n") +
            ("A20: Visit the Help section within the plugin for FAQs, contact information, and support options. You can also reach out to the Enigma2 community on linuxSatSupport for additional assistance.\n")
        )

        PAGE_SIZE = 800
        output_pages = [faq_text[i:i + PAGE_SIZE] for i in range(0, len(faq_text), PAGE_SIZE)]

        # Show the first page of the FAQ
        self.showOutputPages(output_pages, 0)

    # recoded from lululla
    def showOutputPages(self, pages, current_page):
        if current_page < len(pages):
            message = "Script output (Page %s / %s):\n%s" % (current_page + 1, len(pages), pages[current_page])
            try:
                self.session.openWithCallback(
                    lambda ret: self.showOutputPages(pages, current_page + 1 if ret else max(current_page - 1, 0)),
                    MessageBox,
                    message,
                    MessageBox.TYPE_INFO
                )
            except Exception as e:
                print("Error opening MessageBox: %s" % str(e))

    # Provides contact information for support
    def contactSupport(self):
        self.session.open(MessageBox, "If you're looking for support or have questions about the Simple Zoom Panel, you can visit the following link: https://www.linuxsat-support.com/thread/157589-simple-zoom-panel/. This forum thread is a great resource for troubleshooting and getting assistance from the community. Feel free to check it out for detailed guidance and support!", MessageBox.TYPE_INFO, timeout=30)

    # Displays information about the plugin and its creators
    def info(self):
        message = (
            "Creators:\n"
            "- E2W!zard (this whole thing!)\n"
            "- HIUMAN\n"
            "- Bextrh (Servers+Convertor+RestartCAM and also creator of CCcam free server downloader (ZOOM))\n\n"
            "Special Thanks to:\n"
            "- Viliam\n"
            "- Lvicek07\n"
            "- Kakamus\n"
            "- Axy\n"
            "- Lululla\n\n"
            "Overview:\n"
            "The Simple ZOOM Panel plugin provides an intuitive and user-friendly (somewhat) interface for Enigma2-based systems. "
            "It offers a centralized hub for accessing tools, extras, settings, and help, enhancing the overall user experience."
        )
        self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=30)

    # Runs a given command and handles success or failure
    def runCommand(self, command, success_msg, error_msg):
        if self.script_running.is_set():
            self.session.open(MessageBox, "Please wait, the process is still running!", MessageBox.TYPE_INFO, timeout=15)
            return
        self.script_running.set()
        threading.Thread(target=self.executeCommand, args=(command, success_msg, error_msg)).start()
        self.session.open(MessageBox, "Process has started. Please wait for completion.", MessageBox.TYPE_INFO, timeout=10)

    # Executes command on a given input "yes"
    def askForConfirmation(self, message, callback):
        self.session.openWithCallback(callback, MessageBox, message, MessageBox.TYPE_YESNO)

    # Executes a given command and shows appropriate messages based on the result
    def executeCommand(self, command, success_msg, error_msg):
        try:
            # Run the command with shell access and capture the output
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            # Check if the command execution was successful
            if result.returncode != 0:
                self.session.open(MessageBox, error_msg + ":\n" + result.stderr, MessageBox.TYPE_ERROR, timeout=15)
            else:
                # Split the output into pages to display
                PAGE_SIZE = 1000
                output_pages = [result.stdout[i:i + PAGE_SIZE] for i in range(0, len(result.stdout), PAGE_SIZE)]
                self.showOutputPages(output_pages, 0)
                self.session.open(MessageBox, success_msg, MessageBox.TYPE_INFO, timeout=5)
        except Exception as e:
            # Handle any exceptions and show an error message
            self.session.open(MessageBox, "Exception running command:" + str(e), MessageBox.TYPE_ERROR, timeout=15)
        finally:
            # Ensure the script_running flag is cleared after execution
            self.script_running.clear()


class SubMenu(Screen):
    skin = """
        <screen name="SubMenu" position="center,center" size="600,200" title="Sub Menu">
            <widget name="menu" position="10,10" size="580,380" scrollbarMode="showOnDemand" />
        </screen>"""

    # Initialize the submenu screen by setting up session, title, menu items, and action mappings.
    def __init__(self, session, title, menuItems):
        self.session = session
        Screen.__init__(self, session)
        self.setTitle(title)
        self.menuItems = menuItems
        self["menu"] = MenuList([item[0] for item in menuItems])
        self["actions"] = ActionMap(["OkCancelActions"], {
            "ok": self.okClicked,
            "cancel": self.close
        }, -1)

    def okClicked(self):
        choiceIndex = self["menu"].getSelectionIndex()
        choice = self.menuItems[choiceIndex]
        # Open a new submenu if the choice contains a list of items
        if isinstance(choice[1], list):
            self.session.open(SubMenu, choice[0], choice[1])
        else:
            # Execute the selected action
            choice[1]()


def main(session, **kwargs):
    # Opens the main menu of the plugin
    session.open(MainMenus)


def Plugins(**kwargs):
    # Register the plugin for the plugin menu
    return [
        PluginDescriptor(
            name='Simple ZOOM Panel',
            description=_('It is like ZOOM but simpler, and also a panel.'),
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon='/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/plugin.png',
            fnc=main
        )
    ]
