import time
import sqlite3
from api_interface import get_course_info
from notifier import send_email

DB = "subscriptions.db"

def check_subscriptions():
    """Check all subscriptions in the database once, handle alerts with DB state."""
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, email, crn, notified FROM subscriptions")
    subs = c.fetchall()

    for sub_id, email, crn, notified in subs:
        try:
            info = get_course_info(crn)
            seats = info["seats_available"]

            print(
                f"[{time.strftime('%H:%M:%S')}] "
                f"CRN {crn} | Enrolled: {info['current_enrolled']} / {info['max_enrollment']} "
                f"| Seats available: {seats}"
            )

            # Case 1: Seat opens up → send alert if not already sent
            if seats > 0 and notified == 0:
                print(f"🚨 Seats open for CRN {crn}! Sending email to {email}")
                send_email(crn, email)
                c.execute("UPDATE subscriptions SET notified = 1 WHERE id = ?", (sub_id,))

            # Case 2: Seats close → reset notification flag
            elif seats == 0 and notified == 1:
                print(f"ℹ️ CRN {crn} seats filled again. Resetting alert for {email}")
                c.execute("UPDATE subscriptions SET notified = 0 WHERE id = ?", (sub_id,))

        except Exception as e:
            print(f"❌ Error checking {crn}: {e}")

    conn.commit()
    conn.close()

def track_loop(interval=60):
    """Run the subscription checker in a loop with polling interval."""
    print(f"📡 Tracking all subscriptions every {interval} seconds...")
    while True:
        check_subscriptions()
        time.sleep(interval)

if __name__ == "__main__":
    # Example: poll every 60s
    track_loop(interval=60)