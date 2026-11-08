import os
from app import create_app
from app.extensions import db

env_config = os.environ.get("FLASK_ENV", "development")
app = create_app(env_config)

if __name__ == "__main__":
    # Ensure tables exist on first startup
    with app.app_context():
        db.create_all()

    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")

    print("\n" + "=" * 60)
    print(" Group No1 — Global Lost & Found Management System")
    print(f" Running at: http://{host}:{port}")
    print(" Press CTRL+C to quit the server")
    print("=" * 60 + "\n")

    app.run(host=host, port=port, debug=debug)
