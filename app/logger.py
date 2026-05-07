import os
import psutil

LOG_FILE = os.path.join(os.getcwd(), "log.txt")

def log_message(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def log_mem(label):
    proc = psutil.Process(os.getpid())
    rss = proc.memory_info().rss / 1024 / 1024
    log_message(f"🧠 [{label}] Memory: {rss:.0f} MB")
