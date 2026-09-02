# DAWAI-SETU (दवाई सेतु)

**Smart India Hackathon 2026 Prototype — Problem Statement #26296**  
*Team Cheek Syndicate*

> **Medicine lifecycle intelligence, AI surplus forecasting, verified redistribution, and eco-compliant biomedical waste governance for India's healthcare supply chain.**

---

## Architecture & Technology Stack

- **Backend**: Python 3 + Flask RESTful micro-framework
- **Database**: SQLite (Local embedded database) + Production PostgreSQL schema (`schema.sql`)
- **Frontend**: HTML5, Modern CSS3 Healthcare Design System (CSS variables, glassmorphism, responsive grid), Vanilla JavaScript ES6+
- **AI Forecasting Engine**: Predictive demand velocity & monsoon outbreak surge simulation model
- **Governance**: Immutable sequential audit logging, multi-factor non-profit verification desk, and CPCB Form IV biomedical waste tracking

---

## Key Features

1. **Platform Command Center (`/dashboard`)**:
   - Real-time telemetry: Tracked batches, active physical units, near-expiry risk counts, active in-transit transfers, verified NGO partners, and CO₂e environmental impact.
   - Interactive AI Surplus Forecaster Simulator with dynamic sliders (stock volume, daily dispensing velocity, seasonal outbreak surge multiplier).
   - Dynamic shelf-life risk tier distribution bars and weekly distribution velocity chart.

2. **Batch-Level Inventory Desk (`/inventory`)**:
   - Real-time text search and multi-column filtering (Category & Shelf-life risk status).
   - Dynamic countdown tags (*19 days left*, *Critical*, *Safe*).
   - One-click actions: "Match Now", "Eco-Dispose", "Flag Surplus".
   - Direct CSV export utility (`/api/export/inventory`).
   - Batch intake modal with custom storage specs and batch number validation.

3. **AI Smart Matching Engine (`/matching`)**:
   - Multi-factor algorithmic scoring: Clinical Urgency (40%), Route Distance & Proximity (30%), Quantity Compatibility (20%), and NGO Verification (10%).
   - Dynamic source batch selector for easy allocation switching.
   - One-click "Offer Medicine" modal with custom quantity configuration.

4. **Traceable Transfers Pipeline (`/transfers`)**:
   - Visual 6-stage custody stepper (`Pending` → `Accepted` → `Scheduled` → `In Transit` → `Verified` → `Completed`).
   - Digital Consignment Note / QR Waybill manifest preview modal.
   - Real-time stage advancement with automatic immutable audit logging.

5. **Responsible Eco-Disposal Portal (`/disposal`)**:
   - Environmental hazard prevention metrics (waste diverted, CO₂ equivalent neutralized).
   - 6-step statutory biomedical waste disposal pipeline.
   - CPCB Form IV destruction manifest generator.
   - Certified partner assignment (e.g. Meerut Biomedical Waste Management Ltd).

6. **Governance & Audit Center (`/admin`)**:
   - Organization Verification Desk: Instant one-click approve/revoke toggle with real-time audit generation.
   - Automated Anomaly Surveillance (intake volume spikes, rapid re-allocation attempts).
   - Emergency SOS Triage for regional crisis requests.
   - Searchable, filterable cryptographic audit log explorer.

7. **Regional Emergency SOS Protocol**:
   - Accessible from any screen via the top navigation bar (`🚨 SOS Broadcast`).
   - Instant network-wide broadcast for critical outbreaks and disaster relief camps.

---

## Run Locally

```bash
# 1. Clone / Navigate to directory
cd dawai_setu

# 2. Setup virtual environment (Optional)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Run application
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## Complete REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/stats` | `GET` | Dynamic platform KPI telemetry & impact metrics |
| `/api/medicines` | `GET`, `POST` | Retrieve inventory or register a new batch |
| `/api/medicines/<id>/action` | `POST` | Quick batch action (`mark_surplus`, `route_disposal`) |
| `/api/matching/recommendations` | `GET` | Multi-factor AI matching scores for beneficiaries |
| `/api/transfers` | `POST` | Initiate a new medicine transfer consignment |
| `/api/transfer/<id>/status` | `POST` | Advance transfer lifecycle stage |
| `/api/disposal` | `POST` | Generate a certified CPCB disposal manifest |
| `/api/org/<id>/verify` | `POST` | Toggle NGO partner verification status |
| `/api/emergency` | `POST` | Broadcast urgent clinical medicine request |
| `/api/emergency/<id>/resolve` | `POST` | Resolve open emergency call |
| `/api/ai/forecast` | `POST` | Interactive AI demand velocity simulation |
| `/api/audit` | `GET` | Retrieve and search immutable platform audit logs |
| `/api/export/inventory` | `GET` | Export live inventory data to CSV |

---

## Hackathon Demonstration Flow

1. **Home (`/`)**: Explore the mission, interactive medicine lifecycle visual ring, and ecosystem impact.
2. **Dashboard (`/dashboard`)**: Observe live metrics and interact with the AI Surplus Simulation sliders.
3. **Inventory (`/inventory`)**: Filter batches, search stock, export CSV, or add a new batch with "+ Add Medicine Batch".
4. **Smart Matching (`/matching`)**: Review AI match scores and click "Offer Medicine" to dispatch stock to an NGO.
5. **Transfers (`/transfers`)**: Open the QR Waybill modal and advance the transfer through its 6-stage lifecycle.
6. **Eco-Disposal (`/disposal`)**: Review statutory compliance guidelines and generate a Form IV manifest for expired batches.
7. **Governance (`/admin`)**: Approve pending NGO verifications, triage active emergency SOS calls, and search the audit trail.
