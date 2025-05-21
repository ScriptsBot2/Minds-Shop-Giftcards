import os
import json
from flask import Flask, render_template, request
import smtplib
from email.message import EmailMessage

app = Flask(__name__)


KEYS_FILE = "keys.json"
GIFTS_FILE = "keys1.json"


SENDER_EMAIL = "mindsshopdelivery@gmail.com"
SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USER = "8d8da0001@smtp-brevo.com"
SMTP_PASS = os.getenv("BREVO_SMTP_KEY")

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def send_email(to_email, discord_user, reward_key):
    msg = EmailMessage()
    msg["Subject"] = "Thanks for Redeeming Your Key!"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email
    msg.set_content(f"""
Hello {discord_user},

Thanks for supporting us!

Here is your unique reward key: {reward_key}
Enjoy!
""")
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.send_message(msg)

@app.route("/", methods=["GET", "POST"])
def redeem():
    message = ""
    if request.method == "POST":
        discord_user = request.form.get("discord_user", "").strip()
        discord_id = request.form.get("discord_id", "").strip()
        product_key = request.form.get("product_key", "").strip()
        email = request.form.get("email", "").strip()

        if not discord_user or not discord_id or not product_key or not email:
            message = "Please fill in all fields."
        else:
            keys = load_json(KEYS_FILE)
            gifts = load_json(GIFTS_FILE)

            if product_key not in keys.get("valid", []):
                message = "Invalid key."
            elif product_key in keys.get("used", []):
                message = "Key already used."
            else:
                keys["valid"].remove(product_key)
                keys.setdefault("used", []).append(product_key)

                reward_list = gifts.get("standard", []) or gifts.get("premium", [])
                if not reward_list:
                    message = "No reward keys left."
                else:
                    reward_key = reward_list.pop(0)
                    gifts.setdefault("given", []).append(reward_key)

                    save_json(KEYS_FILE, keys)
                    save_json(GIFTS_FILE, gifts)

                    try:
                        send_email(email, discord_user, reward_key)
                        message = f"Success! Reward key sent to {email}."
                    except Exception as e:
                        message = f"Error sending email: {e}"

    return render_template("index.html", message=message)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
