import json
from flask import Flask, render_template, request, redirect
import re

from models import db, Cow, Event, SearchResult

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def get_cow_from_tag(tag):
    return Cow.query.filter_by(tag_number=tag).first()


def get_unique_cow_values():
    cows = Cow.query.all()
    tags = set()
    sexes = set()
    owners = set()
    sires = set()
    dams = set()

    for cow in cows:
        tags.add(cow.get_first_digit_of_tag())
        sexes.add(cow.sex)
        owners.add(cow.owner)
        if cow.get_dam():
            dams.add(cow.get_dam().tag_number)
        if cow.get_sire():
            sires.add(cow.get_sire().tag_number)
    return {"tags": tags, "sexes": sexes, "owners": owners, "sires": sires, "dams": dams}


def get_unique_event_values():
    events = Event.query.all()

    names = set()
    dates = set()
    for event in events:
        names.add(event.name)
        dates.add(event.date)
    return {"names": names, "dates": dates}


@app.route("/")
def home():
    return redirect("/cows")


@app.route("/cows")
def cows():
    cows = Cow.query.all()
    return render_template("cows.html", cows=cows)


@app.route("/events")
def events():
    events = Event.query.all()
    cows = Cow.query.all()
    return render_template("events.html", events=events, cows=cows)


@app.route("/search")
def search():
    # Arguments
    query = request.args.get("q")
    types = request.args.getlist("type")
    # Cow arguments
    tags = request.args.getlist("tag")
    sexes = request.args.getlist("sex")
    owners = request.args.getlist("owner")
    sires = request.args.getlist("sire")
    dams = request.args.getlist("dam")
    # Event arguments
    dates = request.args.getlist("date")
    names = request.args.getlist("name")

    # Package for jinja
    checked_values = {
        "types": types,
        "tags": tags,
        "sexes": sexes,
        "owners": owners,
        "sires": sires,
        "dams": dams,

        "names": names,
        "dates": dates
    }

    # Get unique values from each column
    unique_values = get_unique_cow_values()
    unique_values.update(get_unique_event_values())
    # Add the two types of object
    unique_values["types"] = ["Cow", "Event"]

    events = []
    cows = []
    # If no cow specific parameters are checked, and events haven't been filtered out
    if not (tags or sexes or owners or dams or sires or (types and "Event" not in types)):
        events = Event.query.all()

    # If no event specific parameters are checked, and cows haven't been filtered out
    if not (dates or names or (types and "Cow" not in types)):
        cows = Cow.query.all()

    # Run object.search() for each object, and if it returns true, convert it to a SearchResult and add it to a list
    cow_results = [cow.toSearchResult(query) for cow in cows if cow.search(query, tags=tags, sexes=sexes, owners=owners,
                                                                           sires=sires, dams=dams)]
    event_results = [event.toSearchResult(query)
                     for event in events if event.search(query, dates=dates, names=names)]

    # Put the results together
    results = cow_results+event_results

    # Send it
    return render_template("search.html",
                           # What the user searched for
                           query=query,
                           # The matching results
                           results=results,
                           # The possible filter options
                           unique_values=unique_values,
                           # The selected filter options
                           checked_values=checked_values
                           )


@ app.route("/cow/<tag_number>")
def showCow(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if not cow:
        return redirect("/")
    return render_template("cow.html", cow=cow, cows=Cow.query.all())


@ app.route("/cowexists/<tag_number>")
def cow_exists(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    return "True" if cow else "False"


@ app.route("/newCow", methods=["POST"])
def new_cow():
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

    db.session.add(new_cow_object)
    db.session.commit()
    return redirect(request.referrer)


@ app.route("/newEvent", methods=["POST"])
def new_event():  # sourcery skip: assign-if-exp
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
    return redirect(request.referrer)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
