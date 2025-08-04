from flask import Flask
from routes import booking_bp

app = Flask(__name__)
app.secret_key = 'secret-key'
app.register_blueprint(booking_bp)

if __name__ == "__main__":
    app.run(debug=True)
