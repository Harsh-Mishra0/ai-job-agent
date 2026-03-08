"""whatsapp_alert.py — Free WhatsApp alerts via CallMeBot or Twilio."""
import urllib.request, urllib.parse, json, base64
from typing import List, Dict
from datetime import datetime


def send_whatsapp_alert(jobs: List[Dict], stats: Dict, user_name: str = "Job Hunter"):
    from config.settings import TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, WHATSAPP_TO, CALLMEBOT_PHONE, CALLMEBOT_KEY
    msg = _build_message(jobs, stats, user_name)
    if TWILIO_SID and WHATSAPP_TO:
        if _send_twilio(msg, TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, WHATSAPP_TO): return
    if CALLMEBOT_PHONE and CALLMEBOT_KEY:
        if _send_callmebot(msg, CALLMEBOT_PHONE, CALLMEBOT_KEY): return
    print("\n📱 WHATSAPP ALERT (not configured):\n" + msg + "\n")


def _build_message(jobs: List[Dict], stats: Dict, user_name: str) -> str:
    lines = [
        f"🤖 *AI Job Agent Daily Update*",
        f"👋 Hey {user_name}!",
        f"",
        f"📊 *Today's Run*",
        f"• Jobs found: {stats.get('total',0)}",
        f"• Strong matches: {stats.get('strong',0)}",
        f"• New jobs: {stats.get('new',0)}",
        f"",
        f"🏆 *Top {min(5,len(jobs))} Matches*",
    ]
    icons = {"ML":"🤖","Data":"📊","Entry-Level":"🌱"}
    for i, job in enumerate(jobs[:5], 1):
        lines += [
            f"",
            f"*{i}. {job.get('title','')}* — {job.get('company','')}",
            f"{icons.get(job.get('role_type',''),'💼')} {job.get('match_score',0):.0f}% | 📍 {job.get('location','')[:25]}",
        ]
    lines.append(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    return "\n".join(lines)


def _send_twilio(msg: str, sid: str, token: str, from_: str, to: str) -> bool:
    try:
        url  = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
        data = urllib.parse.urlencode({"From": from_, "To": to, "Body": msg}).encode()
        cred = base64.b64encode(f"{sid}:{token}".encode()).decode()
        req  = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Basic {cred}")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()).get("sid") is not None
    except Exception as e:
        print(f"   Twilio error: {e}"); return False


def _send_callmebot(msg: str, phone: str, key: str) -> bool:
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={urllib.parse.quote(msg)}&apikey={key}"
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"JobAgent/1.0"}), timeout=10) as r:
            body = r.read().decode()
            if "Message queued" in body or "200" in body:
                print(f"   ✓ WhatsApp sent via CallMeBot"); return True
    except Exception as e:
        print(f"   CallMeBot error: {e}")
    return False
