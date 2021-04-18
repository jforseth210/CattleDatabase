from main import *
calf = Cow.query.filter_by(tag_number="002").first()
calf.dam_id = Cow.query.filter_by(tag_number="<>801").first().cow_id
calf.sire_id = Cow.query.filter_by(tag_number="Fred").first().cow_id
db.session.commit()