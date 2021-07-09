from flask import Blueprint, render_template, request, redirect
from flask_simplelogin import login_required


from models import Transaction, Cow, Event, db, get_cow_from_tag
transactions = Blueprint('transactions', __name__, template_folder='templates')
@transactions.route("/transactions")
@login_required
def show_transactions():
    transactions = Transaction.query.all()
    total = sum(
        transaction.price * len(transaction.cows) for transaction in transactions
    )
    formatted_total = "${:,.2f}".format(total)
    return render_template("transactions.html", transactions=transactions, formatted_total=formatted_total, unformatted_total=total)


@transactions.route("/transaction/<transaction_id>")
@login_required
def show_transaction(transaction_id):
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    if not transaction:
        return redirect(request.referrer)
    return render_template("transaction.html", transaction=transaction, all_cows=Cow.query.all())

@ transactions.route("/new", methods=["POST"])
@login_required
def new_transaction():
    event_id = request.form.get('event_id')
    event = Event.query.filter_by(event_id=event_id).first()

    price = request.form.get('price')
    name = request.form.get('name')
    tofrom = request.form.get('tofrom')
    description = request.form.get('description')
    new_transaction_object = Transaction(
        price=price,
        name=name,
        description=description,
        event_id=event_id,
        tofrom=tofrom,
        cows=event.cows
    )

    db.session.add(new_transaction_object)
    db.session.commit()
    return redirect(request.referrer+"#transactions")


@transactions.route("/update_cows", methods=["POST"])
@login_required
def transaction_add_remove_cows():
    all_cows = request.form.getlist("all_cows")
    new_cow = request.form.get("new_cow")

    transaction_id = request.form.get("transaction")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    if all_cows:
        transaction.cows = [get_cow_from_tag(cow) for cow in all_cows]
    elif new_cow:
        transaction.cows.append(get_cow_from_tag(new_cow))
    db.session.commit()
    return redirect(request.referrer)


@ transactions.route("/change_price", methods=["POST"])
@login_required
def transaction_change_price():
    transaction_id = request.form.get("transaction_id")
    price = request.form.get("price")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.price = price
    db.session.commit()
    return redirect(request.referrer)


@ transactions.route("/change_description", methods=["POST"])
@login_required
def transaction_change_description():
    transaction_id = request.form.get("transaction_id")
    description = request.form.get("description")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.description = description
    db.session.commit()
    return redirect(request.referrer)


@ transactions.route("/change_name", methods=["POST"])
@login_required
def transaction_change_name():
    transaction_id = request.form.get("transaction_id")
    name = request.form.get("name")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.name = name
    db.session.commit()
    return redirect(request.referrer)


@ transactions.route("/change_to_from", methods=["POST"])
@login_required
def transaction_change_to_from():
    transaction_id = request.form.get("transaction_id")
    tofrom = request.form.get("tofrom")

    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    transaction.tofrom = tofrom
    db.session.commit()
    return redirect(request.referrer)


@transactions.route("/deletetransaction", methods=["POST"])
@login_required
def delete_transaction():
    transaction_id = request.form.get("transaction_id")
    transaction = Transaction.query.filter_by(
        transaction_id=transaction_id).first()
    db.session.delete(transaction)
    db.session.commit()

    return redirect('/transactions')
