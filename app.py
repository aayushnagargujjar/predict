from flask import Flask, request, jsonify
from prophet import Prophet
import pandas as pd
import traceback
from firebase_init import init_firebase

app = Flask(__name__)
db = init_firebase()

@app.route('/predict', methods=['POST'])
def run_forecast():
    try:
        uid = request.json.get('uid', "OaFGRFLxEVfyhSq7tCZ3W2y823l2")  # default for testing
        if not uid:
            return jsonify({"error": "UID not provided"}), 400

        user_doc_ref = db.collection("users").document(uid)
        user_doc = user_doc_ref.get()
        if not user_doc.exists:
            return jsonify({"error": f"User '{uid}' not found"}), 404

        user_data = user_doc.to_dict()
        co2_data = user_data.get("co2_data", [])
        if len(co2_data) < 3:
            return jsonify({"error": "At least 3 CO₂ data points required"}), 403

        df_co2 = pd.DataFrame(co2_data).rename(columns={"date": "ds", "value": "y"})
        df_co2['ds'] = pd.to_datetime(df_co2['ds'])

        model_co2 = Prophet()
        model_co2.fit(df_co2)
        future_co2 = model_co2.make_future_dataframe(periods=3)
        forecast_co2 = model_co2.predict(future_co2)[['ds', 'yhat']].tail(3)

        co2_forecast = [{"date": str(row['ds'].date()), "co2_pred": round(row['yhat'], 2)}
                        for _, row in forecast_co2.iterrows()]

        # Water forecast (optional)
        water_data = user_data.get("water_data", [])
        water_forecast = []
        if len(water_data) >= 3:
            df_water = pd.DataFrame(water_data).rename(columns={"date": "ds", "value": "y"})
            df_water['ds'] = pd.to_datetime(df_water['ds'])
            model_water = Prophet()
            model_water.fit(df_water)
            future_water = model_water.make_future_dataframe(periods=3)
            forecast_water = model_water.predict(future_water)[['ds', 'yhat']].tail(3)
            water_forecast = [{"date": str(row['ds'].date()), "water_pred": round(row['yhat'], 2)}
                              for _, row in forecast_water.iterrows()]

        # Merge
        combined = []
        for c in co2_forecast:
            match = next((w for w in water_forecast if w['date'] == c['date']), None)
            combined.append({
                "date": c['date'],
                "co2_pred": c['co2_pred'],
                "water_pred": match['water_pred'] if match else 0.0
            })

        user_doc_ref.update({"user_forecast": combined})
        return jsonify({"message": "Forecast updated", "forecast": combined})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
