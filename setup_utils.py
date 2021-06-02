import os
import json
import platform
import subprocess
import re
import socket
from getpass import getpass
import werkzeug.security

PORT = 5000
UPNP_DESCRIPTION = "CattleDB"

def show_server():
    print(r" ____              __    __    ___           ____    ____")
    print(r"/\  _`\           /\ \__/\ \__/\_ \         /\  _`\ /\  _`\ ")
    print(r"\ \ \/\_\     __  \ \ ,_\ \ ,_\//\ \      __\ \ \/\ \ \ \ \ \ ")
    print(r" \ \ \/_/_  /'__`\ \ \ \/\ \ \/ \ \ \   /'__`\ \ \ \ \ \  _ <'")
    print(r"  \ \ \ \ \/\ \ \.\_\ \ \_\ \ \_ \_\ \_/\  __/\ \ \_\ \ \ \ \ \ ")
    print(r"   \ \____/\ \__/.\_\\ \__\\ \__\/\____\ \____\\ \____/\ \____/")
    print(r"    \/___/  \/__/\/_/ \/__/ \/__/\/____/\/____/ \/___/  \/___/")
    print(r"")
    print(r"")
    print(r"")
    print("Welcome to CattleDB. Just leave this window open and your records will be accessible from any device.")
    print()
    if not os.path.exists("config.json") or not os.path.exists("cattle.db"):
        setup_cattle_db()
    still_using_wan = False
    if get_using_wan():
        print("Checking that your connection is still configured correctly... this may take a few seconds")
        still_using_wan = True
        if check_for_upnp_rule():
            print("Good to go!")
            print()
        else:
            print("Connection not configured correctly. Attempting to fix!")
            if add_upnp_rule():
                print("Fixed! Good to go!")
                print()
            else:
                print()
                print("Whoops! Something went wrong. We couldn't automatically configure your connection.")
                print(f"Your records will still be accessible on {get_network_ssid()}")
                print("It may still be possible to set up online access manually!")
                print("Contact the developer for more information.")
                print()
                still_using_wan = False

    if still_using_wan:
        print("If you are on the same network as this computer ({}), connect using this link:".format(get_network_ssid()))
        print("http://" + get_private_ip() + ":" + str(PORT))
        print()
        print("If you are on a different network (not {}) connect using:".format(get_network_ssid()))
        
        print("http://" + get_public_ip() + ":" + str(PORT))
    else:
        print(f"You can access your from any device (as long as it's connected to {get_network_ssid()}) at:")
        print("http://" + get_private_ip() + ":" + str(PORT))
    print()
    #Attempt to silence app.run() output
    #with contextlib.redirect_stdout(io.StringIO()):

def get_private_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # connect to the server on local computer
    s.connect(("8.8.8.8", 80))
    private_ip = s.getsockname()[0]
    s.close()
    return private_ip

def get_public_ip():
    return requests.get("https://www.wikipedia.org").headers["X-Client-IP"]

def get_network_ssid():
    if platform.system() == "Windows":
        return subprocess.check_output("powershell.exe (get-netconnectionProfile).Name", shell=True).strip().decode("UTF-8")       
    # Not Windows. Works on Manjaro, presumably other distros, IDK about MacOS
    subprocess_result = subprocess.Popen('iwgetid',shell=True,stdout=subprocess.PIPE)
    subprocess_output = subprocess_result.communicate()[0],subprocess_result.returncode
    if subprocess_output[0] == b"":
        return "<CURRENTLY OFFLINE>"
    return re.search(r'"(.*?)"',subprocess_output[0].decode('utf-8')).group(0).replace("\"","")

def setup_cattle_db():
    print("There are just a couple steps to get started:")
    print()
    if not os.path.exists("cattle.db"):
        print("The database hasn't been created yet. Would you like to:")
        print("1) Create a new database")
        print("2) Import an existing database")
        print()
        print("(If you aren't sure, choose 1)")
        response = ""
        while response != "1" and response != "2":
            response = input("Please type \"1\" or \"2\": ")
            if response == "1":
                with app.app_context():
                    db.create_all()
                    db.session.commit()
                print("Database created!")
            elif response == "2":
                print("Please copy your \"cattle.db\" file to this folder...")
                while not os.path.exists("cattle.db"):
                    time.sleep(1)
                print()
                print("Database imported!")
                print()
    if not os.path.exists("config.json"):
        print("The configuration file hasn't been created yet. Would you like to:")
        print("1) Create a new configuration")
        print("2) Import an old configuration")
        print()
        print("(If you aren't sure, choose 1)")
        response = ""
        while response != "1" and response != "2":
            response = input("Please type \"1\" or \"2\": ")
            if response == "1":
                generate_config()
            elif response == "2":
                print("Please copy your \"config.json\" file to this folder...")
                while not os.path.exists("config.json"):
                    time.sleep(1)
                print("Configuration imported!")
    print()
    print("Good to go!")
    print()

