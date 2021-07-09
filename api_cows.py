import json
import urllib
from flask import Blueprint
from flask_simplelogin import login_required

from models import *
api_cows = Blueprint('api_cows', __name__, template_folder='templates')

@api_cows.route("/delete/<tag_number>", methods=["POST"])
@login_required(basic=True)
def api_cows_delete_cow(tag_number):
    tag_number =  urllib.parse.unquote(tag_number)
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    db.session.delete(cow)
    db.session.commit()
    return "True"

@api_cows.route("/add/<new_cow_json>", methods=["POST"])
@login_required(basic=True)
def add_cow_api_cows(new_cow_json):
    new_cow_json = urllib.parse.unquote(new_cow_json)
    new_cow_dict = json.loads(new_cow_json)
    print(new_cow_dict)
    if new_cow_dict["dam"] == "Not+Applicable":
        dam_id = "N/A"
    else:
        dam_id = Cow.query.filter_by(tag_number=new_cow_dict["dam"]).first().cow_id
    if new_cow_dict["sire"] == "Not+Applicable":
        sire_id = "N/A"
    else:
        sire_id = Cow.query.filter_by(tag_number=new_cow_dict["sire"]).first().cow_id
    cow = Cow(
        dam_id=dam_id,
        sire_id=sire_id,
        tag_number=new_cow_dict["tag_number"].replace("+", " "),
        owner=new_cow_dict["owner"].replace("+", " "),
        sex=new_cow_dict["sex"]
    )
    if (new_cow_dict.get("born_event", False)):
        born_event = Event(
            date=new_cow_dict['date'], name="Born", description=f"{new_cow_dict['dam']} gave birth to {new_cow_dict['tag_number']}", cows=[cow])
        db.session.add(born_event)

    if (new_cow_dict.get("calved_event", False)):
        calved_event = Event(date=new_cow_dict['date'], name="Calved", description=f"{new_cow_dict['dam']} gave birth to {new_cow_dict['tag_number']}", cows=[
                             get_cow_from_tag(new_cow_dict['dam'])])
        db.session.add(calved_event)

    db.session.add(cow)
    db.session.commit()
    return json.dumps({
        "operation": "add_cow",
        "result": "success"
    })

@api_cows.route("/cow/<tag_number>", methods=["POST"])
@login_required(basic=True)
def show_cow_api_cows(tag_number):
    tag_number = urllib.parse.unquote(tag_number)
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if cow:
        return json.dumps({
            "tag_number": cow.tag_number,
            "owner": cow.owner,
            "dam": cow.get_dam().tag_number if cow.get_dam() else "N/A",
            "sire": cow.get_sire().tag_number if cow.get_sire() else "N/A",
            "sex": cow.sex,
            "calves": [(calf.tag_number, calf.sex) for calf in cow.get_calves()] if cow.get_calves() else []
        })
    return "{}", 404



@api_cows.route("/possible_parents/<type>", methods=["POST"])
@login_required(basic=True)
def get_possible_parents(type):
    cows = Cow.query.all()
    if type == "sire":
        return json.dumps({"parent_type": "sire", "parents": [cow.tag_number for cow in cows if cow.sex in COW_SEXES_MALE_POSSIBLE_PARENTS]})
    else:
        return json.dumps({"parent_type": "dam", "parents": [cow.tag_number for cow in cows if cow.sex in COW_SEXES_FEMALE_POSSIBLE_PARENTS]})

@api_cows.route("/sex_list/", methods=["POST"])
@login_required(basic=True)
def get_sex_list():
    return json.dumps({"sexes":COW_SEXES})

@api_cows.route("/add_parent/<new_parent_json>", methods=["POST"])
@login_required(basic=True)
def add_parent_api_cows(new_parent_json):
    new_parent_json = urllib.parse.unquote(new_parent_json)
    new_parent_dict = json.loads(new_parent_json)
    print(new_parent_dict)
    cow = get_cow_from_tag(str(new_parent_dict["tag_number"]))

    cow.dam_id=get_cow_from_tag(new_parent_dict["dam"]).cow_id
    cow.sire_id=get_cow_from_tag(new_parent_dict["sire"]).cow_id
    db.session.commit()
    return json.dumps({
        "operation":"add_parent",
        "result":"success"
    })

@api_cows.route("/change_tag/<tag_change_json>", methods=["POST"])
@login_required(basic=True)
def change_tag_api_cows(tag_change_json):
    tag_change_json = urllib.parse.unquote(tag_change_json)
    tag_change_dict = json.loads(tag_change_json)
    cow = Cow.query.filter_by(tag_number=tag_change_dict["old_tag"]).first()
    cow.tag_number = tag_change_dict["new_tag"]
    db.session.commit()
    return "{'succeeded':'True'}"

@api_cows.route("/transfer_ownership/<transfer_ownership_json>", methods=["POST"])
@login_required(basic=True)
def transfer_ownership_api_cows(transfer_ownership_json):
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


@api_cows.route("/get_list/", methods=["POST"])
@login_required(basic=True)
def get_cow_list():
    cows = Cow.query.all()
    cow_tag_numbers = [(cow.tag_number, cow.sex) for cow in cows]
    cow_tag_numbers.sort()
    return json.dumps({
        "cows":cow_tag_numbers
    })
