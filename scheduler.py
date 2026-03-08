"""scheduler.py — Daily automated run. Usage: python scheduler.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, verify_user
from pipeline    import run_pipeline
from config.settings import SCHEDULE_TIME

def run_daily():
    print("🤖 AI Job Agent — Daily Run")
    init_db()
    username = os.getenv("AGENT_USERNAME", "")
    password = os.getenv("AGENT_PASSWORD", "")
    if not username or not password:
        print("Set AGENT_USERNAME and AGENT_PASSWORD env vars.")
        return
    user = verify_user(username, password)
    if not user:
        print("Invalid credentials."); return
    resume_path = os.getenv("RESUME_PATH", "data/my_resume.txt")
    try:
        with open(resume_path, encoding="utf-8") as f:
            resume_text = f.read()
    except FileNotFoundError:
        print(f"Resume not found: {resume_path}"); return
    result = run_pipeline(user_id=user["id"], resume_text=resume_text)
    if result["success"]:
        print(f"✅ Done: {result['total']} jobs, {result['strong']} strong matches")
    else:
        print(f"❌ Failed: {result.get('error')}")

if __name__ == "__main__":
    import schedule, time
    run_daily()  # run immediately on start
    schedule.every().day.at(SCHEDULE_TIME).do(run_daily)
    print(f"⏰ Scheduled daily at {SCHEDULE_TIME}. Ctrl+C to stop.")
    while True:
        schedule.run_pending(); time.sleep(60)
