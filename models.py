from flask_sqlalchemy import SQLAlchemy
from flask import Markup
import re
db = SQLAlchemy()

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

    def search(self, query):
        if query.lower() in repr(self).lower():
            return SearchResult(self.tag_number, repr(self).replace(query, f"<b>{query}</b>"), f"/cow/{self.tag_number}")
    
    def get_first_digit_of_tag(self):
        first_digit = re.search("\d", self.tag_number)
        first_digit = first_digit.group()[0] if first_digit else "N/A"
    
    def __repr__(self):
        return f"{self.sex} with tag {self.tag_number} owned by {self.owner}"


class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

    def get_cows(self):
        return self.cows

    def search(self, query):
        if query.lower() in repr(self).lower():
            return SearchResult(self.name, repr(self).replace(query, f"<b>{query}</b>"), f"/event/{self.event_id}")

    def __repr__(self):
        return f"Event on {self.date}: {self.name} - {self.description}"


class SearchResult():
    def __init__(self, title, body, url):
        self.title = title
        self.body = Markup(body)
        self.url = url
