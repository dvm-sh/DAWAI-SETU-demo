import sqlite3
import json
import os
import csv
import io
from datetime import date, datetime, timedelta
from flask import Flask, render_template, jsonify, request, redirect, url_for, Response, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")
DB_PATH = "dawai_setu.db"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_expiry_status(expiry_str):
    try:
        exp_date = date.fromisoformat(expiry_str)
        today = date.today()
        days_left = (exp_date - today).days
        if days_left < 0:
            return "Expired", days_left
        elif days_left <= 30:
            return "Critical", days_left
        elif days_left <= 60:
            return "Near Expiry", days_left
        elif days_left <= 90:
            return "Monitor", days_left
        else:
            return "Available", days_left
    except Exception:
        return "Available", 180

def audit(action, entity, previous="", new="", actor="Demo Admin"):
    try:
        conn = db()
        conn.execute("""
            INSERT INTO audit_logs(actor, action, entity, previous_status, new_status, created)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (actor, action, entity, previous, new, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")

def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        batch TEXT NOT NULL UNIQUE,
        quantity INTEGER NOT NULL,
        expiry TEXT NOT NULL,
        storage TEXT DEFAULT 'Room temp 20–25°C',
        location TEXT DEFAULT 'Meerut',
        status TEXT DEFAULT 'Available',
        donor TEXT DEFAULT 'CityCare Pharmacy',
        added TEXT DEFAULT CURRENT_DATE
    );

    CREATE TABLE IF NOT EXISTS organizations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT DEFAULT 'NGO',
        location TEXT NOT NULL,
        distance_km INTEGER DEFAULT 12,
        verified INTEGER DEFAULT 0,
        required_medicine TEXT NOT NULL,
        required_qty INTEGER NOT NULL,
        urgency TEXT DEFAULT 'Medium',
        contact_person TEXT DEFAULT 'Dr. Coordinator',
        phone TEXT DEFAULT '+91 98765 43210'
    );

    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine TEXT NOT NULL,
        batch TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        donor TEXT NOT NULL,
        recipient TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        tracking_code TEXT,
        created TEXT NOT NULL,
        updated TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS disposal_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine TEXT NOT NULL,
        batch TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        expiry TEXT NOT NULL,
        reason TEXT NOT NULL,
        partner TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        manifest_id TEXT,
        created TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        entity TEXT NOT NULL,
        previous_status TEXT,
        new_status TEXT,
        created TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS emergency_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        urgency TEXT DEFAULT 'Critical',
        location TEXT NOT NULL,
        reason TEXT NOT NULL,
        required_by TEXT NOT NULL,
        status TEXT DEFAULT 'Open',
        contact TEXT DEFAULT '+91 98110 00000',
        created TEXT NOT NULL
    );
    """)

    cursor = conn.execute("SELECT COUNT(*) FROM medicines")
    if cursor.fetchone()[0] == 0:
        sample_medicines = [
            ("Paracetamol 650mg", "Analgesic & Antipyretic", "PCM-24081", 500, (date.today() + timedelta(days=48)).isoformat(), "Room temp 20–25°C", "Meerut", "High Surplus Risk", "CityCare Pharmacy", (date.today() - timedelta(days=20)).isoformat()),
            ("Amoxicillin 500mg", "Antibiotic", "AMX-24019", 180, (date.today() + timedelta(days=22)).isoformat(), "Controlled storage 15–20°C", "Meerut", "Critical", "HealthFirst Hospital", (date.today() - timedelta(days=15)).isoformat()),
            ("ORS Sachet Hydration", "Rehydration Electrolytes", "ORS-24110", 850, (date.today() + timedelta(days=210)).isoformat(), "Dry ambient storage", "Meerut", "Available", "Seva Medical Store", (date.today() - timedelta(days=10)).isoformat()),
            ("Azithromycin 250mg", "Antibiotic", "AZI-24072", 120, (date.today() + timedelta(days=34)).isoformat(), "Room temp 20–25°C", "Delhi-NCR", "Near Expiry", "MetroCare Pharmacy", (date.today() - timedelta(days=8)).isoformat()),
            ("Cetirizine 10mg", "Antihistamine", "CET-24144", 450, (date.today() + timedelta(days=145)).isoformat(), "Room temp 20–25°C", "Ghaziabad", "Available", "CityCare Pharmacy", (date.today() - timedelta(days=5)).isoformat()),
            ("Ibuprofen 400mg", "Analgesic & Anti-inflammatory", "IBU-24031", 90, (date.today() + timedelta(days=18)).isoformat(), "Dry storage <25°C", "Meerut", "Critical", "HealthFirst Hospital", (date.today() - timedelta(days=3)).isoformat()),
            ("Metformin 500mg", "Antidiabetic", "MET-24095", 300, (date.today() + timedelta(days=85)).isoformat(), "Room temp 20–25°C", "Noida", "Monitor", "Apex Healthcare Store", (date.today() - timedelta(days=2)).isoformat()),
            ("Cough Syrup Pediatric", "Pediatric Respiratory", "CSP-24012", 40, (date.today() - timedelta(days=5)).isoformat(), "Room temp 20–25°C", "Meerut", "Expired", "Lifeline Chemist", (date.today() - timedelta(days=30)).isoformat()),
        ]
        conn.executemany("""
            INSERT INTO medicines (name, category, batch, quantity, expiry, storage, location, status, donor, added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_medicines)

        sample_orgs = [
            ("ABC Healthcare NGO", "NGO", "Meerut Cantt", 14, 1, "Paracetamol 650mg", 250, "High", "Dr. A. Verma", "+91 98370 12345"),
            ("Sehat Relief Foundation", "Charity Clinic", "Ghaziabad East", 28, 1, "Amoxicillin 500mg", 150, "Critical", "Sister Rita", "+91 98111 23456"),
            ("NCR Community Hospital", "Public Hospital", "East Delhi", 42, 1, "ORS Sachet Hydration", 400, "High", "Dr. S. K. Gupta", "+91 98100 34567"),
            ("Jan Arogya Trust", "NGO", "Modinagar", 19, 0, "Azithromycin 250mg", 80, "Critical", "M. Sharma", "+91 97560 45678"),
            ("Gramin Swasthya Mission", "Rural Health Subcenter", "Hapur Rural", 35, 1, "Ibuprofen 400mg", 75, "High", "R. P. Singh", "+91 94120 56789"),
        ]
        conn.executemany("""
            INSERT INTO organizations (name, type, location, distance_km, verified, required_medicine, required_qty, urgency, contact_person, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_orgs)

        sample_transfers = [
            ("Paracetamol 650mg", "PCM-24081", 200, "CityCare Pharmacy", "ABC Healthcare NGO", "In Transit", "TRK-26296-01", (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M"), (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")),
            ("ORS Sachet Hydration", "ORS-24110", 300, "Seva Medical Store", "NCR Community Hospital", "Completed", "TRK-26296-02", (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"), (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")),
            ("Azithromycin 250mg", "AZI-24072", 50, "MetroCare Pharmacy", "Sehat Relief Foundation", "Pending", "TRK-26296-03", (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M"), (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M")),
        ]
        conn.executemany("""
            INSERT INTO transfers (medicine, batch, quantity, donor, recipient, status, tracking_code, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_transfers)

        sample_disposals = [
            ("Cough Syrup Pediatric", "CSP-24012", 40, (date.today() - timedelta(days=5)).isoformat(), "Passed safety shelf-life threshold", "Meerut Biomedical Waste Management Ltd", "Disposed", "MAN-DISP-0841", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")),
        ]
        conn.executemany("""
            INSERT INTO disposal_requests (medicine, batch, quantity, expiry, reason, partner, status, manifest_id, created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_disposals)

        sample_emergencies = [
            ("Paracetamol 650mg & ORS", 300, "Critical", "Meerut District Flood Relief Camp", "Sudden gastro outbreak in low-lying settlement", "District Health Officer Meerut", "Open", "+91 94122 88899", (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M")),
            ("Amoxicillin 500mg", 100, "High", "Ghaziabad Shelter Home", "Pediatric & elderly chest infection cluster", "Sehat Foundation", "Open", "+91 98110 55544", (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")),
        ]
        conn.executemany("""
            INSERT INTO emergency_requests (medicine, quantity, urgency, location, reason, required_by, status, contact, created)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_emergencies)

        initial_audits = [
            ("System Daemon", "DAWAI-SETU Platform Initialized", "Meerut Regional Node", "", "Operational", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")),
            ("Demo Admin", "Batch Intake Registered", "PCM-24081 / Paracetamol 650mg", "New", "High Surplus Risk", (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")),
            ("AI Match Engine", "Surplus Allocation Triggered", "PCM-24081 -> ABC Healthcare NGO", "Pending", "Matched", (datetime.now() - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")),
            ("Logistics Node", "Transfer Status Dispatched", "Transfer #TRK-26296-01", "Scheduled", "In Transit", (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")),
        ]
        conn.executemany("""
            INSERT INTO audit_logs (actor, action, entity, previous_status, new_status, created)
            VALUES (?, ?, ?, ?, ?, ?)
        """, initial_audits)

    conn.commit()
    conn.close()

init_db()

# ==========================================
# STATIC ASSET DIRECT SERVING (style.css & app.js)
# ==========================================
@app.route("/style.css")
def root_css():
    return send_from_directory("static", "style.css")

@app.route("/app.js")
def root_js():
    return send_from_directory("static", "app.js")

# ==========================================
# PAGE ROUTES (Supporting direct .html file names)
# ==========================================

@app.route("/")
@app.route("/index.html")
def index():
    return render_template("index.html", active_page="home")

@app.route("/dashboard")
@app.route("/dashboard.html")
def dashboard():
    return render_template("dashboard.html", active_page="dashboard")

@app.route("/inventory")
@app.route("/inventory.html")
def inventory():
    conn = db()
    medicines = [dict(row) for row in conn.execute("SELECT * FROM medicines ORDER BY expiry ASC").fetchall()]
    conn.close()
    
    for m in medicines:
        status, days_left = calculate_expiry_status(m["expiry"])
        m["days_left"] = days_left
        if days_left < 0:
            m["status"] = "Expired"
    
    return render_template("inventory.html", medicines=medicines, active_page="inventory")

@app.route("/matching")
@app.route("/matching.html")
def matching():
    conn = db()
    medicines = [dict(row) for row in conn.execute("SELECT * FROM medicines WHERE status != 'Expired' ORDER BY expiry ASC").fetchall()]
    orgs = [dict(row) for row in conn.execute("SELECT * FROM organizations ORDER BY verified DESC, urgency DESC").fetchall()]
    conn.close()
    return render_template("matching.html", medicines=medicines, orgs=orgs, active_page="matching")

@app.route("/transfers")
@app.route("/transfers.html")
def transfers():
    conn = db()
    transfers_list = [dict(row) for row in conn.execute("SELECT * FROM transfers ORDER BY id DESC").fetchall()]
    conn.close()
    return render_template("transfers.html", transfers=transfers_list, active_page="transfers")

@app.route("/disposal")
@app.route("/disposal.html")
def disposal():
    conn = db()
    disposal_list = [dict(row) for row in conn.execute("SELECT * FROM disposal_requests ORDER BY id DESC").fetchall()]
    expired_medicines = [dict(row) for row in conn.execute("SELECT * FROM medicines WHERE status IN ('Expired', 'Critical')").fetchall()]
    conn.close()
    return render_template("disposal.html", disposal=disposal_list, expired_medicines=expired_medicines, active_page="disposal")

@app.route("/admin")
@app.route("/admin.html")
def admin():
    conn = db()
    orgs = [dict(row) for row in conn.execute("SELECT * FROM organizations ORDER BY id ASC").fetchall()]
    emergencies = [dict(row) for row in conn.execute("SELECT * FROM emergency_requests ORDER BY id DESC").fetchall()]
    conn.close()
    return render_template("admin.html", orgs=orgs, emergencies=emergencies, active_page="admin")

# Legacy folder-prefix route compatibility
@app.route("/dawai_setu/templates/<path:page_name>")
def legacy_templates(page_name):
    clean = page_name.replace(".html", "")
    if clean in ["index", "home"]:
        return redirect("/index.html")
    elif clean in ["dashboard", "inventory", "matching", "transfers", "disposal", "admin"]:
        return redirect(f"/{clean}.html")
    return redirect("/index.html")

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.get("/api/stats")
def get_stats():
    conn = db()
    total_medicines = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
    total_quantity = conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM medicines").fetchone()[0]
    near_expiry = conn.execute("SELECT COUNT(*) FROM medicines WHERE status IN ('Near Expiry', 'Critical', 'High Surplus Risk')").fetchone()[0]
    redistributed_qty = conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM transfers WHERE status IN ('Completed', 'In Transit', 'Collected', 'Verified')").fetchone()[0]
    disposed_qty = conn.execute("SELECT COALESCE(SUM(quantity), 0) FROM disposal_requests WHERE status = 'Disposed'").fetchone()[0]
    active_transfers = conn.execute("SELECT COUNT(*) FROM transfers WHERE status NOT IN ('Completed', 'Cancelled')").fetchone()[0]
    verified_orgs = conn.execute("SELECT COUNT(*) FROM organizations WHERE verified = 1").fetchone()[0]
    open_emergencies = conn.execute("SELECT COUNT(*) FROM emergency_requests WHERE status = 'Open'").fetchone()[0]
    conn.close()

    waste_diverted_kg = round(redistributed_qty * 0.05, 1)
    co2_saved_kg = round(waste_diverted_kg * 0.42, 1)

    return jsonify(
        total_medicines=total_medicines,
        total_quantity=total_quantity,
        near_expiry=near_expiry,
        redistributed=redistributed_qty,
        disposed=disposed_qty,
        active_transfers=active_transfers,
        verified_orgs=verified_orgs,
        waste_avoided=redistributed_qty,
        waste_diverted_kg=waste_diverted_kg,
        co2_saved_kg=co2_saved_kg,
        open_emergencies=open_emergencies
    )

@app.get("/api/medicines")
def get_medicines():
    conn = db()
    medicines = [dict(row) for row in conn.execute("SELECT * FROM medicines ORDER BY expiry ASC").fetchall()]
    conn.close()
    for m in medicines:
        status, days_left = calculate_expiry_status(m["expiry"])
        m["days_left"] = days_left
    return jsonify(medicines)

@app.post("/api/medicines")
def add_medicine():
    try:
        data = request.json or request.form
        name = data.get("name", "").strip()
        category = data.get("category", "General").strip()
        batch = data.get("batch", "").strip().upper()
        quantity = int(data.get("quantity", 0))
        expiry = data.get("expiry", "").strip()
        storage = data.get("storage", "Room temp 20–25°C").strip()
        location = data.get("location", "Meerut").strip()
        donor = data.get("donor", "CityCare Pharmacy").strip()

        if not name or not batch or quantity <= 0 or not expiry:
            return jsonify(ok=False, error="Name, batch, positive quantity, and expiry date are required."), 400

        status, days_left = calculate_expiry_status(expiry)
        if status == "Critical" or (days_left < 60 and quantity > 200):
            status = "High Surplus Risk"

        conn = db()
        conn.execute("""
            INSERT INTO medicines (name, category, batch, quantity, expiry, storage, location, status, donor, added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, category, batch, quantity, expiry, storage, location, status, donor, date.today().isoformat()))
        conn.commit()
        conn.close()

        audit("Medicine Batch Intake", f"{name} (Batch {batch})", "", status)
        return jsonify(ok=True, status=status, batch=batch, message=f"Batch {batch} recorded with status: {status}")
    except sqlite3.IntegrityError:
        return jsonify(ok=False, error=f"Batch number '{batch}' already exists. Please provide a unique batch."), 409
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/medicines/<int:mid>/action")
def update_medicine_action(mid):
    try:
        data = request.json
        action = data.get("action")
        conn = db()
        med = conn.execute("SELECT * FROM medicines WHERE id = ?", (mid,)).fetchone()
        if not med:
            conn.close()
            return jsonify(ok=False, error="Medicine not found"), 404

        old_status = med["status"]
        if action == "mark_surplus":
            new_status = "High Surplus Risk"
            conn.execute("UPDATE medicines SET status = ? WHERE id = ?", (new_status, mid))
            audit("Marked Surplus", f"{med['name']} ({med['batch']})", old_status, new_status)
        elif action == "route_disposal":
            new_status = "Routed for Disposal"
            conn.execute("UPDATE medicines SET status = ? WHERE id = ?", (new_status, mid))
            manifest_id = f"MAN-DISP-{datetime.now().strftime('%m%d%H%M')}"
            conn.execute("""
                INSERT INTO disposal_requests (medicine, batch, quantity, expiry, reason, partner, status, manifest_id, created)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (med["name"], med["batch"], med["quantity"], med["expiry"], "Designated for safe disposal by administrator", "Meerut Biomedical Waste Management Ltd", "Pending", manifest_id, datetime.now().strftime("%Y-%m-%d %H:%M")))
            audit("Routed to Eco-Disposal", f"{med['name']} ({med['batch']})", old_status, new_status)
        else:
            conn.close()
            return jsonify(ok=False, error="Unknown action"), 400

        conn.commit()
        conn.close()
        return jsonify(ok=True, message=f"Action '{action}' executed successfully.")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/api/matching/recommendations")
def get_matching_recommendations():
    conn = db()
    orgs = [dict(row) for row in conn.execute("SELECT * FROM organizations WHERE verified = 1").fetchall()]
    conn.close()

    results = []
    for o in orgs:
        score = 65
        if o["urgency"] == "Critical":
            score += 20
        elif o["urgency"] == "High":
            score += 12
        elif o["urgency"] == "Medium":
            score += 6
        
        dist = o.get("distance_km", 20)
        if dist <= 15:
            score += 12
        elif dist <= 30:
            score += 7
        else:
            score += 2

        if o["verified"] == 1:
            score += 5

        score = min(98, max(50, score))
        o["match_score"] = score
        results.append(o)

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return jsonify(results)

@app.post("/api/transfers")
def create_transfer():
    try:
        data = request.json
        medicine = data.get("medicine", "Paracetamol 650mg")
        batch = data.get("batch", "PCM-24081")
        quantity = int(data.get("quantity", 100))
        donor = data.get("donor", "CityCare Pharmacy")
        recipient = data.get("recipient", "ABC Healthcare NGO")

        tracking_code = f"TRK-26296-{datetime.now().strftime('%H%M%S')}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = db()
        conn.execute("""
            INSERT INTO transfers (medicine, batch, quantity, donor, recipient, status, tracking_code, created, updated)
            VALUES (?, ?, ?, ?, ?, 'Pending', ?, ?, ?)
        """, (medicine, batch, quantity, donor, recipient, tracking_code, now_str, now_str))
        conn.commit()
        conn.close()

        audit("Transfer Consignment Created", f"{medicine} ({quantity} units) -> {recipient}", "New", "Pending")
        return jsonify(ok=True, tracking_code=tracking_code, message=f"Transfer {tracking_code} initiated successfully.")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/transfer/<int:tid>/status")
def update_transfer_status(tid):
    try:
        data = request.json
        target_status = data.get("status")
        valid_statuses = ["Pending", "Accepted", "Scheduled", "Collected", "In Transit", "Verified", "Completed", "Cancelled"]

        if target_status not in valid_statuses:
            return jsonify(ok=False, error=f"Invalid status. Must be one of {valid_statuses}"), 400

        conn = db()
        current = conn.execute("SELECT * FROM transfers WHERE id = ?", (tid,)).fetchone()
        if not current:
            conn.close()
            return jsonify(ok=False, error="Transfer not found"), 404

        old_status = current["status"]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn.execute("UPDATE transfers SET status = ?, updated = ? WHERE id = ?", (target_status, now_str, tid))
        conn.commit()
        conn.close()

        audit("Transfer Status Transition", f"Transfer #{tid} ({current['medicine']})", old_status, target_status)
        return jsonify(ok=True, new_status=target_status, message=f"Transfer #{tid} updated to {target_status}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/disposal")
def create_disposal():
    try:
        data = request.json
        medicine = data.get("medicine")
        batch = data.get("batch")
        quantity = int(data.get("quantity", 0))
        expiry = data.get("expiry", date.today().isoformat())
        reason = data.get("reason", "Expired stock")
        partner = data.get("partner", "Meerut Biomedical Waste Management Ltd")

        if not medicine or not batch or quantity <= 0:
            return jsonify(ok=False, error="Medicine, batch, and valid quantity required"), 400

        manifest_id = f"MAN-DISP-{datetime.now().strftime('%y%m%d-%H%M')}"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = db()
        conn.execute("""
            INSERT INTO disposal_requests (medicine, batch, quantity, expiry, reason, partner, status, manifest_id, created)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending', ?, ?)
        """, (medicine, batch, quantity, expiry, reason, partner, manifest_id, now_str))
        conn.commit()
        conn.close()

        audit("Eco-Disposal Manifest Created", f"{medicine} ({batch}) - Manifest {manifest_id}", "New", "Pending")
        return jsonify(ok=True, manifest_id=manifest_id, message="Disposal manifest registered for authorized pickup.")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/org/<int:oid>/verify")
def toggle_org_verification(oid):
    try:
        data = request.json or {}
        new_state = 1 if data.get("verified", True) else 0
        conn = db()
        org = conn.execute("SELECT * FROM organizations WHERE id = ?", (oid,)).fetchone()
        if not org:
            conn.close()
            return jsonify(ok=False, error="Organization not found"), 404

        old_str = "Verified" if org["verified"] == 1 else "Pending"
        new_str = "Verified" if new_state == 1 else "Pending"

        conn.execute("UPDATE organizations SET verified = ? WHERE id = ?", (new_state, oid))
        conn.commit()
        conn.close()

        audit("Organization Verification Status", org["name"], old_str, new_str)
        return jsonify(ok=True, verified=new_state, message=f"{org['name']} verification status set to {new_str}")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/api/audit")
def get_audit_trail():
    query = request.args.get("q", "").strip().lower()
    conn = db()
    if query:
        rows = conn.execute("""
            SELECT * FROM audit_logs
            WHERE LOWER(actor) LIKE ? OR LOWER(action) LIKE ? OR LOWER(entity) LIKE ?
            ORDER BY id DESC LIMIT 100
        """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 100").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.post("/api/emergency")
def submit_emergency():
    try:
        data = request.json
        medicine = data.get("medicine", "").strip()
        quantity = int(data.get("quantity", 0))
        urgency = data.get("urgency", "Critical")
        location = data.get("location", "Meerut").strip()
        reason = data.get("reason", "").strip()
        required_by = data.get("required_by", "Emergency Shelter").strip()
        contact = data.get("contact", "+91 98110 00000").strip()

        if not medicine or quantity <= 0 or not reason:
            return jsonify(ok=False, error="Medicine, valid quantity, and clinical reason are required."), 400

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        conn = db()
        conn.execute("""
            INSERT INTO emergency_requests (medicine, quantity, urgency, location, reason, required_by, status, contact, created)
            VALUES (?, ?, ?, ?, ?, ?, 'Open', ?, ?)
        """, (medicine, quantity, urgency, location, reason, required_by, contact, now_str))
        conn.commit()
        conn.close()

        audit("Emergency SOS Broadcast", f"{medicine} ({quantity} units) @ {location}", "New", "Open Broadcast")
        return jsonify(ok=True, message="Emergency broadcast activated across all regional network nodes.")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/emergency/<int:eid>/resolve")
def resolve_emergency(eid):
    try:
        conn = db()
        conn.execute("UPDATE emergency_requests SET status = 'Resolved' WHERE id = ?", (eid,))
        conn.commit()
        conn.close()
        audit("Emergency Call Resolved", f"Emergency #{eid}", "Open", "Resolved")
        return jsonify(ok=True, message="Emergency request marked as resolved.")
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.post("/api/ai/forecast")
def ai_forecast():
    try:
        data = request.json or {}
        batch_stock = int(data.get("stock", 500))
        daily_dispense_rate = float(data.get("daily_dispense", 4.2))
        days_to_expiry = int(data.get("days_to_expiry", 48))
        monsoon_surge_pct = float(data.get("surge_factor", 1.0))

        adjusted_rate = daily_dispense_rate * monsoon_surge_pct
        predicted_local_demand = min(batch_stock, int(adjusted_rate * days_to_expiry))
        predicted_surplus = max(0, batch_stock - predicted_local_demand)
        risk_tier = "High Surplus Risk" if predicted_surplus > (batch_stock * 0.4) else ("Moderate Surplus" if predicted_surplus > 0 else "Optimal Balance")

        confidence_score = 94.2

        return jsonify(
            ok=True,
            stock=batch_stock,
            days_to_expiry=days_to_expiry,
            adjusted_daily_rate=round(adjusted_rate, 2),
            predicted_local_demand=predicted_local_demand,
            predicted_surplus=predicted_surplus,
            risk_tier=risk_tier,
            confidence_score=confidence_score,
            action_recommendation="Trigger immediate verified NGO redistribution" if predicted_surplus > 0 else "Maintain current inventory flow"
        )
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500

@app.get("/api/export/inventory")
def export_inventory_csv():
    conn = db()
    rows = conn.execute("SELECT * FROM medicines ORDER BY expiry ASC").fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["ID", "Medicine Name", "Category", "Batch Number", "Quantity", "Expiry Date", "Storage Requirements", "Location", "Status", "Donor Organization", "Added Date"])
    for r in rows:
        cw.writerow([r["id"], r["name"], r["category"], r["batch"], r["quantity"], r["expiry"], r["storage"], r["location"], r["status"], r["donor"], r["added"]])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=dawai_setu_inventory.csv"}
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
