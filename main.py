import json
from flask import Flask, render_template, request, redirect
import re

from models import db, Cow, Event, SearchResult

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def get_cows():
    return Cow.query.all()


def get_cow_from_tag(tag):
    return Cow.query.filter_by(tag_number=tag).first()

def get_first_digit_of_tag(tag_number):
    first_digit = re.search("\d", tag_number)
    first_digit = first_digit.group()[0] if first_digit else "N/A"
    return first_digit

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
    query = request.args.get("q")
    checked_tags = request.args.getlist("tag")
    checked_sexes = request.args.getlist("sex")
    checked_owners = request.args.getlist("owner")
    
    checked_dates = request.args.getlist("date")
    checked_names = request.args.getlist("name")

    cows = Cow.query.all()
    events = Event.query.all()

    #Get unique values from each column
    all_tags = set()
    all_sexes = set()
    all_owners = set()
    for cow in cows:
        all_tags.add(get_first_digit_of_tag(cow.tag_number))
        all_sexes.add(cow.sex)
        all_owners.add(cow.owner)
    
    all_dates = set()
    all_names = set()
    for event in events:
        all_dates.add(event.date)
        all_names.add(event.name)

    if checked_tags or checked_sexes or checked_owners:
        events = []
    if checked_dates or checked_names:
        cows = []

    if checked_tags:
        cows = [cow for cow in cows if get_first_digit_of_tag(cow.tag_number) in checked_tags]
    if checked_sexes:
        cows = [cow for cow in cows if cow.sex in checked_sexes]
    if checked_owners:
        cows = [cow for cow in cows if cow.owner in checked_owners]
    
    if checked_dates:
        events = [event for event in events if event.date in checked_dates]
    if checked_names:
        events = [event for event in events if event.name in checked_names]

    cow_results = [cow.search(query) for cow in cows if cow.search(query)]
    event_results = [event.search(query)
                     for event in events if event.search(query)]

    results = cow_results+event_results

    return render_template("search.html",
                           query=query,
                           results=results,
                           all_tags=all_tags, 
                           checked_tags=checked_tags, 
                           all_sexes=all_sexes, 
                           checked_sexes=checked_sexes,
                           all_owners=all_owners,
                           checked_owners=checked_owners,
                           all_dates=all_dates,
                           checked_dates=checked_dates, 
                           all_names=all_names,
                           checked_names=checked_names
    )


@ app.route("/cow/<tag_number>")
def showCow(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if not cow:
        return redirect("/")
    return render_template("cow.html", cow=cow, cows=get_cows())


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
    return redirect("/")


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
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
