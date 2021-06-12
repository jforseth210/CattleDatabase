import urllib.parse
import json

from flask import Blueprint, render_template
from flask_simplelogin import login_required

from models import db, Cow
from setup_utils import get_private_ip, get_public_ip

api = Blueprint('api', __name__,
                        template_folder='templates')

@api.route("/test_credentials", methods=["POST"])
@login_required(basic=True)
def test_credentials():
    return "True"

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
    new_cow_json =  urllib.parse.unquote(new_cow_json)
    new_cow_dict = json.loads(new_cow_json)
    print(new_cow_dict)
    cow = Cow(
        dam_id=Cow.query.filter_by(tag_number=new_cow_dict["dam"]).first().cow_id,
        sire_id=Cow.query.filter_by(tag_number=new_cow_dict["sire"]).first().cow_id,
        tag_number=new_cow_dict["tag_number"],
        owner=new_cow_dict["owner"],
        sex=new_cow_dict["sex"]
    )
    db.session.add(cow)
    db.session.commit()
    return json.dumps({
        "operation":"add_cow",
        "result":"success"
    })
@api.route("/cow/<tag_number>", methods=["POST"])
@login_required(basic=True)
def show_cow_api(tag_number):
    tag_number =  urllib.parse.unquote(tag_number)
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
@api.route("/get_server_info/")
def get_server_info():
    return json.dumps({
        "LAN_address":get_private_ip(),
        "WAN_address":get_public_ip()
    })

@api.route("/get_possible_parents/sire", methods=["POST"])
@login_required(basic=True)
def get_possible_sires():
    cows = Cow.query.all()
    return json.dumps({"parent_type":"sire", "parents":[cow.tag_number for cow in cows if cow.sex == "Bull"]})

@api.route("/get_possible_parents/dam", methods=["POST"])
@login_required(basic=True)
def get_possible_dams():
    cows = Cow.query.all()
    return json.dumps({"parent_type":"dam", "parents":[cow.tag_number for cow in cows if cow.sex in ["Cow", "Heifer"]]})