def generate_config():
    print("Creating a new configuration: ")
    print()
    users = create_users()
    using_wan = prompt_wan_lan()
    if using_wan:
        print()
        print("Setting up online access... this may take a few seconds")
        print()
        if not check_for_upnp_rule():
            if add_upnp_rule():
                print()
                print("Your records are now accessible online")
                print()
            else:
                print()
                print("Whoops! Something went wrong. We couldn't automatically configure your connection.")
                print(f"Your records will still be accessible on {get_network_ssid()}")
                print("It may still be possible to set up online access manually!")
                print("Contact the developer for more information.")
                print()
                using_wan = False
        else:
            print("Already set up. (We didn't do anything)")
    config_dict = {
        "users":users,
        "using_wan":using_wan
    }
    config_json = json.dumps(config_dict, indent=4)
    with open("config.json", "w") as file:
        file.write(config_json)
    print()
    print("Configuration created!")
    print()

def create_users():
    print("Please create a username.")
    print("This will be used to log in and will be used")
    print("to distinguish between your cows, and cows")
    print("owned by others, like the one's you've sold.")

    print("You can create multiple users using commas and spaces (\", \") like so:")
    print("Jesse James, Billy the Kid, Butch Cassidy")
    print("")
    user_strings = input("Enter your name(s): ").split(", ")
    print()
    print("You'll now be prompted to choose a password. (The cursor will not move)")
    print()
    users = []
    for username in user_strings:
        password = getpass(f"Enter a password for {username}: ")
        hashed_password = werkzeug.security.generate_password_hash(password)
        users.append({"username":username,"hashed_password":hashed_password})
    print()
    print("Users created")
    print()
    return users

def prompt_wan_lan():
    print()
    print("Would you like to make you cattle records accessible online?")
    print()
    print("Choosing \"yes\" will configure your internet connection to allow you")
    print("to access your records from anywhere. However, it will be less secure")
    print()
    print("Choosing \"no\" will be more secure, however, you'll only be able to")
    print(f"access your records from this network ({get_network_ssid()}).")
    print()
    response = input("Access cattle records online? (yes/no): ")
    return response.lower() in ["yes", "y"]

def prompt_for_upnp_wizard():
    print("We ran into a small problem.")
    print("We need to install an additional program to automatically configure your network.")
    print("Don't worry, all you need to do is go to:")
    print("https://www.xldevelopment.net/upnpwiz.php")
    print("And download and install the UPnP wizard.")
    while not upnp_wizard_installed():
        if input("Press ENTER to continue after UPnP wizard is installed or press \"c\" to switch to local mode.") == "C":
            break

def upnp_wizard_installed():
    return os.path.exists("C:/Program Files (x86)/UPnP Wizard/UPnPWizardC.exe")

def add_upnp_rule():
    try:
        if platform.system() == "Windows": 
            if not upnp_wizard_installed():
                prompt_for_upnp_wizard()
            subprocess.run(r'"C:\Program Files (x86)\UPnP Wizard\UPnPWizardC.exe" -add {} -ip {} -intport {} -extport {} -protocol {} -legacy'.format(UPNP_DESCRIPTION, get_private_ip(), PORT, PORT, "TCP"))
            return True
        upnp = miniupnpc.UPnP()
        upnp.discoverdelay = 10
        upnp.discover()
        upnp.selectigd()
        # addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
        upnp.addportmapping(PORT, 'TCP', upnp.lanaddr, PORT, UPNP_DESCRIPTION, '')
    except:
        return False
    return True

def check_for_upnp_rule():
    if platform.system() == "Windows": 
        if not upnp_wizard_installed():
            prompt_for_upnp_wizard()
        str(subprocess.check_output(r'"C:\Program Files (x86)\UPnP Wizard\UPnPWizardC.exe" -legacy -list'))
        return UPNP_DESCRIPTION in str(subprocess.check_output(r'"C:\Program Files (x86)\UPnP Wizard\UPnPWizardC.exe" -legacy -list'))
    #try:
    upnp = miniupnpc.UPnP()
    upnp.discoverdelay=200;upnp.discover();upnp.selectigd()

    p=1;i=0
    while p:
        p = upnp.getgenericportmapping(i) ; i+=1
        if p:
            port,protocol,(toAddr,toPort),desc,x,y,z = p
            if port == PORT and toAddr == get_private_ip():
                return True
    #except:
    #    pass
    return False

def get_using_wan():
    with open("config.json", "r") as file:
        return json.loads(file.read()).get("using_wan")

def get_users():
    with open("config.json", "r") as file:
        return json.loads(file.read()).get("users")

def get_usernames():
    return [user["username"] for user in get_users()]