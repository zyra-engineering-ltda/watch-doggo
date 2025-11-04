import json
from pathlib import Path

from pywebpush import webpush, WebPushException

SUBSCRIPTIONS_FILE = Path("subscriptions.json")

def load_subscriptions():
    if SUBSCRIPTIONS_FILE.exists():
        return json.loads(SUBSCRIPTIONS_FILE.read_text())
    return []

def save_subscriptions(subs):
    SUBSCRIPTIONS_FILE.write_text(json.dumps(subs, indent=2))

def add_subscription(sub):
    subs = load_subscriptions()
    # avoid duplicates
    if not any(s["endpoint"] == sub["endpoint"] for s in subs):
        subs.append(sub)
        save_subscriptions(subs)

def send_notification_to_all(payload, vapid_private_key, vapid_claims):
    subs = load_subscriptions()
    for sub in subs:
        try:
            webpush(
                subscription_info=sub,
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
        except WebPushException as ex:
            print("Web push failed for", sub["endpoint"], ex)
