import urllib.parse
import json

from flask import Blueprint, request
from flask_simplelogin import login_required

from models import db, Cow, Transaction, Event
from setup_utils import get_private_ip, get_public_ip

api = Blueprint('api', __name__, template_folder='templates')

@api.route("/test_credentials/", methods=["POST"])
@login_required(basic=True)
def test_credentials():
    return "{'succeeded':'True'}"

@api.route("/delete_cow/<tag_number>", methods=["POST"])
@login_required(basic=True)
def api_delete_cow(tag_number):
    tag_number =  urllib.parse.unquote(tag_number)
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    db.session.delete(cow)
    db.session.commit()
    return "True"

@api.route("/add_cow/<new_cow_json>", methods=["POST"])
@login_required(basic=True)
def add_cow_api(new_cow_json):
    new_cow_json = urllib.parse.unquote(new_cow_json)
    new_cow_dict = json.loads(new_cow_json)
    print(new_cow_dict)
    if new_cow_dict["dam"] == "Not+Applicable":
        dam_id = "N/A"
    else:
        dam_id = Cow.query.filter_by(tag_number=new_cow_dict["dam"]).first().cow_id
    if new_cow_dict["sire"] == "Not+Applicable":
        print("Sire is N/A")
        sire_id = "N/A"
    else:
        sire_id = Cow.query.filter_by(tag_number=new_cow_dict["sire"]).first().cow_id
    cow = Cow(
        dam_id=dam_id,
        sire_id=sire_id,
        tag_number=new_cow_dict["tag_number"],
        owner=new_cow_dict["owner"],
        sex=new_cow_dict["sex"]
    )
    db.session.add(cow)
    db.session.commit()
    return json.dumps({
        "operation": "add_cow",
        "result": "success"
    })

@api.route("/cow/<tag_number>", methods=["POST"])
@login_required(basic=True)
def show_cow_api(tag_number):
    tag_number = urllib.parse.unquote(tag_number)
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if cow:
        return json.dumps({
            "tag_number": cow.tag_number,
            "owner": cow.owner,
            "dam": cow.get_dam().tag_number if cow.get_dam() else "N/A",
            "sire": cow.get_sire().tag_number if cow.get_sire() else "N/A",
            "sex": cow.sex,
            "calves": [calf.tag_number for calf in cow.get_calves()] if cow.get_calves() else []
        })
    return "{}", 404

@api.route("/get_server_info", methods=["POST"])
def get_server_info():
    return json.dumps({
        "LAN_address": get_private_ip(),
        "WAN_address": get_public_ip()
    })

@api.route("/get_possible_parents/sire", methods=["POST"])
@login_required(basic=True)
def get_possible_sires():
    cows = Cow.query.all()
    return json.dumps({"parent_type": "sire", "parents": [cow.tag_number for cow in cows if cow.sex == "Bull"]})

@api.route("/get_possible_parents/dam", methods=["POST"])
@login_required(basic=True)
def get_possible_dams():
    cows = Cow.query.all()
    return json.dumps({"parent_type": "dam", "parents": [cow.tag_number for cow in cows if cow.sex in ["Cow", "Heifer"]]})

@api.route("/add_parent/<new_parent_json>", methods=["POST"])
@login_required(basic=True)
def add_parent_api(new_parent_json):
    new_parent_json = urllib.parse.unquote(new_parent_json)
    new_parent_dict = json.loads(new_parent_json)

    cow = Cow.query.filter_by(tag_number=new_parent_dict["tag_number"])

    cow.dam_id=Cow.query.filter_by(tag_number=new_parent_dict["dam"]).first().cow_id,
    cow.sire_id=Cow.query.filter_by(tag_number=new_parent_dict["sire"]).first().cow_id,

    db.session.commit()
    return json.dumps({
        "operation":"add_parent",
        "result":"success"
    })

@api.route("/change_tag/<tag_change_json>", methods=["POST"])
@login_required(basic=True)
def change_tag_api(tag_change_json):
    tag_change_json = urllib.parse.unquote(tag_change_json)
    tag_change_dict = json.loads(tag_change_json)
    cow = Cow.query.filter_by(tag_number=tag_change_dict["old_tag"]).first()
    cow.tag_number = tag_change_dict["new_tag"]
    db.session.commit()
    return "{'succeeded':'True'}"

@api.route("/transfer_ownership/<transfer_ownership_json>", methods=["POST"])
@login_required(basic=True)
def transfer_ownership_api(transfer_ownership_json):
    transfer_ownership_json_ = urllib.parse.unquote(transfer_ownership_json)
    transfer_ownership_dict = json.loads(transfer_ownership_json)

    transfer_ownership_dict["description"] = transfer_ownership_dict["description"].replace("+"," ")

    cow = Cow.query.filter_by(tag_number=transfer_ownership_dict["tag_number"]).first()
    sale_transaction = Transaction(
        name="Sold", description=f"{cow.owner} sold {cow.tag_number}: {transfer_ownership_dict['description']}", price=transfer_ownership_dict["price"], tofrom=transfer_ownership_dict["new_owner"])
    sale_event = Event(date=transfer_ownership_dict["date"], name="Transfer",
                       description=f"Transfer {cow.tag_number} from {cow.owner} to {transfer_ownership_dict['new_owner']}:\n{transfer_ownership_dict['description']}", cows=[cow], transactions=[sale_transaction])

    cow.owner = transfer_ownership_dict['new_owner']

    db.session.add(sale_event)
    db.session.add(sale_transaction)
    db.session.commit()
    return "{'succeeded':'True'}"


@api.route("/get_cow_list/", methods=["POST"])
@login_required(basic=True)
def get_cow_list():
    cows = Cow.query.all()
    cow_tag_numbers = [cow.tag_number for cow in cows]
    print(cow_tag_numbers)
    cow_tag_numbers.sort()
    return json.dumps({
        "cows":cow_tag_numbers
    })
