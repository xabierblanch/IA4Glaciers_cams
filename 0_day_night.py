from astral.sun import sun
from astral import LocationInfo
from datetime import datetime, timezone
import pytz

def is_day_or_night():
    LATITUDE = -50.474164647981034
    LONGITUDE = -73.0354106241449
    
    argentina_tz = pytz.timezone('America/Argentina/Ushuaia')
    location = LocationInfo(name="Calafate", latitude=LATITUDE, longitude=LONGITUDE)
    
    now = datetime.now(argentina_tz)
    
    s = sun(location.observer, date=now.date(), tzinfo=argentina_tz)
    sunrise = s["sunrise"]
    sunset = s["sunset"]
    
    print(sunrise)
    print(sunset)
    print(now)
    
    if sunrise.time() <= now.time() < sunset.time():
        return "day"
    else:
        return "night"

if __name__ == "__main__":
    print(is_day_or_night())