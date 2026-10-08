"""Web app: report form, one-stop status page for each fault, and a list of all faults."""
import logging

from flask import (Flask, abort, g, make_response, redirect, render_template, request,
                   send_from_directory, url_for)

from . import channels, compose, db, scheduler
from .config import Config
from .followup import send_initial


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    db.connect(Config.DATABASE).close()  # create tables on boot
    scheduler.start()

    def conn():
        if "db" not in g:
            g.db = db.connect(Config.DATABASE)
        return g.db

    @app.teardown_appcontext
    def close(_exc):
        c = g.pop("db", None)
        if c:
            c.close()

    @app.context_processor
    def globals_():
        return {"cfg": Config}

    def page_url(public_id):
        return Config.BASE_URL.rstrip("/") + url_for("status", public_id=public_id)

    @app.get("/")
    def index():
        recent = conn().execute("SELECT * FROM faults WHERE status IN ('open','escalated') "
                                "ORDER BY created_at DESC LIMIT 5").fetchall()
        return render_template("report.html", labels=compose.FAULT_LABELS, errors={}, form={},
                               recent=recent)

    @app.post("/report")
    def report():
        f = request.form
        errors = {}
        intersection = f.get("intersection", "").strip()
        fault_type = f.get("fault_type", "")
        if len(intersection) < 3:
            errors["intersection"] = "Enter the intersection, for example “Jan Smuts Ave and Bolton Rd”."
        if fault_type not in compose.FAULT_LABELS:
            errors["fault_type"] = "Choose what is wrong with the traffic light."
        lat = lng = None
        if f.get("lat") and f.get("lng"):
            try:
                lat, lng = float(f["lat"]), float(f["lng"])
            except ValueError:
                pass
        if f.get("website"):  # honeypot field for bots, hidden from people and screen readers
            abort(400)
        if errors:
            return render_template("report.html", labels=compose.FAULT_LABELS,
                                   errors=errors, form=f, recent=[]), 422

        existing = db.find_duplicate(conn(), intersection, lat, lng, Config.DEDUP_RADIUS_M)
        if existing:
            db.add_reporter(conn(), existing["id"])
            return redirect(url_for("status", public_id=existing["public_id"], dup=1))

        fault = db.create_fault(conn(), intersection=intersection, suburb=f.get("suburb", "").strip(),
                                lat=lat, lng=lng, fault_type=fault_type,
                                details=f.get("details", "").strip()[:1000])
        send_initial(conn(), fault)
        return redirect(url_for("status", public_id=fault["public_id"], new=1,
                                token=fault["manage_token"]))

    @app.get("/fault/<public_id>")
    def status(public_id):
        fault = db.get(conn(), public_id) or abort(404)
        emails = conn().execute("SELECT * FROM emails WHERE fault_id=? ORDER BY id",
                                (fault["id"],)).fetchall()
        token = request.args.get("token", "")
        can_manage = token == fault["manage_token"] or (Config.ADMIN_TOKEN and token == Config.ADMIN_TOKEN)
        return render_template("status.html", fault=fault, emails=emails, labels=compose.FAULT_LABELS,
                               can_manage=can_manage, token=token, share=channels.links(fault, page_url(public_id)),
                               seen=request.cookies.get("seen_" + public_id) == "1",
                               is_new=request.args.get("new"), is_dup=request.args.get("dup"),
                               metoo=request.args.get("metoo"))

    @app.post("/fault/<public_id>/metoo")
    def metoo(public_id):
        fault = db.get(conn(), public_id) or abort(404)
        if fault["status"] in ("open", "escalated") and request.cookies.get("seen_" + public_id) != "1":
            db.add_reporter(conn(), fault["id"])
        resp = make_response(redirect(url_for("status", public_id=public_id, metoo=1)))
        resp.set_cookie("seen_" + public_id, "1", max_age=60 * 60 * 24 * 90, samesite="Lax")
        return resp

    @app.post("/fault/<public_id>/update")
    def update(public_id):
        fault = db.get(conn(), public_id) or abort(404)
        token = request.form.get("token", "")
        if token != fault["manage_token"] and not (Config.ADMIN_TOKEN and token == Config.ADMIN_TOKEN):
            abort(403)
        action = request.form.get("action")
        if action in {"fixed", "paused", "open"}:
            db.set_status(conn(), fault["id"], action)
        if "city_reference" in request.form:
            db.set_reference(conn(), fault["id"], request.form["city_reference"])
        return redirect(url_for("status", public_id=public_id, token=token))

    @app.get("/faults")
    def faults():
        rows = conn().execute("SELECT * FROM faults ORDER BY CASE status WHEN 'open' THEN 0 "
                              "WHEN 'escalated' THEN 1 WHEN 'paused' THEN 2 ELSE 3 END, "
                              "created_at DESC").fetchall()
        return render_template("list.html", faults=rows, labels=compose.FAULT_LABELS)

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/manifest.webmanifest")
    def manifest():
        resp = send_from_directory(app.static_folder, "manifest.webmanifest")
        resp.mimetype = "application/manifest+json"
        return resp

    @app.get("/healthz")
    def healthz():
        conn().execute("SELECT 1")
        return {"ok": True}

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("message.html", title="Page not found",
                               body="We couldn’t find that fault. Check the link, or see all faults."), 404

    return app
