import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message

app = Flask(__name__)

# ------------------------
# Database configuration
# ------------------------
db_path = os.environ.get('DB_PATH')
if db_path:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
else:
    db_path = os.path.join(os.getcwd(), "data", "messages.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ------------------------
# Email (Gmail SMTP config)
# ------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "fm0119678@gmail.com"
app.config['MAIL_PASSWORD'] = "jmzmwqcvyhigofmn"   # ← no spaces
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']


db = SQLAlchemy(app)
mail = Mail(app)

# ------------------------
# Database model
# ------------------------
class MessageModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)

with app.app_context():
    db.create_all()

# ------------------------
# Routes
# ------------------------
@app.route("/contact", methods=["POST"])
def contact():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    message_text = data.get("message")

    if not name or not email or not message_text:
        return jsonify({"error": "Missing fields"}), 400

    # Save to DB
    new_message = MessageModel(name=name, email=email, message=message_text)
    db.session.add(new_message)
    db.session.commit()

    print(f"New message saved from {name} ({email}): {message_text}")

    # Try sending emails if credentials exist
    if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
        try:
            # 1) Notification to YOU (admin)
            admin_msg = Message(
                subject=f"New Contact Form Message from {name}",
                recipients=[app.config['MAIL_USERNAME']],
                body=f"Name: {name}\nEmail: {email}\n\nMessage:\n{message_text}"
            )
            mail.send(admin_msg)

            # 2) Confirmation email to SENDER
            user_msg = Message(
                subject="We received your message!",
                recipients=[email],
                body=f"Hi {name},\n\nThanks for contacting us! We received your message:\n\n{message_text}\n\nWe will reply soon.\n\n- Team"
            )
            mail.send(user_msg)

            email_status = "sent"
        except Exception as e:
            print("Email sending error:", e)
            email_status = f"failed: {e}"
            return jsonify({
                "status": "success",
                "message": "Saved but email sending failed (see logs).",
                "email_error": str(e)
            }), 200
    else:
        email_status = "skipped - MAIL_USERNAME/MAIL_PASSWORD not set"

    return jsonify({
        "status": "success",
        "message": "Your message has been received and confirmation email sent!",
        "email_status": email_status
    }), 200


@app.route("/messages", methods=["GET"])
def get_messages():
    messages = MessageModel.query.all()
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "name": msg.name,
            "email": msg.email,
            "message": msg.message
        })
    return jsonify(result), 200

# ------------------------
# Run app
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
