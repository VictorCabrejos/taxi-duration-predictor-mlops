"""Small API-only consumer: no tracker access, selection or heuristic predictions."""

import os

import requests
import streamlit as st

from taxi_duration_predictor.presentation import request_prediction


def main():
    st.set_page_config(page_title="Taxi lifecycle reference", page_icon="🚕", layout="wide")
    st.title("Taxi duration — attributable prediction")
    st.caption(
        "Educational reference. The owned synthetic fixture does not establish NYC accuracy. "
        "Every result below belongs to the exact model run returned by the prediction API."
    )
    st.info("Confidence is NOT_AVAILABLE: this reference has no calibrated confidence estimate.")
    with st.form("prediction"):
        pickup, dropoff = st.columns(2)
        with pickup:
            pickup_latitude = st.number_input("Pickup latitude", 40.5, 40.9, 40.7, format="%.5f")
            pickup_longitude = st.number_input(
                "Pickup longitude", -74.3, -73.7, -74.0, format="%.5f"
            )
        with dropoff:
            dropoff_latitude = st.number_input("Dropoff latitude", 40.5, 40.9, 40.8, format="%.5f")
            dropoff_longitude = st.number_input(
                "Dropoff longitude", -74.3, -73.7, -73.9, format="%.5f"
            )
        passengers = st.number_input("Passengers", 1, 6, 1)
        vendor = st.selectbox("Vendor ID", [1, 2])
        timestamp = st.text_input("Pickup time (ISO 8601)", "2026-01-01T08:00:00-05:00")
        submitted = st.form_submit_button("Request prediction")
    if not submitted:
        return
    payload = {
        "pickup_latitude": pickup_latitude,
        "pickup_longitude": pickup_longitude,
        "dropoff_latitude": dropoff_latitude,
        "dropoff_longitude": dropoff_longitude,
        "passenger_count": passengers,
        "vendor_id": vendor,
        "pickup_datetime": timestamp,
    }
    try:
        view = request_prediction(
            requests.post, os.getenv("API_BASE_URL", "http://127.0.0.1:8000"), payload
        )
    except requests.HTTPError as error:
        status = error.response.status_code if error.response is not None else "unknown"
        st.error(
            f"Prediction unavailable (HTTP {status}). Check inputs and model readiness. No estimate was substituted."
        )
        return
    except (requests.RequestException, ValueError, TypeError):
        # Do not expose a configured URL/credential or response internals in an error.
        st.error(
            "Prediction unavailable or inconsistent API evidence. No estimate was substituted."
        )
        return
    duration, distance, confidence = st.columns(3)
    duration.metric("Predicted duration", view["duration"])
    distance.metric("Trip distance", view["distance"])
    confidence.metric("Confidence", view["confidence"])
    st.subheader("Evidence for this prediction")
    st.text(f"Exact run: {view['run_id']}")
    st.caption(
        "RMSE/MAE/R² describe the returned run's validation cohort, not this trip's confidence."
    )
    st.json(view["model"])
    with st.expander("Exact features and response"):
        st.json(view["response"])


if __name__ == "__main__":
    main()
