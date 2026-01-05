from datetime import datetime

def format_datetime(dt_str):
    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    return dt.strftime("%d %b %Y, %H:%M")