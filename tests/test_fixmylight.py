import os
from datetime import datetime, timedelta, timezone

import pytest


@pytest.fixture()
def env(tmp_path, monkeypatch):
    from fixmylight.config import Config
    monkeypatch.setattr(Config, "DATABASE", str(tmp_path / "t.sqlite3"))
    monkeypatch.setattr(Config, "DRY_RUN", True)
    monkeypatch.setattr(Config, "SKIP_WEEKENDS", False)
    monkeypatch.setattr(Config, "MAX_FOLLOWUPS", 3)
    monkeypatch.setattr(Config, "ANTHROPIC_API_KEY", "")
    from fixmylight import db
    return db.connect(Config.DATABASE)


def _report(conn, name="Jan Smuts Ave and Bolton Rd", **kw):
    from fixmylight import db
    from fixmylight.followup import send_initial
    f = db.create_fault(conn, intersection=name, suburb="Rosebank", lat=kw.get("lat"),
                        lng=kw.get("lng"), fault_type="off", details="")
    send_initial(conn, f)
    return db.get(conn, f["public_id"])


def test_initial_email_logged(env):
    f = _report(env)
    assert f["thread_msgid"]
    assert env.execute("SELECT count(*) FROM emails").fetchone()[0] == 1


def test_no_followup_same_day(env):
    from fixmylight.followup import run
    _report(env)
    assert run(env)["sent"] == []


def test_followup_next_day_threads_and_stops_when_fixed(env):
    from fixmylight import db
    from fixmylight.followup import run
    f = _report(env)
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    assert run(env, tomorrow)["sent"] == [f["public_id"]]
    body = env.execute("SELECT body FROM emails WHERE kind='followup'").fetchone()[0]
    assert "follow-up #1" in body
    db.set_status(env, f["id"], "fixed")
    assert run(env, tomorrow + timedelta(days=1))["sent"] == []


def test_max_followups_escalates(env):
    from fixmylight import db
    from fixmylight.followup import run
    f = _report(env)
    t = datetime.now(timezone.utc)
    for i in range(1, 5):
        env.execute("UPDATE faults SET last_emailed_at=? WHERE id=?",
                    ((t - timedelta(days=2)).isoformat(), f["id"]))
        env.commit()
        run(env, t)
    f = db.get(env, f["public_id"])
    assert f["followups_sent"] == 3 and f["status"] == "escalated"


def test_duplicates_merge(env):
    from fixmylight import db
    _report(env, lat=-26.1460, lng=28.0390)
    assert db.find_duplicate(env, "jan smuts ave  and bolton rd", None, None, 75)
    assert db.find_duplicate(env, "somewhere else", -26.1462, 28.0391, 75)
    assert db.find_duplicate(env, "somewhere else", -26.20, 28.04, 75) is None


def test_reference_appears_in_subject(env):
    from fixmylight import compose, db
    f = _report(env)
    db.set_reference(env, f["id"], "JRA-12345")
    f = db.get(env, f["public_id"])
    assert "JRA-12345" in compose.subject(f, "followup")


def test_web_form_flow(env):
    from fixmylight.app import create_app
    client = create_app().test_client()
    r = client.get("/")
    assert r.status_code == 200 and b'<html lang="en-ZA">' in r.data
    r = client.post("/report", data={"intersection": ""})
    assert r.status_code == 422 and b'role="alert"' in r.data and b'aria-invalid="true"' in r.data
    r = client.post("/report", data={"intersection": "Oxford Rd and Riviera Rd", "fault_type": "flashing"})
    assert r.status_code == 302 and "token=" in r.headers["Location"]
    r = client.post("/report", data={"intersection": "oxford rd and riviera rd", "fault_type": "off"})
    assert "dup=1" in r.headers["Location"]
    assert client.get("/faults").status_code == 200


def test_next_run_is_next_0710_johannesburg():
    from fixmylight.scheduler import next_run, TZ
    before = datetime(2026, 10, 8, 6, 0, tzinfo=TZ)
    after = datetime(2026, 10, 8, 8, 0, tzinfo=TZ)
    assert next_run(before).strftime("%Y-%m-%d %H:%M") == "2026-10-08 07:10"
    assert next_run(after).strftime("%Y-%m-%d %H:%M") == "2026-10-09 07:10"


def test_share_links(env):
    from urllib.parse import unquote
    from fixmylight import channels
    f = _report(env)
    s = channels.links(f, "https://example.org/fault/" + f["public_id"])
    assert s["call_href"] == "tel:0860562874"
    assert "@CityofJoburgZA" in unquote(s["x_href"]) and f["intersection"] in unquote(s["x_href"])
    assert s["whatsapp_href"].startswith("https://wa.me/?text=")


def test_metoo_counts_once_and_pages_load(env):
    from fixmylight import db
    from fixmylight.app import create_app
    c = create_app().test_client()
    f = _report(env)
    c.post(f"/fault/{f['public_id']}/metoo")
    c.post(f"/fault/{f['public_id']}/metoo")  # same browser again: not double-counted
    assert db.get(env, f["public_id"])["reporter_count"] == 2
    page = c.get(f"/fault/{f['public_id']}").data
    assert b"Call Joburg Connect" in page and b"Post on X" in page
    assert c.get("/healthz").json == {"ok": True}
    assert c.get("/manifest.webmanifest").mimetype == "application/manifest+json"
    assert c.get("/about").status_code == 200
    assert c.get("/fault/NOPE").status_code == 404
