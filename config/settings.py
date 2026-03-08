import os

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL    = os.getenv("GEMINI_MODEL",   "gemini-1.5-flash")
MAX_TOKENS      = 2048
RESUME_PATH     = "data/my_resume.txt"
RESUME_OUT_DIR  = "outputs/tailored_resumes"
COVER_OUT_DIR   = "outputs/cover_letters"
KEYWORDS = [
    "machine learning engineer", "ML engineer", "NLP engineer",
    "data scientist", "data analyst", "python developer",
    "AI engineer", "software engineer", "flutter developer",
]
LOCATIONS       = ["remote", "india", "bangalore", "hyderabad", "mumbai"]
TWILIO_SID      = os.getenv("TWILIO_SID",     "")
TWILIO_TOKEN    = os.getenv("TWILIO_TOKEN",    "")
TWILIO_FROM     = os.getenv("TWILIO_FROM",     "whatsapp:+14155238886")
WHATSAPP_TO     = os.getenv("WHATSAPP_TO",     "")
CALLMEBOT_PHONE = os.getenv("CALLMEBOT_PHONE", "")
CALLMEBOT_KEY   = os.getenv("CALLMEBOT_KEY",   "")
SCHEDULE_TIME   = "08:00"
APP_TITLE       = "AI Job Agent v4"
APP_ICON        = "🤖"
