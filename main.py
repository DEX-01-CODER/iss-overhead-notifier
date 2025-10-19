import requests
from datetime import datetime, timezone
import smtplib
import time
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env next to your script

my_email = os.getenv("EMAIL_USER")
password = os.getenv("EMAIL_PASS")
to_email = os.getenv("TO_EMAIL")

MY_LAT = float(os.getenv("MY_LAT", 0))
MY_LONG = float(os.getenv("MY_LONG", 0))

HTTP_TIMEOUT = 10
HTTP_HEADERS = {"User-Agent": "ISS-Notifier/1.0 (+https://github.com/DEX-01-CODER)"}

def is_iss_overhead():
    try:
        response = requests.get(url="http://api.open-notify.org/iss-now.json", timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return False

    iss_latitude = float(data["iss_position"]["latitude"])
    iss_longitude = float(data["iss_position"]["longitude"])

    # Your position is within +5 or -5 degrees of the ISS position.
    if (MY_LAT - 5) <= iss_latitude <= (MY_LAT + 5) and (MY_LONG - 5) <= iss_longitude <= (MY_LONG + 5):
        return True
    return False

def is_night():
    params = {"lat": MY_LAT, "lng": MY_LONG, "formatted": 0}
    try:
        response = requests.get("https://api.sunrise-sunset.org/json", params=params, timeout=HTTP_TIMEOUT, headers=HTTP_HEADERS)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return False

    # Parse full ISO timestamps (UTC)
    try:
        sunrise_utc = datetime.fromisoformat(data["results"]["sunrise"]).astimezone(timezone.utc)
        sunset_utc  = datetime.fromisoformat(data["results"]["sunset"]).astimezone(timezone.utc)
    except Exception:
        # Fallback to hour-only if parsing fails
        sunrise_utc = None
        sunset_utc = None

    now_utc = datetime.now(timezone.utc)

    if sunrise_utc and sunset_utc:
        return now_utc >= sunset_utc or now_utc <= sunrise_utc

    # Fallback using hour comparison if needed
    try:
        sunrise_hour = int(data["results"]["sunrise"].split("T")[1].split(":")[0])
        sunset_hour = int(data["results"]["sunset"].split("T")[1].split(":")[0])
        now_hour = now_utc.hour
        return now_hour >= sunset_hour or now_hour <= sunrise_hour
    except Exception:
        return False

while True:
    if is_iss_overhead() and is_night():
        try:
            with smtplib.SMTP("smtp.gmail.com") as connection:
                connection.starttls()
                connection.login(user=my_email, password=password)
                msg = (
                    f"From: {my_email}\r\n"
                    f"To: {to_email}\r\n"
                    f"Subject: Look up 👆\r\n\r\n"
                    f"The ISS is above you in the sky."
                )
                connection.sendmail(from_addr=my_email, to_addrs=to_email, msg=msg)
        except Exception:
            pass
    time.sleep(60)
