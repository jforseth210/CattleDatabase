import json
import re
import subprocess
import socket 
import contextlib
import io
import sys
import os
import platform
import time
from getpass import getpass

# Trying to get this installed on Windows is agnonizing
# This might help: https://github.com/miniupnp/miniupnp/issues/159
import miniupnpc

import requests
from flask import Flask, render_template, request, redirect, Markup
import pyfiglet
import werkzeug.security

from models import db, Cow, Event, Transaction, SearchResult
from searchfunctions import *

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cattle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def get_cow_from_tag(tag):
    return Cow.query.filter_by(tag_number=tag).first()


@app.route("/")
def home():
    return redirect("/cows")


@app.route("/cows")
def cows():
    cows = Cow.query.all()
    usernames = get_usernames()
    print(usernames)
    return render_template("cows.html", cows=cows, usernames=usernames)


@app.route("/cow/<tag_number>")
def show_cow(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if not cow:
        return redirect(request.referrer)
    events = Event.query.all()

    transaction_total = 0
    for event in events:
        for transaction in event.transactions:
            transaction_total += transaction.price

    return render_template("cow.html", cow=cow, cows=Cow.query.all(), events=events, transaction_total=transaction_total)


@app.route("/events")
def events():
    events = Event.query.all()
    cows = Cow.query.all()
    return render_template("events.html", events=events, cows=cows)


@app.route("/event/<event_id>")
def show_event(event_id):
    event = Event.query.filter_by(event_id=event_id).first()
    if not event:
        return redirect(request.referrer)
    return render_template("event.html", event=event, cows=Cow.query.all())


@app.route("/transactions")
def transactions():
    transactions = Transaction.query.all()
    total = sum(
        transaction.price * len(transaction.cows) for transaction in transactions
    )
    formatted_total = "${:,.2f}".format(total)
    return render_template("transactions.html", transactions=transactions, formatted_total=formatted_total, unformatted_total=total)


@app.route("/transaction/<transaction_id>")
def show_transaction(transaction_id):
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    if not transaction:
        return redirect(request.referrer)
    return render_template("transaction.html", transaction=transaction, all_cows=Cow.query.all())


@app.route('/calendar')
def calendar():
    cows = Cow.query.all()
    return render_template('calendar.html', cows=cows)


@app.route('/calendar/events/api')
def event_api():
    events = Event.query.all()
    formatted_events = []
    for event in events:
        cow_string = ", ".join(cow.tag_number for cow in event.cows)
        formatted_event = {
            'title': event.name + ": " + cow_string,
            'start': event.date,
            'id': event.event_id
        }
        formatted_events.append(formatted_event)
    return json.dumps(formatted_events)


@app.route("/search")
def search():
    # Arguments
    query = request.args.get("q")
    # What kind of things are we searching for?
    types = determine_types(request)

    argument_dict = {"types": request.args.getlist("type")}
    if "Cow" in types:
        argument_dict.update({
            "tags": request.args.getlist("tag"),
            "sexes": request.args.getlist("sex"),
            "owners": request.args.getlist("owner"),
            "sires": request.args.getlist("sire"),
            "dams": request.args.getlist("dam")
        })

    if "Event" in types:
        argument_dict.update({
            "dates": request.args.getlist("date"),
            "event_names": request.args.getlist("event_name")
        })

    if "Transaction" in types:
        argument_dict.update({
            "transaction_names": request.args.getlist("transaction_name"),
            "prices": request.args.getlist("price")
        })

    unique_values = get_unique_values()

    results = get_results(types, argument_dict, query)

    # TODO: Fix this mess
    if types == ["Transaction"]:
        if argument_dict["prices"] == ["Low to High"]:
            for i in results:
                print(i.body)
            results.sort(key=lambda x: float(
                re.search("\$.\d+.\d+", x.body).group().strip("$")))
        else:
            results.sort(key=lambda x: float(
                re.search("\$.\d+.\d+", x.body).group().strip("$")), reverse=True)
    # Send it
    return render_template("search.html", query=query, results=results, unique_values=unique_values, checked_values=argument_dict)


@ app.route("/newCow", methods=["POST"])
def new_cow():
    date = request.form.get('date')
    born_event_enabled = request.form.get('born_event')
    calved_event_enabled = request.form.get('calved_event')
    dam_tag = request.form.get('dam')
    sire_tag = request.form.get('sire')
    tag_number = request.form.get('tag_number')
    owner = request.form.get('owner')
    sex = request.form.get('sex')

    new_cow_object = Cow(
        dam_id=get_cow_from_tag(dam_tag).cow_id if dam_tag else "",
        sire_id=get_cow_from_tag(sire_tag).cow_id if sire_tag else "",
        owner=owner,
        sex=sex,
        tag_number=tag_number
    )

    if born_event_enabled == 'on':
        born_event = Event(
            date=date, name="Born", description=f"{dam_tag} gave birth to {tag_number}", cows=[new_cow_object])
        db.session.add(born_event)

    if calved_event_enabled == 'on':
        calved_event = Event(date=date, name="Calved", description=f"{dam_tag} gave birth to {tag_number}", cows=[
                             get_cow_from_tag(dam_tag)])
        db.session.add(calved_event)

    db.session.add(new_cow_object)
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/cowexists/<tag_number>")
def cow_exists(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()

    return "True" if cow else "False"


@app.route("/cowChangeTagNumber", methods=["POST"])
def change_tag_number():
    old_tag_number = request.form.get("old_tag_number")
    new_tag_number = request.form.get("new_tag_number")

    cow = get_cow_from_tag(old_tag_number)
    cow.tag_number = new_tag_number
    db.session.commit()
    return redirect("/cow/"+new_tag_number)


@app.route("/deletecow", methods=["POST"])
def delete_cow():
    tag_number = request.form.get("tag_number")
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    db.session.delete(cow)
    db.session.commit()
    return redirect('/cows')


@app.route("/transferOwnership", methods=["POST"])
def transferOwnership():
    tag_number = request.form.get("tag_number")
    new_owner = request.form.get("newOwner")
    date = request.form.get("date")
    price = request.form.get("price")
    description = request.form.get("description")

    cow = Cow.query.filter_by(tag_number=tag_number).first()
    sale_transaction = Transaction(
        name="Sold", description=f"{cow.owner} sold {tag_number}: {description}", price=price, tofrom=new_owner)
    sale_event = Event(date=date, name="Transfer",
                       description=f"Transfer {cow.tag_number} from {cow.owner} to {new_owner}:\n{description}", cows=[cow], transactions=[sale_transaction])

    cow.owner = new_owner

    db.session.add(sale_event)
    db.session.commit()
    return redirect(request.referrer)


@app.route("/cowAddParent", methods=["POST"])
def cow_add_parent():
    tag_number = request.form.get("tag_number")
    parent_type = request.form.get("parent_type")
    parent_tag = request.form.get("parent_tag")

    cow = get_cow_from_tag(tag_number)

    if parent_type == "Dam":
        cow.dam_id = get_cow_from_tag(parent_tag).cow_id
    else:
        cow.sire_id = get_cow_from_tag(parent_tag).cow_id
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/newEvent", methods=["POST"])
def new_event():
    tag = request.form.get('tag_number')

    if tag:
        cows = [tag]
    else:
        cows = request.form.getlist('cows')
    date = request.form.get('date')
    name = request.form.get('name')
    description = request.form.get('description')
    new_event_object = Event(
        date=date,
        name=name,
        description=description,
        cows=[get_cow_from_tag(tag) for tag in cows]
    )

    db.session.add(new_event_object)
    db.session.commit()
    return redirect(request.referrer+"#events")


@app.route("/dateexists/<date>")
def check_if_date_exists(date):
    events = Event.query.filter_by(date=date).all()
    if events:
        return f"Found {len(events)} events on {date}: " + ', '.join(
            event.name for event in events
        )
    else:
        return "No events on this date"


@app.route("/eventAddRemoveCows", methods=["POST"])
def event_add_remove_cows():
    all_cows = request.form.getlist("all_cows")
    new_cow = request.form.get("new_cow")

    event_id = request.form.get("event")

    event = Event.query.filter_by(event_id=event_id).first()
    if all_cows:
        event.cows = [get_cow_from_tag(cow) for cow in all_cows]
    elif new_cow:
        event.cows.append(get_cow_from_tag(new_cow))
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/eventChangeDate", methods=["POST"])
def event_change_date():
    event_id = request.form.get("event_id")
    date = request.form.get("date")

    event = Event.query.filter_by(event_id=event_id).first()
    event.date = date
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/eventChangeDescription", methods=["POST"])
def event_change_description():
    event_id = request.form.get("event_id")
    description = request.form.get("description")

    event = Event.query.filter_by(event_id=event_id).first()
    event.description = description
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/eventChangeName", methods=["POST"])
def event_change_name():
    event_id = request.form.get("event_id")
    name = request.form.get("name")

    event = Event.query.filter_by(event_id=event_id).first()
    event.name = name
    db.session.commit()
    return redirect(request.referrer)


@app.route("/deleteevent", methods=["POST"])
def delete_event():
    event_id = request.form.get("event_id")
    event = Event.query.filter_by(event_id=event_id).first()
    db.session.delete(event)
    db.session.commit()
    return redirect('/events')


@ app.route("/newTransaction", methods=["POST"])
def new_transaction():
    event_id = request.form.get('event_id')
    event = Event.query.filter_by(event_id=event_id).first()

    price = request.form.get('price')
    name = request.form.get('name')
    tofrom = request.form.get('tofrom')
    description = request.form.get('description')
    new_transaction_object = Transaction(
        price=price,
        name=name,
        description=description,
        event_id=event_id,
        tofrom=tofrom,
        cows=event.cows
    )

    db.session.add(new_transaction_object)
    db.session.commit()
    return redirect(request.referrer+"#transactions")


@app.route("/transactionAddRemoveCows", methods=["POST"])
def transaction_add_remove_cows():
    all_cows = request.form.getlist("all_cows")
    new_cow = request.form.get("new_cow")

    transaction_id = request.form.get("transaction")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    if all_cows:
        transaction.cows = [get_cow_from_tag(cow) for cow in all_cows]
    elif new_cow:
        transaction.cows.append(get_cow_from_tag(new_cow))
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/transactionChangePrice", methods=["POST"])
def transaction_change_price():
    transaction_id = request.form.get("transaction_id")
    price = request.form.get("price")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.price = price
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/transactionChangeDescription", methods=["POST"])
def transaction_change_description():
    transaction_id = request.form.get("transaction_id")
    description = request.form.get("description")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.description = description
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/transactionChangeName", methods=["POST"])
def transaction_change_name():
    transaction_id = request.form.get("transaction_id")
    name = request.form.get("name")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.name = name
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/transactionChangeToFrom", methods=["POST"])
def transaction_change_to_from():
    transaction_id = request.form.get("transaction_id")
    tofrom = request.form.get("tofrom")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.tofrom = tofrom
    db.session.commit()
    return redirect(request.referrer)


@app.route("/deletetransaction", methods=["POST"])
def delete_transaction():
    transaction_id = request.form.get("transaction_id")
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    db.session.delete(transaction)
    db.session.commit()
    return redirect('/transactions')

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
    print("This will be used to log in, and to")
    print("highlight the cows you currently own in the system.")
    print("You can enter multiple usernames, separated by commas (and spaces) like so:")
    #print("Katie Elder, Tom Elder, John Elder, Matt Elder, Bud Elder")
    user_strings = input().split(", ")
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
PORT = 5000
UPNP_DESCRIPTION = "CattleDB"
if __name__ == "__main__":
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
    print("SERVER LOG: IGNORE UNLESS SOMETHING GOES WRONG")
    #Attempt to silence app.run() output
    #with contextlib.redirect_stdout(io.StringIO()):
    app.run(debug=False, host="0.0.0.0")
