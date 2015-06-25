from urllib import unquote, quote
from functools import wraps

from flask import Flask, request, render_template, redirect
import requests


app = Flask(__name__)


def ssl_required(fn):
    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not any([app.debug, request.is_secure, request.headers.get("X-Forwarded-Proto", "") == "https"]):
            return redirect(request.url.replace("http://", "https://"))
        else:
            return fn(*args, **kwargs)

    return decorated_view


@ssl_required
@app.route("/")
def meme():
    domain = request.args["team_domain"]
    slackbot = request.args["slackbot"]
    text = request.args["text"]
    channel = request.args["channel_id"]
    user = request.args["user_name"]

    text = unquote(text)
    text = text[:-1] if text[-1] == ";" else text
    params = text.split(";")
    params = [x.strip().replace(" ", "-") for x in params]
    params = [quote(x) for x in params]

    if not len(params) == 3:
        return "Your syntax should be in the form: /meme template; top; bottom;"

    valid_templates = [x["name"] for x in get_templates()]

    template = params[0]

    if template not in valid_templates:
        return "That template doesn't exist. See https://slackbot-meme.herokuapp.com/templates for valid templates."

    top = params[1]
    bottom = params[2]

    data = u"{0} says http://memegen.link/{1}/{2}/{3}.jpg".format(user, template, top, bottom)
    url = "https://{0}.slack.com/services/hooks/slackbot?token={1}&channel={2}".format(domain, slackbot, channel)

    requests.post(url, data=data)

    return "Success!", 200


@ssl_required
@app.route("/templates")
def templates():
    return render_template("templates.html", table=get_templates())


def get_templates():
    response = requests.get("http://memegen.link/templates").json()

    data = []

    for key, value in response.items():
        d = {}
        d["name"] = value.replace("http://memegen.link/templates/", "")
        d["description"] = key
        d["example"] = "/meme {0}; top text; bottom text;".format(d["name"])
        d["result"] = "http://memegen.link/{0}/top-text/bottom-text.jpg".format(d["name"])
        data.append(d)

    return data