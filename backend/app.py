import os
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from sklearn.linear_model import LogisticRegression

app = Flask(__name__)
CORS(app)

# Dummy ML Surplus Risk Classification Model
# Features: [Days_to_Expiry, Current_Stock_Qty, Historical_Monthly_Consumption, Local_Demand_Index]
X_train = np.array([
    [120, 500, 450, 0.8], # Low Surplus Risk
    [45,  300, 50,  0.2], # High Surplus Risk
    [30,  1000, 200, 0.3], # High Surplus Risk
    [180, 200, 200, 0.9], # Low Surplus Risk
    [15,  150, 10,  0.1], # High Surplus Risk
    [90,  600, 550, 0.7]  # Medium Surplus Risk
])
# 0: Low Risk, 1: High Surplus Risk
y_train = np.array([0, 1, 1, 0, 1, 0])

model = LogisticRegression()
model.fit(X_train, y_train)

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "system": "DAWAI-SETU Core Engine", "version": "1.0.0"}), 200

@app.route('/api/v1/predict-surplus', methods=['POST'])
def predict_surplus():
    try:
        data = request.json
        days_to_expiry = float(data.get('days_to_expiry'))
        current_stock = float(data.get('quantity'))
        historical_consumption = float(data.get('historical_consumption', 100))
        demand_index = float(data.get('demand_index', 0.5))

        features = np.array([[days_to_expiry, current_stock, historical_consumption, demand_index]])
        risk_prob = model.predict_proba(features)[0][1]
        
        predicted_demand = int(historical_consumption * (days_to_expiry / 30.0) * demand_index)
        predicted_surplus = max(0, int(current_stock - predicted_demand))
        
        risk_level = "High Risk" if risk_prob > 0.6 else ("Medium Risk" if risk_prob > 0.3 else "Low Risk")
        recommendation = "Redistribute immediately via DAWAI-SETU Smart Match" if risk_prob > 0.5 else "Retain in inventory for local consumption"

        return jsonify({
            "success": True,
            "prediction": {
                "risk_score": round(float(risk_prob * 100), 2),
                "risk_level": risk_level,
                "predicted_demand": predicted_demand,
                "predicted_surplus": predicted_surplus,
                "recommended_action": recommendation
            }
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/api/v1/match', methods=['POST'])
def smart_match():
    data = request.json
    medicine_name = data.get("medicine_name")
    quantity = data.get("quantity")
    
    # Heuristic score calculation
    mock_organizations = [
        {"id": 101, "name": "ABC Healthcare NGO", "distance_km": 12.4, "demand_qty": 200, "eligibility": "Verified"},
        {"id": 102, "name": "Red Cross District Clinic", "distance_km": 28.1, "demand_qty": 500, "eligibility": "Verified"},
        {"id": 103, "name": "Community Care Center", "distance_km": 5.2, "demand_qty": 150, "eligibility": "Verified"}
    ]
    
    matches = []
    for org in mock_organizations:
        dist_score = max(0, 100 - (org["distance_km"] * 2))
        qty_score = min(100, (org["demand_qty"] / quantity) * 100)
        match_score = round((dist_score * 0.4) + (qty_score * 0.6), 1)
        
        matches.append({
            "org_id": org["id"],
            "org_name": org["name"],
            "distance_km": org["distance_km"],
            "requested_qty": org["demand_qty"],
            "match_score": match_score
        })
        
    matches = sorted(matches, key=lambda x: x['match_score'], reverse=True)
    return jsonify({"success": True, "matches": matches}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)