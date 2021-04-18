import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

calendar = db.Table('calendar', 
    db.Column('cow_id', db.Integer, db.ForeignKey('cow.cow_id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.event_id'))
)


class Cow(db.Model):
    cow_id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(8))
    events = db.relationship("Event", secondary=calendar, backref=db.backref('cows', lazy='dynamic'))
    
    dam_id=db.Column(db.Integer, db.ForeignKey('cow.cow_id'))
    sire_id=db.Column(db.Integer, db.ForeignKey('cow.cow_id'))
    
    def get_dam(self):
        return Cow.query.filter_by(cow_id = self.dam_id).first()

    def get_sire(self):
        return Cow.query.filter_by(cow_id = self.sire_id).first()

    def get_events(self):
        return self.events

class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

    def get_cows():
        return self.cows

@app.route("/datadump")
def datadump():
    cows = Cow.query.all()
    for cow in cows:
        events = cow.events
        for event in events:
            print(cow.tag_number + ": " + event.name + " " + event.date)
    return ""

@app.route('/getparents/<tag_number>')
def get_parents(tag_number):
    calf = Cow.query.filter_by(tag_number=tag_number).first()
    dam = calf.get_dam()
    sire = calf.get_sire()
    print(f"{tag_number}'s parents are:")
    print(f"Sire: {sire.tag_number}")
    print(f"Dam: {dam.tag_number}")
    return ""
if __name__ == "__main__":
    app.run()