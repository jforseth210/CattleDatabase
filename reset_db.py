import os
from main import *
from models import *
try:
    os.remove("test.db")
except FileNotFoundError:
    pass
with app.app_context():
    db.create_all()
    cow1 = Cow(tag_number="<>804", owner="Justin", sex="Heifer")
    cow2 = Cow(tag_number="<>819", owner="Justin", sex="Heifer")
    cow3 = Cow(tag_number="<>772", owner="Justin", sex="Heifer")
    cow4 = Cow(tag_number="814", owner="Justin", sex="Heifer")
    db.session.add(cow1)
    db.session.add(cow2)
    db.session.add(cow3)
    db.session.add(cow4)

    bull = Cow(tag_number="Larry", sex="Bull")
    db.session.add(bull)
    db.session.commit()
    calf = Cow(tag_number="001", owner="Justin",
            sex="Steer", 
            dam_id=cow1.cow_id,
            sire_id=bull.cow_id
    )
    calf.events.append(Event(name="Born", description="N/A", date="2021-04-18", transactions=[Transaction(name="Vet Bills", amount=102.29, description="Cesarean"), Transaction(name="Another Transaction", amount=10.24, description="IDK")]))
    db.session.add(calf)
    db.session.commit()
