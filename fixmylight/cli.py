"""Command line: `python -m fixmylight serve | followup | report | list | fixed`."""
import argparse
import json

from . import db
from .config import Config
from .followup import run, send_initial


def main(argv=None):
    p = argparse.ArgumentParser(prog="fixmylight", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="run the web form")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=5000)
    sub.add_parser("followup", help="send today's follow-ups (run once a day)")
    r = sub.add_parser("report", help="report a fault from the terminal")
    r.add_argument("intersection")
    r.add_argument("--suburb", default="")
    r.add_argument("--type", default="off", dest="fault_type")
    r.add_argument("--details", default="")
    r.add_argument("--lat", type=float)
    r.add_argument("--lng", type=float)
    sub.add_parser("list", help="list faults")
    for name in ("fixed", "pause", "reopen"):
        x = sub.add_parser(name, help=f"mark a fault {name}")
        x.add_argument("public_id")
    ref = sub.add_parser("ref", help="store the city's reference number")
    ref.add_argument("public_id")
    ref.add_argument("reference")
    a = p.parse_args(argv)

    if a.cmd == "serve":
        from .app import create_app
        create_app().run(host=a.host, port=a.port)
        return
    conn = db.connect(Config.DATABASE)
    if a.cmd == "followup":
        print(json.dumps(run(conn), indent=2))
    elif a.cmd == "report":
        dup = db.find_duplicate(conn, a.intersection, a.lat, a.lng, Config.DEDUP_RADIUS_M)
        if dup:
            db.add_reporter(conn, dup["id"])
            print(f"Already tracked as {dup['public_id']}; added your report to it.")
            return
        f = db.create_fault(conn, intersection=a.intersection, suburb=a.suburb, lat=a.lat, lng=a.lng,
                            fault_type=a.fault_type, details=a.details)
        send_initial(conn, f)
        print(f"Reported as {f['public_id']}")
    elif a.cmd == "list":
        for f in conn.execute("SELECT * FROM faults ORDER BY created_at DESC"):
            print(f"{f['public_id']}  {f['status']:<9} follow-ups={f['followups_sent']:<3} {f['intersection']}")
    elif a.cmd in ("fixed", "pause", "reopen"):
        f = db.get(conn, a.public_id) or exit(f"No fault {a.public_id}")
        db.set_status(conn, f["id"], {"fixed": "fixed", "pause": "paused", "reopen": "open"}[a.cmd])
        print("Updated.")
    elif a.cmd == "ref":
        f = db.get(conn, a.public_id) or exit(f"No fault {a.public_id}")
        db.set_reference(conn, f["id"], a.reference)
        print("Reference saved; follow-ups will quote it.")


if __name__ == "__main__":
    main()
