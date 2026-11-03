"""The options the admin page can change. Each can still start from its environment variable; a saved value wins."""

from engine import DEFAULT_REPO, DEFAULT_VOICES
from settings import Setting

SETTINGS = [
    Setting("update_check_hours", "Check for updates every (hours)", "float", 6.0, "TTSPIPER_UPDATE_CHECK_HOURS", 0, 720,
            help="0 = only when you press Check now"),
    Setting("max_inflight", "Calls allowed to wait for the model", "int", 0, "TTSPIPER_MAX_INFLIGHT", 0, 10000,
            help="Per replica; more get 429. 0 = 4"),
    Setting("voices", "Voices served", "text", DEFAULT_VOICES, "TTSPIPER_VOICES", blank=False,
            help="Comma separated Piper voice names, such as en_US-lessac-medium. The first is the default. Each downloads on first use"),
    Setting("model", "Voices repository", "text", DEFAULT_REPO, "TTSPIPER_MODEL", restart=True, blank=False,
            help="A Hugging Face repository laid out like rhasspy/piper-voices"),
    Setting("warm", "Load the default voice at start", "bool", True, "TTSPIPER_WARM", restart=True),
]
