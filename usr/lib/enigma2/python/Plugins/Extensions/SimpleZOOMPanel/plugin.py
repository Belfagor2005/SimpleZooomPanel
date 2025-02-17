#!/usr/bin/python
# -*- coding: utf-8 -*-

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Pixmap import Pixmap
from Plugins.Plugin import PluginDescriptor
from Screens.Console import Console
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from os import mkdir, chmod
from os.path import exists
from six.moves import range

import os
import subprocess
import sys
import threading
import zipfile

PY3 = sys.version_info.major >= 3

if PY3:
    from urllib.request import urlopen
else:
    from urllib2 import urlopen

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
                <eLabel name="" position="7,3" size="350,44" text="Simple ZOOM Panel 2.2.5" font="Regular; 26" foregroundColor="#707070" />
                <eLabel name="" position="445,1" size="66,26" text="created :" font="Regular; 15" foregroundColor="green" />
                <eLabel name="" position="517,2" size="81,23" text="E2W!zard" font="Regular; 16" />
                <eLabel name="" position="518,24" size="73,25" font="Regular; 16" text="HIUMAN" />
            </screen>"""

    # Constructor to initialize the MainMenus screen
    def __init__(self, session):
        self.session = session
        Screen.__init__(self, session)  # Initialize the base class
        if not exists("/usr/script"):
            mkdir("/usr/script", 0o755)
        self.initUI()  # Set up the user interface
        self.initActions()  # Set up the actions (key mappings)
        self.selectedIcon = 1  # Start with the first icon selected
        self.script_running = threading.Event()  # Event to manage script running state
        self.updateSelection()  # Update the selection display

        self.my_crond_run = False

        self.on_init_cron()

    # Initialize the user interface elements
    def initUI(self):
        # Set up cront
        self["lab2"] = Label(_("Current Status:"))
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

    def is_crond_running(self):
        output = os.popen("pgrep crond").read().strip()
        return bool(output)  # Restituisce True se crond è in esecuzione, False altrimenti

    def on_init_cron(self):
        crond_process = self.is_crond_running()
        print("DEBUG: crond_process =", crond_process)  # Stampa lo stato attuale di crond
        self["labrun"].hide()
        self["labstop"].hide()
        self.my_crond_run = crond_process  # Usa direttamente il valore booleano
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
        print("DEBUG: Callback triggered -> result={}, retval={}, extra_args={}".format(result, retval, extra_args))
        sleep(3)
        self.on_init_cron()

    # Handle OK button click
    def okClicked(self):
        # Determine action based on the selected icon
        if self.selectedIcon == 1:
            self.session.open(SubMenu, "Tools", [
                ("Free Cline Access", self.askForUserPreference)])
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
                    ("CURL", self.installCURL),
                    ("WGET", self.installWGET),
                    ("Python", self.installPython),
                    ("CCCAM.CFG/OSCAM.CFG/CCCAMDATAX/OSCAMDATAX", self.installCCCAMDATAX)
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
                ("CronTimer Stop", self.crondStart),
            ])

        elif self.selectedIcon == 5:
            self.session.open(SubMenu, "Help", [
                ("FAQ", self.faq),
                ("Contact + Support", self.contactSupport),
                ("INFO", self.info)
            ])

    # Prompts the user to confirm the installation of crontimer
    def installcron(self):
        self.askForConfirmation("Do you want to install Cron Script?", self.confirmInstallCron)

    # Handles the confirmation for installing Cron script
    def confirmInstallCron(self, confirmed):
        if confirmed:
            source = "/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/root"
            destination = "/etc/cron/crontabs/root"
            command = "mkdir -p /etc/cron/crontabs;cp %s %s && chmod +x %s" % (source, destination, destination)
            self.session.open(Console, _("Installing cron job script..."), [command])

    # Update the selection display based on the currently selected icon
    def updateSelection(self):
        descriptions = ["Tools", "Extras", "Settings", "CronTimer", "Help"]
        self["detail"].hide()  # Hide detail by default
        for i in range(1, 6):
            self["icon" + str(i)].show()  # Show all icons
            if i == self.selectedIcon:
                # Highlight the selected icon
                self["desc" + str(i)].setText("^" + descriptions[i - 1] + "^")
                self["detail"].setText(self["detail" + str(i)].getText())  # Update detail text
                self["detail"].show()  # Show detail text
            else:
                # Set default description for non-selected icons
                self["desc" + str(i)].setText(descriptions[i - 1])

    # Handle Left key press
    def keyLeft(self):
        self.selectedIcon = 4 if self.selectedIcon == 1 else self.selectedIcon - 1
        self.updateSelection()

    # Handle Right key press
    def keyRight(self):
        self.selectedIcon = 1 if self.selectedIcon == 4 else self.selectedIcon + 1
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

    # Prompt user to confirm whether they want to see the process (or background) for Free Cline Access
    def askForUserPreference(self):
        self.session.openWithCallback(self.runScriptWithPreference, MessageBox, "Do you want to see the process?", MessageBox.TYPE_YESNO)

    # Execute script based on user preference
    def runScriptWithPreference(self, confirmed):
        if confirmed:
            self.runScriptWithConsole()  # Show the process in a console
        else:
            self.runScriptInBackground()  # Run the script in the background

    # Run the FCA script with console output
    def runScriptWithConsole(self):
        script_path = "/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Centrum/Tools/FCA.sh"
        if os.path.exists(script_path):
            chmod(script_path, 0o777)
            # Execute the script
            self.session.open(Console, title="Executing Free Cline Access Script", cmdlist=[script_path])
        else:
            self.session.open(MessageBox, "Error: file not found\nSimpleZOOMPanel/Centrum/Tools/FCA.sh", MessageBox.TYPE_ERROR, timeout=10)

    # Script has been finished
    def scriptFinished(self, result):
        self.script_running.clear()
        self.session.open(MessageBox, "Script execution finished!", MessageBox.TYPE_INFO, timeout=5)

    # Run the script FCA in the background
    def runScriptInBackground(self):
        if self.script_running.is_set():
            self.session.open(MessageBox, "Please wait, the process is still running!", MessageBox.TYPE_INFO, timeout=5)
            return
        self.script_running.set()
        script_path = "/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Centrum/Tools/FCA.sh"
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

    # Shows the paginated output of the script execution
    def showOutputPages(self, pages, current_page):
        if current_page < len(pages):
            message = "Script output (Page {} / {}):\n{}".format(current_page + 1, len(pages), pages[current_page])
            # Open a MessageBox with the current page of output
            try:
                self.session.openWithCallback(lambda ret: self.showOutputPages(pages, str(current_page + 1) if ret else max(current_page - 1, 0)),
                                              MessageBox(message,
                                              MessageBox.TYPE_INFO))
            except Exception as e:
                print("Error opening MessageBox:", str(e))

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
                if os.path.exists(old_config_path):
                    os.rename(old_config_path, new_config_path)

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
                if os.path.exists(cccam_cfg_path) and os.path.exists(cccamdatax_cfg_path):
                    self.session.open(MessageBox, "CCCAM/OSCAM/CCCAMDATAX/OSCAMDATAX already added.", MessageBox.TYPE_INFO, timeout=5)
                else:
                    # Create the config files if they do not exist
                    cfg_paths = [cccam_cfg_path, oscam_cfg_path, cccamdatax_cfg_path, oscamdatax_cfg_path]
                    for path in cfg_paths:
                        if not os.path.exists(path):
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

    # Installs TiVuStream addons
    def runLinuxsatPanel(self):
        self.session.open(Console, _("Installing TiVuStream addons..."), [
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
        self.session.open(Console, _("Updating package..."), [
            "wget -O /tmp/package.ipk 'https://drive.google.com/uc?export=download&id=1c01xd-idAwPc6rDO8TqGijXG8niJ52Sv' > /dev/null 2>&1 && opkg install /tmp/package.ipk"
        ])

    # Displays FAQ information in paginated format
    def faq(self):
        faq_text = (("General Questions\n") +
                    ("Q1: What is the purpose of the Simple ZOOM Panel plugin?\n") +
                    ("A1: The Simple ZOOM Panel plugin provides a user-friendly interface to access various tools, extras, settings, and help for your Enigma2-based system.\n\n") +
                    ("Q2: How do I set up the automatic installation of servers?\n") +
                    ("A2: Use CRON. In CRON, select the AUTFCA.sh script and choose your desired time.\n\n") +
                    ("Q3: How do I set up my personal lines?\n") +
                    ("A3: Use one of the DATAx (You have to manually install it in dependencies!. Also there must be no cccam.cfg oscam and cccam datax files!) file in /etc/ directory. You can choose between CCCAM and OSCAM. Now every time you use Free Cline Access it will also add your personal lines.\n\n") +
                    ("Installation and Setup\n") +
                    ("Q4: How do I install the Simple ZOOM Panel plugin?\n") +
                    ("A4: The plugin can be installed from the IPK. Ensure you have the necessary permissions and dependencies to install the plugin.\n\n") +
                    ("Usage\n") +
                    ("Q5: How do I navigate through the Simple ZOOM Panel menu?\n") +
                    ("A5: Use the left and right arrow keys to navigate between different icons (Tools, Extras, Settings, Help). Press the OK button to select an option. The red, green, yellow, and blue buttons also correspond to specific menu options.\n\n") +
                    ("Q6: What actions are available in each menu?\n") +
                    ("A6:\n") +
                    ("- Tools: Access utility tools like Free Cline Access.\n") +
                    ("- Extras: Install and manage addons such as AJPanel, SatVenusPanel, and media extensions like ArchivCZSK.\n") +
                    ("- Settings: Update the panel.\n") +
                    ("- Help: Access FAQs, support, and information.\n\n") +
                    ("Script Execution\n") +
                    ("Q7: How do I execute scripts from the Simple ZOOM Panel?\n") +
                    ("A7: Selecting certain tools or addons will prompt you to run scripts. You can choose to view the process in a console or let it run in the background. The plugin ensures you are informed about the status and completion of the scripts.\n\n") +
                    ("Q8: What happens if a script is already running?\n") +
                    ("A8: If a script is already running, you will receive a message informing you to wait until the current process is completed.\n\n") +
                    ("Troubleshooting\n") +
                    ("Q9: I encountered an error while running a script. What should I do?\n") +
                    ("A9: If an error occurs during script execution, the plugin will display the error message. Check the message for details and ensure all dependencies are installed. You can also review the script output if necessary.\n\n") +
                    ("Q10: The plugin says \"This option is not yet implemented.\" What does this mean?\n") +
                    ("A10: This message indicates that the selected feature is planned but not yet available in the current version of the plugin.\n\n") +
                    ("Advanced Features\n") +
                    ("Q11: How do I install additional components like CURL, WGET, etc.? \n") +
                    ("A11: Navigate to the Extras menu, select the component you wish to install, and follow the prompts. Confirm your action, and the plugin will handle the installation process.\n\n") +
                    ("Q12: The \"HomeMade\" config is used for what?\n") +
                    ("A12: It is an optimized OSCam config for free servers. Note that this config may not always be the best option, and you may need to configure your own.\n\n") +
                    ("Customization\n") +
                    ("Q13: Can I customize the plugin's appearance or functionality?\n") +
                    ("A13: Currently, the plugin does not support customization of its appearance. However, you can suggest new features or improvements to the developer.\n\n") +
                    ("Development and Contribution\n") +
                    ("Q14: I am a developer. How can I contribute to the Simple ZOOM Panel plugin?\n") +
                    ("A14: Contributions are welcome. Review the plugin's source code to understand its structure and functionality. You can contribute by adding new features, fixing bugs, or improving documentation. Contact me for more details.\n\n") +
                    ("Contact and Support\n") +
                    ("Q15: Where can I get help if I encounter issues with the plugin?\n") +
                    ("A15: Visit the Help section within the plugin for FAQs, contact information, and support options. You can also reach out to the Enigma2 community on linuxSatSupport for additional assistance.\n")
                    )

        PAGE_SIZE = 800
        output_pages = [faq_text[i:i + PAGE_SIZE] for i in range(0, len(faq_text), PAGE_SIZE)]

        # Show the first page of the FAQ
        self.showOutputPages(output_pages, 0)

    # Provides contact information for support
    def contactSupport(self):
        self.session.open(MessageBox, "If you’re looking for support or have questions about the Simple Zoom Panel, you can visit the following link: https://www.linuxsat-support.com/thread/157589-simple-zoom-panel/. This forum thread is a great resource for troubleshooting and getting assistance from the community. Feel free to check it out for detailed guidance and support!", MessageBox.TYPE_INFO, timeout=30)

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
            "- Axy\n\n"
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

    # Handles the OK button click in the submenu
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
        PluginDescriptor(name='Simple ZOOM Panel',
                         description=_('It is like ZOOM but simpler, and also a panel.'),
                         where=PluginDescriptor.WHERE_PLUGINMENU,
                         icon='/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel/Graphics/plugin.png',
                         fnc=main),
    ]
