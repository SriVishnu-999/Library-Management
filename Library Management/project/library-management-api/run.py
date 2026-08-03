"""
Library Management REST API — WSGI Entry Point

Run locally:
    python run.py

Run with Gunicorn (production):
    gunicorn -w 4 -b 0.0.0.0:5000 run:app
"""

from app.app_factory import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
