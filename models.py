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
    
    def get_transactions(self):
        transactions = []
        for event in self.events:
            for transaction in event.transactions:
                transactions.append(transaction)
        return transactions

    def get_birthdate(self):
        events = self.get_events()
        for event in events:
            if event.name == "Born":
                return event.date

    def search(self, query, tags=[], sexes=[], owners=[], sires=[], dams=[]):
        search_match = query.lower() in repr(self).lower()
        tag_match = not tags or self.get_first_digit_of_tag() in tags
        sex_match = not sexes or self.sex in sexes
        owner_match = not owners or self.owner in owners
        sire_match = not sires or (
            self.get_sire() is not None and self.get_sire().tag_number in sires)
        dam_match = not dams or (
            self.get_dam() is not None and self.get_dam().tag_number in dams)
        return search_match and tag_match and sex_match and owner_match and sire_match and dam_match

    def toSearchResult(self, query):
        return SearchResult(self.tag_number, repr(self).replace(query, f"<b>{query}</b>"), f"/cow/{self.tag_number}")

    def get_first_digit_of_tag(self):
        first_digit = re.search("\d", self.tag_number)
        first_digit = first_digit.group()[0] if first_digit else "N/A"
        return first_digit

    def __repr__(self):
        return f"{self.sex} with tag {self.tag_number} owned by {self.owner}"


class Event(db.Model):
    event_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    name = db.Column(db.String(100))
    description = db.Column(db.Text)

    def get_cows(self):
        return self.cows

    def search(self, query, dates=[], names=[]):
        query_match = query.lower() in repr(self).lower()
        date_match = not dates or self.date in dates
        name_match = not names or self.name in names
        return query_match and date_match and name_match

    def toSearchResult(self, query):
        return SearchResult(self.name, repr(self).replace(query, f"<b>{query}</b>"), f"/event/{self.event_id}")

    def __repr__(self):
        return f"Event on {self.date}: {self.name} - {self.description}"


class Transaction(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    price = db.Column(db.Float)
    tofrom = db.Column(db.String(255))
    description = db.Column(db.Text)

    event_id = db.Column('event_id', db.Integer, db.ForeignKey(
        'event.event_id'), nullable=False)

    event = db.relationship(
        'Event', backref=db.backref('transactions', lazy=True))

    def get_cows(self):
        return [transaction for transaction in self.event.cows]

    def get_date(self):
        return self.event.date

    def get_formatted_price(self):
        return "${:,.2f}".format(self.price)


    def get_formatted_total(self):
        return "${:,.2f}".format(self.price * len(self.cows))

    def search(self, query, prices=[], names=[]):
        query_match = query.lower() in repr(self).lower()
        price_match = not prices or self.price in prices
        name_match = not names or self.name in names
        return query_match and price_match and name_match

    def toSearchResult(self, query):
        if query:
            return SearchResult(self.name, repr(self).replace(query, f"<b>{query}</b>"), f"/transaction/{self.transaction_id}")
        return SearchResult(self.name, repr(self), f"/transaction/{self.transaction_id}")
    def __repr__(self):
        if self.price > 0:
            return f"Transaction: ${self.price} from {self.tofrom} for {self.name} -{self.description}"
        return f"Transaction: ${self.price} to {self.tofrom} for {self.name} -{self.description}"


class SearchResult():
    def __init__(self, title, body, url):
        self.title = title
        self.body = Markup(body)
        self.url = url
