from flask import Flask, render_template, request, redirect, url_for, session
import requests, json
from datetime import datetime
from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

app = Flask(__name__)

@app.before_request
def require_login():

    allowed_routes = ["login", "static"]

    if request.endpoint not in allowed_routes and not session.get("authenticated"):
        return redirect(url_for("login"))


# session secret
app.secret_key = "change_this_secret_key"

# password from .env
APP_PASSWORD = os.getenv("APP_PASSWORD")

NETLIFY_API = "https://api.netlify.com/api/v1/sites"


# --------- MongoDB connection ----------
mongo_client = MongoClient(os.getenv("MONGO_URI"))

db = mongo_client[os.getenv("MONGO_DB")]

accounts_collection = db[os.getenv("MONGO_COLLECTION")]
# --------------------------------------


# --------- time formatting helper ----------
def format_time(timestr):

    if not timestr:
        return ""

    try:
        dt = datetime.fromisoformat(timestr.replace("Z", ""))
        return dt.strftime("%d %b %Y %I:%M %p")
    except:
        return timestr
# -----------------------------------------------


# --------- authentication check ----------
def check_auth():

    if not session.get("authenticated"):
        return False

    return True
# -----------------------------------------------


# --------- login route ----------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        password = request.form.get("password")
        print(password,APP_PASSWORD)
        if password == APP_PASSWORD:

            session["authenticated"] = True
            return redirect(url_for("index"))

    return render_template("login.html")
# -----------------------------------------------


# --------- logout ----------
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))
# -----------------------------------------------


# --------- load accounts from MongoDB ----------
def load_accounts():

    accounts = list(accounts_collection.find({}, {"_id":0}))

    return accounts
# -----------------------------------------------


def get_sites(token):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(NETLIFY_API, headers=headers)

    sites = []

    for site in r.json():

        build = site.get("build_settings", {})

        repo = build.get("repo_url")

        github_user = None
        repo_name = None

        if repo:
            parts = repo.split("/")
            github_user = parts[3]
            repo_name = parts[4]

        sites.append({
            "name": site.get("name"),
            "url": site.get("url"),
            "created": site.get("created_at"),
            "created_formatted": format_time(site.get("created_at")),
            "repo": repo,
            "github_user": github_user,
            "repo_name": repo_name,
            "screenshot": site.get("screenshot_url")
        })

    return sites


# --------- Vercel project fetch ----------
def get_vercel_projects(token):

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(
        "https://api.vercel.com/v9/projects",
        headers=headers
    )

    projects = []
    print(projects)

    for p in r.json().get("projects", []):

        repo = None
        github_user = None
        repo_name = None

        git = p.get("link")

        if git:
            repo_name = git.get("repo")
            github_user = git.get("org")
            repo = f"https://github.com/{github_user}/{repo_name}" if github_user and repo_name else None

        projects.append({
            "name": p.get("name"),
            "url": f"https://{p.get('name')}.vercel.app",
            "created": "",
            "created_formatted": "",
            "repo": repo,
            "github_user": github_user,
            "repo_name": repo_name,
            "screenshot": None
        })

    return projects
# -----------------------------------------------


@app.route("/")
def index():

    if not check_auth():
        return redirect(url_for("login"))

    accounts = load_accounts()

    return render_template("index.html", accounts=accounts)


@app.route("/sites")
def sites():

    if not check_auth():
        return redirect(url_for("login"))

    account_num = int(request.args.get("account"))

    accounts = load_accounts()

    token = None
    account_title = None
    provider = "netlify"

    for acc in accounts:
        if acc["account_num"] == account_num:
            token = acc["token"]
            account_title = acc["account_title"]
            provider = acc.get("provider", "netlify")
            break

    if provider == "vercel":
        sites = get_vercel_projects(token)
    else:
        sites = get_sites(token)

    return render_template(
        "sites.html",
        sites=sites,
        account_title=account_title
    )


if __name__ == "__main__":
    app.run(debug=True)