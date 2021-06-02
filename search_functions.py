from models import Cow, Event, Transaction


def determine_types(request):
    COW_ARGS = ["tag", "sex", "owner", "sire", "dam"]
    EVENT_ARGS = ["event_name", "date"]
    TRANSACTION_ARGS = ["transaction_name", "price"]
    chosen_types = ["Cow", "Event", "Transaction"]

    # Explicitly filtering by type
    if "type" in request.args:
        chosen_types = request.args.getlist("type")

    # Implicitly filtering by type using filters
    # exclusive to cows, events, or transactions
    for arg in COW_ARGS:
        if arg in request.args:
            # If a not-cow is filtered by a cow attribute, no results
            chosen_types = ["Cow"] if "Cow" in chosen_types else []
    for arg in EVENT_ARGS:
        if arg in request.args:
            chosen_types = ["Event"] if "Event" in chosen_types else []

    for arg in TRANSACTION_ARGS:
        if arg in request.args:
            chosen_types = [
                "Transaction"] if "Transaction" in chosen_types else []

    return chosen_types

def get_unique_values():
    unique_values = {}

    unique_values.update(cow_unique_values())
    unique_values.update(event_unique_values())
    unique_values.update(transaction_unique_values())

    unique_values["types"] = ["Cow", "Event", "Transaction"]
    return unique_values


def cow_unique_values():
    cows = Cow.query.all()
    tags = set()
    sexes = set()
    owners = set()
    sires = set()
    dams = set()

    for cow in cows:
        tags.add(cow.get_first_digit_of_tag())
        sexes.add(cow.sex)
        owners.add(cow.owner)
        if cow.get_dam():
            dams.add(cow.get_dam().tag_number)
        if cow.get_sire():
            sires.add(cow.get_sire().tag_number)

    return {"tags": tags, "sexes": sexes,
            "owners": owners, "sires": sires, "dams": dams}


def event_unique_values():
    events = Event.query.all()

    names = set()
    dates = set()
    for event in events:
        names.add(event.name)
        dates.add(event.date)
    return {"event_names": names, "dates": dates}


def transaction_unique_values():
    transactions = Transaction.query.all()

    names = set()
    prices = set()
    for transaction in transactions:
        names.add(transaction.name)
        prices.add(transaction.price)
    return {"transaction_names": names, "prices": prices}


def get_results(types, argument_dict, query):
    results = []
    if "Cow" in types:
        cows = Cow.query.all()
        for cow in cows:
            if cow.search(query, tags=argument_dict["tags"], sexes=argument_dict["sexes"], owners=argument_dict["owners"],
                          sires=argument_dict["sires"], dams=argument_dict["dams"]):
                results.append(cow.toSearchResult(query))
    if "Event" in types:
        events = Event.query.all()
        for event in events:
            if event.search(
                    query, names=argument_dict["event_names"], dates=argument_dict["dates"]):
                results.append(event.toSearchResult(query))

    if "Transaction" in types:
        transactions = Transaction.query.all()
        for transaction in transactions:
            if transaction.search(
                    query, names=argument_dict["transaction_names"]):
                results.append(transaction.toSearchResult(query))
    return results