"""email_parser/gmail_parser.py — Gmail recruiter email classifier."""
import re, base64
from pathlib import Path
from typing import List, Dict

SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = Path("email_parser/token.json")
CREDS_PATH = Path("email_parser/credentials.json")

PATTERNS = {
    "INTERVIEW_INVITE": [r"invite you.{0,20}interview", r"schedule.{0,20}interview",
                         r"next (step|round)", r"move forward with you",
                         r"interview (slot|availability)", r"technical (screen|round)"],
    "OFFER":            [r"pleased to offer", r"offer of employment", r"job offer",
                         r"would like to offer", r"offer letter"],
    "REJECTION":        [r"decided.{0,20}move forward with other", r"other candidates",
                         r"not (moving|proceeding) forward", r"position has been filled",
                         r"regret to inform", r"not selected", r"unfortunately.{0,20}not"],
    "INFO_REQUEST":     [r"could you.{0,20}(share|send|provide)", r"(attach|upload|send) your",
                         r"availability for", r"complete.{0,20}(form|assessment|test)"],
    "FOLLOW_UP":        [r"following up", r"checking in", r"touch base", r"status of your application"],
}


def classify_email(subject: str, body: str) -> str:
    text = f"{subject} {body}".lower()
    for cat in ["OFFER", "INTERVIEW_INVITE", "INFO_REQUEST", "FOLLOW_UP", "REJECTION"]:
        if any(re.search(p, text) for p in PATTERNS[cat]):
            return cat
    return "UNKNOWN"


def get_email_stats(emails: List[Dict]) -> Dict:
    cats = {}
    for e in emails:
        c = e.get("category", "UNKNOWN")
        cats[c] = cats.get(c, 0) + 1
    return {
        "total":         len(emails),
        "interviews":    cats.get("INTERVIEW_INVITE", 0),
        "offers":        cats.get("OFFER", 0),
        "rejections":    cats.get("REJECTION", 0),
        "info_requests": cats.get("INFO_REQUEST", 0),
        "action_needed": sum(1 for e in emails if e.get("action_needed")),
        "by_category":   cats,
    }


class GmailParser:
    def __init__(self):
        self._service = None

    def authenticate(self) -> bool:
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            print("   Install: pip install google-api-python-client google-auth-oauthlib")
            return False

        creds = None
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not CREDS_PATH.exists():
                    print(f"   credentials.json not found at {CREDS_PATH}")
                    return False
                flow  = InstalledAppFlow.from_client_secrets_file(str(CREDS_PATH), SCOPES)
                creds = flow.run_local_server(port=0)
            TOKEN_PATH.write_text(creds.to_json())

        from googleapiclient.discovery import build
        self._service = build("gmail", "v1", credentials=creds)
        return True

    def fetch_recruiter_emails(self, max_results: int = 50) -> List[Dict]:
        if not self._service:
            if not self.authenticate():
                return self.demo_emails()
        query = ('subject:(application OR interview OR offer OR hiring OR opportunity OR '
                 '"next steps" OR "moving forward") newer_than:90d')
        try:
            res  = self._service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            msgs = res.get("messages", [])
            return [self._process(m["id"]) for m in msgs]
        except Exception as e:
            print(f"   Gmail error: {e}")
            return self.demo_emails()

    def _process(self, msg_id: str) -> Dict:
        try:
            msg     = self._service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            subject = headers.get("Subject", "")
            sender  = headers.get("From", "")
            date    = headers.get("Date", "")
            body    = self._body(msg["payload"])
            cat     = classify_email(subject, body)
            m       = re.search(r"@([\w\-]+)\.", sender)
            company = m.group(1).title() if m and m.group(1).lower() not in ("gmail","yahoo","outlook") else ""
            return {
                "id": msg_id, "subject": subject, "sender": sender, "date": date,
                "body_preview": body[:300], "category": cat, "company": company,
                "action_needed": cat in ("INTERVIEW_INVITE", "INFO_REQUEST", "OFFER"),
            }
        except Exception as e:
            return {"id": msg_id, "category": "UNKNOWN", "error": str(e), "action_needed": False}

    def _body(self, payload: Dict) -> str:
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data: return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
        return ""

    def demo_emails(self) -> List[Dict]:
        return [
            {"id":"d1","subject":"Interview Invite — ML Engineer at Cohere","sender":"talent@cohere.ai",
             "date":"2025-01-14","body_preview":"We'd like to invite you for a technical interview for the ML Engineer position.",
             "category":"INTERVIEW_INVITE","company":"Cohere","action_needed":True},
            {"id":"d2","subject":"Application Update — Scale AI","sender":"noreply@scaleai.com",
             "date":"2025-01-13","body_preview":"After careful consideration we have decided to move forward with other candidates.",
             "category":"REJECTION","company":"Scale AI","action_needed":False},
            {"id":"d3","subject":"Next Steps — Data Scientist","sender":"hr@notion.so",
             "date":"2025-01-15","body_preview":"Could you please complete the take-home assessment? You have 72 hours.",
             "category":"INFO_REQUEST","company":"Notion","action_needed":True},
            {"id":"d4","subject":"Job Offer — Junior ML Engineer","sender":"offers@startup.io",
             "date":"2025-01-16","body_preview":"We are pleased to offer you the position. Please respond by Friday.",
             "category":"OFFER","company":"Startup","action_needed":True},
        ]
