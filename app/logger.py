import os

LOG_FILE = os.path.join(os.getcwd(), "log.txt")

def log_message(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
