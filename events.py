from flask import Blueprint, render_template, request, redirect, flash, Markup
from flask_simplelogin import login_required
from sqlalchemy.exc import IntegrityError

from models import Event, Cow, db, get_cow_from_tag

events = Blueprint('events', __name__, template_folder='templates')
@events.route('/calendar')
@login_required
def calendar():
    cows = Cow.query.all()
    return render_template('calendar.html', cows=cows)

@events.route("/")
@login_required
def load_events():
    events = Event.query.all()
    cows = Cow.query.all()
    return render_template("events.html", events=events, cows=cows)


@events.route("/event/<event_id>")
@login_required
def show_event(event_id):
    event = Event.query.filter_by(event_id=event_id).first()
    if not event:
        return redirect(request.referrer)
    return render_template("event.html", event=event, cows=Cow.query.all())

@ events.route("/new", methods=["POST"])
@login_required
def new_event():
    tag = request.form.get('tag_number')

    cows = [tag] if tag else request.form.getlist('cows')

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
    return redirect(request.referrer+"#events")


@events.route("/exists/<date>")
@login_required
def check_if_date_exists(date):
    events = Event.query.filter_by(date=date).all()
    if events:
        return f"Found {len(events)} events on {date}: " + ', '.join(
            event.name for event in events
        )
    else:
        return "No events on this date"


@events.route("/update_cows", methods=["POST"])
@login_required
def event_add_remove_cows():
    all_cows = request.form.getlist("all_cows")
    new_cow = request.form.get("new_cow")

    event_id = request.form.get("event")

    event = Event.query.filter_by(event_id=event_id).first()
    if all_cows:
        event.cows = [get_cow_from_tag(cow) for cow in all_cows]
    elif new_cow:
        event.cows.append(get_cow_from_tag(new_cow))
    db.session.commit()
    return redirect(request.referrer)


@ events.route("/change_date", methods=["POST"])
@login_required
def event_change_date():
    event_id = request.form.get("event_id")
    date = request.form.get("date")

    event = Event.query.filter_by(event_id=event_id).first()
    event.date = date
    db.session.commit()
    return redirect(request.referrer)


@ events.route("/change_description", methods=["POST"])
@login_required
def event_change_description():
    event_id = request.form.get("event_id")
    description = request.form.get("description")

    event = Event.query.filter_by(event_id=event_id).first()
    event.description = description
    db.session.commit()
    return redirect(request.referrer)


@ events.route("/change_name", methods=["POST"])
@login_required
def event_change_name():
    event_id = request.form.get("event_id")
    name = request.form.get("name")

    event = Event.query.filter_by(event_id=event_id).first()
    event.name = name
    db.session.commit()
    return redirect(request.referrer)


@events.route("/delete", methods=["POST"])
@login_required
def delete_event():
    event_id = request.form.get("event_id")
    event = Event.query.filter_by(event_id=event_id).first()
    try: 
        db.session.delete(event)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash(
            Markup(
                    "Please delete all transactions from this event first. The following transactions are preventing event deletion: <ul>"
                + "".join("<li>" + transaction.name + "</li>"for transaction in event.transactions)+"</ul>"
            )
        )

        return redirect(request.referrer)
    return redirect('/events')