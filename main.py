import json
import re
import subprocess
import socket
import contextlib
import io
import sys
import os
import platform
import time
import logging
import urllib.parse
from getpass import getpass
import argparse

# Trying to get this installed on Windows is agnonizing
# This might help: https://github.com/miniupnp/miniupnp/issues/159
import miniupnpc
import requests
from flask import Flask, render_template, request, redirect, Markup
from jinja2 import Environment, BaseLoader
from flask_simplelogin import SimpleLogin, login_required
import click
import werkzeug.security

from models import *
from search_functions import *
from setup_utils import *
from sensitive_data import SECRET_KEY

from api import api
from cows import cows
from events import events
from transactions import transactions

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder,
                static_folder=static_folder)
else:
    app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cattle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(cows, url_prefix='/cows')
app.register_blueprint(events, url_prefix='/events')
app.register_blueprint(transactions, url_prefix='/transactions')

db.init_app(app)


app.jinja_env.globals['COW_SEXES'] = COW_SEXES
app.jinja_env.globals['COW_SEXES_FEMALE'] = COW_SEXES_FEMALE
app.jinja_env.globals['COW_SEXES_FEMALE_POSSIBLE_PARENTS'] = COW_SEXES_FEMALE_POSSIBLE_PARENTS
app.jinja_env.globals['COW_SEXES_FEMALE_IMPOSSIBLE_PARENTS'] = COW_SEXES_FEMALE_IMPOSSIBLE_PARENTS
app.jinja_env.globals['COW_SEXES_MALE'] = COW_SEXES_MALE
app.jinja_env.globals['COW_SEXES_MALE_POSSIBLE_PARENTS'] = COW_SEXES_MALE_POSSIBLE_PARENTS
app.jinja_env.globals['COW_SEXES_MALE_IMPOSSIBLE_PARENTS'] = COW_SEXES_MALE_IMPOSSIBLE_PARENTS
def login_checker(provided_user):
    with open("config.json", "r") as file:
        config_string = file.read()
    config = json.loads(config_string)
    users = config["users"]
    for user in users:
        if provided_user["username"] == user["username"] and werkzeug.security.check_password_hash(user["hashed_password"], provided_user["password"]):
            return True
    return False


messages = {
    'login_success': 'Logged In',
    'login_failure': 'Login Failed',
    'is_logged_in': 'Logged In!',
    'logout': 'Logged Out',
    'login_required': 'Please log in first',
    'access_denied': 'You don\'t have access to this page',
    'auth_error': 'Something went wrong： {0}'
}

SimpleLogin(app, login_checker=login_checker, messages=messages)


@app.route("/")
@login_required
def home():
    return redirect("/cows")


@app.route('/calendar/events/api')
def event_api():
    events = Event.query.all()
    formatted_events = []
    for event in events:
        cow_string = ", ".join(cow.tag_number for cow in event.cows)
        formatted_event = {
            'title': event.name + ": " + cow_string,
            'start': event.date,
            'id': event.event_id
        }
        formatted_events.append(formatted_event)
    return json.dumps(formatted_events)


@app.route("/search")
@login_required
def search():
    # Arguments
    query = request.args.get("q")
    # What kind of things are we searching for?
    types = determine_types(request)

    argument_dict = {"types": request.args.getlist("type")}
    if "Cow" in types:
        argument_dict.update({
            "tags": request.args.getlist("tag"),
            "sexes": request.args.getlist("sex"),
            "owners": request.args.getlist("owner"),
            "sires": request.args.getlist("sire"),
            "dams": request.args.getlist("dam")
        })

    if "Event" in types:
        argument_dict.update({
            "dates": request.args.getlist("date"),
            "event_names": request.args.getlist("event_name")
        })

    if "Transaction" in types:
        argument_dict.update({
            "transaction_names": request.args.getlist("transaction_name"),
            "prices": request.args.getlist("price")
        })

    unique_values = get_unique_values()

    results = get_results(types, argument_dict, query)

    # TODO: Fix this mess
    if types == ["Transaction"]:
        if argument_dict["prices"] == ["Low to High"]:
            for i in results:
                print(i.body)
            results.sort(key=lambda x: float(
                re.search("\$.\d+.\d+", x.body).group().strip("$")))
        else:
            results.sort(key=lambda x: float(
                re.search("\$.\d+.\d+", x.body).group().strip("$")), reverse=True)
    # Send it
    return render_template("search.html", query=query, results=results, unique_values=unique_values, checked_values=argument_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true",
                        help="Run the server without opening it in browser")
    parser.add_argument("--show_log", action="store_true",
                        help="Show default flask server information")
    args = parser.parse_args()

    SHOW_SERVER = not args.show_log
    app.debug = True

    if getattr(sys, 'frozen', False) or SHOW_SERVER:
        show_server(args.headless)
        app.debug = False

        # Silence server log
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        def secho(text, file=None, nl=None, err=None, color=None, **styles):
            pass

        def echo(text, file=None, nl=None, err=None, color=None, **styles):
            pass

        click.echo = echo
        click.secho = secho

    app.run(debug=app.debug, host="0.0.0.0")
