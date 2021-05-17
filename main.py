import json
from flask import Flask, render_template, request, redirect, Markup
import re

from models import db, Cow, Event, Transaction, SearchResult
from searchfunctions import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
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
    return render_template("cows.html", cows=cows)


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
    return render_template("transactions.html", transactions=transactions,formatted_total=formatted_total,unformatted_total=total)


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
        event_id = event_id,
        tofrom = tofrom,
        cows = event.cows
    )

    db.session.add(new_transaction_object)
    db.session.commit()
    return redirect(request.referrer+"#transactions")

@app.route("/transactionAddRemoveCows", methods=["POST"])
def transaction_add_remove_cows():
    all_cows = request.form.getlist("all_cows")
    new_cow = request.form.get("new_cow")

    transaction_id = request.form.get("transaction")

    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
