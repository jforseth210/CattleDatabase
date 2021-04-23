from main import *
cow = Cow.query.filter_by(tag_number='814').first()
cow.events.append(Event(date="2018-01-01", name="Born", description="Born"))
cow.events.append(Event(date="2018-06-02", name="Branded", description="Branded"))
db.session.commit()