import json
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

calendar = db.Table('calendar',
                    db.Column('cow_id', db.Integer,
                              db.ForeignKey('cow.cow_id')),
                    db.Column('event_id', db.Integer,
                              db.ForeignKey('event.event_id'))
                    )


class Cow(db.Model):
    cow_id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(8))
    owner = db.Column(db.String(255))
    sex = db.Column(db.String(255))
    events = db.relationship("Event", secondary=calendar,
                             backref=db.backref('cows', lazy='dynamic'))

    dam_id = db.Column(db.Integer, db.ForeignKey('cow.cow_id'))
    sire_id = db.Column(db.Integer, db.ForeignKey('cow.cow_id'))

    def get_dam(self):
        return Cow.query.filter_by(cow_id=self.dam_id).first()

    def get_sire(self):
        return Cow.query.filter_by(cow_id=self.sire_id).first()

    def get_calves(self):
        if self.sex in ["Cow", "Heifer"]:
            return Cow.query.filter_by(dam_id=self.cow_id)

        # There shouldn't be any reason get_calves() is ever
        # called on a steer, but if so, I would assume the
        # steer is the sire?
        elif self.sex in ["Bull", "Steer"]:
            return Cow.query.filter_by(sire_id=self.cow_id)

    def get_events(self):
        return self.events

    def get_birthdate(self):
        events = self.get_events()
        for event in events:
            if event.name == "Born":
                return event.date


class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

    def get_cows():
        return self.cows


def get_cows():
    return Cow.query.all()


def get_cow_from_tag(tag):
    return Cow.query.filter_by(tag_number=tag).first()


@app.route("/")
def home():
    cows = Cow.query.all()
    return render_template("index.html", cows=cows)

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

    new_cow = Cow(
        dam_id=get_cow_from_tag(dam_tag).cow_id if dam_tag else "",
        sire_id=get_cow_from_tag(sire_tag).cow_id if sire_tag else "",
        owner=owner,
        sex=sex,
        tag_number=tag_number
    )

    #db.session.add(new_cow)
    #db.session.commit()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
