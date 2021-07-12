import json
import urllib
from flask import Blueprint
from flask_simplelogin import login_required

from models import *
api_events = Blueprint('api_events', __name__, template_folder='templates')

@api_events.route("/delete/<event_id>", methods=["POST"])
@login_required(basic=True)
def api_events_delete_event(event_id):
    event_id =  urllib.parse.unquote(event_id)
    event_id = event_id.replace("+"," ")
    event = Event.query.filter_by(event_id=event_id).first()
    db.session.delete(event)
    db.session.commit()
    return "True"

@api_events.route("/event/<event_id>", methods=["POST"])
@login_required(basic=True)
def show_event_api_events(event_id):
    event_id = urllib.parse.unquote(event_id)
    event_id = event_id.replace("+", " ")
    event = Event.query.filter_by(event_id=event_id).first()
    if event:
        return json.dumps({
            "event_id": event.event_id,
            "owner": event.owner,
            "dam": event.get_dam().event_id if event.get_dam() else "N/A",
            "sire": event.get_sire().event_id if event.get_sire() else "N/A",
            "date": event.date,
            "calves": [(calf.event_id, calf.date) for calf in event.get_calves()] if event.get_calves() else [],
            "events": sorted([(event.name, event.date) for event in event.get_events()], key=lambda a: a[1]) if event.get_events() else [],
            "transactions": sorted([(transaction.name, transaction.get_date() + ": $" + str(transaction.price)) for transaction in event.get_transactions()], key=lambda a: a[1]) if event.get_transactions() else []
        })
    return "{}", 404



@api_events.route("/possible_parents/<type>", methods=["POST"])
@login_required(basic=True)
def get_possible_parents(type):
    events = Event.query.all()
    if type == "sire":
        return json.dumps({"parent_type": "sire", "parents": [event.event_id for event in events if event.date in COW_SEXES_MALE_POSSIBLE_PARENTS]})
    else:
        return json.dumps({"parent_type": "dam", "parents": [event.event_id for event in events if event.date in COW_SEXES_FEMALE_POSSIBLE_PARENTS]})

@api_events.route("/date_list/", methods=["POST"])
@login_required(basic=True)
def get_date_list():
    return json.dumps({"datees":COW_SEXES})

@api_events.route("/add_parent/<new_parent_json>", methods=["POST"])
@login_required(basic=True)
def add_parent_api_events(new_parent_json):
    new_parent_json = urllib.parse.unquote(new_parent_json)
    new_parent_json = new_parent_json.replace("+", " ")
    new_parent_dict = json.loads(new_parent_json)
    print(new_parent_dict)
    event = get_event_from_tag(str(new_parent_dict["event_id"]))

    event.dam_id=get_event_from_tag(new_parent_dict["dam"]).event_id
    event.sire_id=get_event_from_tag(new_parent_dict["sire"]).event_id
    db.session.commit()
    return json.dumps({
        "operation":"add_parent",
        "result":"success"
    })

@api_events.route("/change_tag/<tag_change_json>", methods=["POST"])
@login_required(basic=True)
def change_tag_api_events(tag_change_json):
    tag_change_json = urllib.parse.unquote(tag_change_json)
    tag_change_json = tag_change_json.replace("+", " ")
    tag_change_dict = json.loads(tag_change_json)
    event = Event.query.filter_by(event_id=tag_change_dict["old_tag"]).first()
    event.event_id = tag_change_dict["new_tag"]
    db.session.commit()
    return "{'succeeded':'True'}"

@api_events.route("/change_date/<date_change_json>", methods=["POST"])
@login_required(basic=True)
def change_date_api_events(date_change_json):
    date_change_json = urllib.parse.unquote(date_change_json)
    date_change_json = date_change_json.replace("+", " ")
    date_change_dict = json.loads(date_change_json)
    event = Event.query.filter_by(event_id=date_change_dict["event_id"]).first()
    event.date = date_change_dict["date"]
    db.session.commit()
    return "{'succeeded':'True'}"


@api_events.route("/get_list/", methods=["POST"])
@login_required(basic=True)
def get_event_list():
    events = Event.query.all()
    event_names = [
        (
            event.event_id,
            event.name + ": " + ", ".join(cow.tag_number for cow in event.cows),
            event.date,
        )
        for event in events
    ]

    event_names.sort(key= lambda a: a[2])
    return json.dumps({
        "events":event_names
    })
