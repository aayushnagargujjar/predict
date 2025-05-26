from prophet import Prophet
import pandas as pd
from firebase_init import init_firebase

db = init_firebase()

def run_daily_forecast():
    uid = "OaFGRFLxEVfyhSq7tCZ3W2y823l2"
    user_doc = db.collection("users").document(uid).get()
    if not user_doc.exists:
        print("User not found")
        return

    co2_data = user_doc.to_dict().get("co2_data", [])
    if len(co2_data) < 3:
        print("Not enough CO₂ data")
        return

    df = pd.DataFrame(co2_data).rename(columns={"date": "ds", "value": "y"})
    df["ds"] = pd.to_datetime(df["ds"])

    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=3)
    forecast = model.predict(future)[["ds", "yhat"]].tail(3)

    result = [{"date": str(row["ds"].date()), "co2_pred": round(row["yhat"], 2)} for _, row in forecast.iterrows()]
    db.collection("users").document(uid).update({"user_forecast": result})
    print("Forecast updated:", result)

if __name__ == "__main__":
    run_daily_forecast()
