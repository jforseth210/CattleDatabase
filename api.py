import urllib.parse
import json

from flask import Blueprint, request
from flask_simplelogin import login_required

from models import db, Cow, Transaction, Event, get_cow_from_tag, COW_SEXES_FEMALE_POSSIBLE_PARENTS, COW_SEXES_MALE_POSSIBLE_PARENTS, COW_SEXES
from setup_utils import get_private_ip, get_public_ip

api = Blueprint('api', __name__, template_folder='templates')



@api.route("/test_credentials/", methods=["POST"])
@login_required(basic=True)
def test_credentials():
    return "{'succeeded':'True'}"

@api.route("/get_server_info", methods=["POST"])
def get_server_info():
    return json.dumps({
        "LAN_address": get_private_ip(),
        "WAN_address": get_public_ip()
    })