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
    cows = Cow.query.all()
    events = Event.query.all()
    cow_results = [cow.search(query) for cow in cows if cow.search(query)]
    event_results = [event.search(query)
                     for event in events if event.search(query)]
    results = cow_results + event_results
    return render_template("search.html", query=query, results=results)


@app.route("/cow/<tag_number>")
def showCow(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    if not cow:
        return redirect("/")
    return render_template("cow.html", cow=cow, cows=get_cows())


@app.route("/cowexists/<tag_number>")
def cow_exists(tag_number):
    cow = Cow.query.filter_by(tag_number=tag_number).first()
    return "True" if cow else "False"


@app.route("/newCow", methods=["POST"])
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


@app.route("/newEvent", methods=["POST"])
def new_event():
    tag = request.form.get('tag_number')

    if tag:
        cows = [tag]
    else:
        cows = request.form.getlist('cows')
        print(type(cows))
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
