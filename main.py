from json import dumps
from random import randint
import uuid
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

@app.route("/")
def hello():
    cow = Cow(tag_number=f"<>{randint(100,999)}", id=str(uuid.uuid4()))
    db.session.add(cow)
    cow.add_event(date=f"{randint(1990,2021)}-{randint(1,12)}-{randint(1,31)}", name="Born", description=f"My name is {cow.tag_number} and I was born")
    cow.add_event(date=f"{randint(1990,2021)}-{randint(1,12)}-{randint(1,31)}", name="Died", description=f"My name is {cow.tag_number} and I died")
    db.session.commit()
    return ""
@app.route("/cows")
def cows():
    return dumps([cow.get_events() for cow in Cow.query.all()])

class Cow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tag_number = db.Column(db.String(6))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    events = db.relationship('Event', backref=db.backref('cows', lazy=True))

    def __init__(self, **kwargs):
        super(Cow, self).__init__(**kwargs)

    def moo(self):
        print(f"{self.tag_number} mooed")
    
    def add_event(self, date, name, description):
        print(f"Passing: date={date}, name={name}, description={description}, cow_id={self.id}")
        event = Event(date=date, name=name, description=description, cow_id=self.id)
    def get_events(self):
        return f"{self.tag_number}:<br/>" + dumps([repr(event) for event in Event.query.all()])

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    name = db.Column(db.Text)
    description = db.Column(db.Text)
    cow_id = db.Column(db.Text)
    #cow =  db.relationship('Cow', backref=db.backref('events', lazy=True))

    def __repr__(self):
        return f"Event:{self.name}  Description:{self.description}  Date:{self.date}"
if __name__ == "__main__":
    app.run()