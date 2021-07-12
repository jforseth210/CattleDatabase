import json
import urllib
from flask import Blueprint
from flask_simplelogin import login_required

from models import *
api_transactions = Blueprint('api_transactions', __name__, template_folder='templates')

@api_transactions.route("/delete/<transaction_id>", methods=["POST"])
@login_required(basic=True)
def api_transactions_delete_transaction(transaction_id):
    transaction_id =  urllib.parse.unquote(transaction_id)
    transaction_id = transaction_id.replace("+"," ")
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    db.session.delete(transaction)
    db.session.commit()
    return "True"

@api_transactions.route("/transaction/<transaction_id>", methods=["POST"])
@login_required(basic=True)
def show_transaction_api_transactions(transaction_id):
    transaction_id = urllib.parse.unquote(transaction_id)
    transaction_id = transaction_id.replace("+", " ")
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    if transaction:
        return json.dumps({
            "transaction_id": transaction.transaction_id,
            "owner": transaction.owner,
            "dam": transaction.get_dam().transaction_id if transaction.get_dam() else "N/A",
            "sire": transaction.get_sire().transaction_id if transaction.get_sire() else "N/A",
            "date": transaction.date,
            "calves": [(calf.transaction_id, calf.date) for calf in transaction.get_calves()] if transaction.get_calves() else [],
            "transactions": sorted([(transaction.name, transaction.date) for transaction in transaction.get_transactions()], key=lambda a: a[1]) if transaction.get_transactions() else [],
            "transactions": sorted([(transaction.name, transaction.get_date() + ": $" + str(transaction.price)) for transaction in transaction.get_transactions()], key=lambda a: a[1]) if transaction.get_transactions() else []
        })
    return "{}", 404



@api_transactions.route("/possible_parents/<type>", methods=["POST"])
@login_required(basic=True)
def get_possible_parents(type):
    transactions = Transaction.query.all()
    if type == "sire":
        return json.dumps({"parent_type": "sire", "parents": [transaction.transaction_id for transaction in transactions if transaction.date in COW_SEXES_MALE_POSSIBLE_PARENTS]})
    else:
        return json.dumps({"parent_type": "dam", "parents": [transaction.transaction_id for transaction in transactions if transaction.date in COW_SEXES_FEMALE_POSSIBLE_PARENTS]})

@api_transactions.route("/date_list/", methods=["POST"])
@login_required(basic=True)
def get_date_list():
    return json.dumps({"datees":COW_SEXES})

@api_transactions.route("/add_parent/<new_parent_json>", methods=["POST"])
@login_required(basic=True)
def add_parent_api_transactions(new_parent_json):
    new_parent_json = urllib.parse.unquote(new_parent_json)
    new_parent_json = new_parent_json.replace("+", " ")
    new_parent_dict = json.loads(new_parent_json)
    print(new_parent_dict)
    transaction = get_transaction_from_tag(str(new_parent_dict["transaction_id"]))

    transaction.dam_id=get_transaction_from_tag(new_parent_dict["dam"]).transaction_id
    transaction.sire_id=get_transaction_from_tag(new_parent_dict["sire"]).transaction_id
    db.session.commit()
    return json.dumps({
        "operation":"add_parent",
        "result":"success"
    })

@api_transactions.route("/change_tag/<tag_change_json>", methods=["POST"])
@login_required(basic=True)
def change_tag_api_transactions(tag_change_json):
    tag_change_json = urllib.parse.unquote(tag_change_json)
    tag_change_json = tag_change_json.replace("+", " ")
    tag_change_dict = json.loads(tag_change_json)
    transaction = Transaction.query.filter_by(transaction_id=tag_change_dict["old_tag"]).first()
    transaction.transaction_id = tag_change_dict["new_tag"]
    db.session.commit()
    return "{'succeeded':'True'}"

@api_transactions.route("/change_date/<date_change_json>", methods=["POST"])
@login_required(basic=True)
def change_date_api_transactions(date_change_json):
    date_change_json = urllib.parse.unquote(date_change_json)
    date_change_json = date_change_json.replace("+", " ")
    date_change_dict = json.loads(date_change_json)
    transaction = Transaction.query.filter_by(transaction_id=date_change_dict["transaction_id"]).first()
    transaction.date = date_change_dict["date"]
    db.session.commit()
    return "{'succeeded':'True'}"


@api_transactions.route("/get_list/", methods=["POST"])
@login_required(basic=True)
def get_transaction_list():
    transactions = Transaction.query.all()
    transaction_names = [
        (
            transaction.transaction_id,
            transaction.name + ": " + ", ".join(cow.tag_number for cow in transaction.cows),
            transaction.get_date() + " - $" + str(transaction.price),
        )
        for transaction in transactions
    ]

    transaction_names.sort(key= lambda a: a[2])
    return json.dumps({
        "transactions":transaction_names
    })
