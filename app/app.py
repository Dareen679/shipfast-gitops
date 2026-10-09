"""ShipFast status-check API.

A tiny Flask service with two endpoints:
  GET /status  - basic service information (name, version, environment)
  GET /health  - lightweight health check used by Docker and Kubernetes probes
"""
import os
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)

SERVICE_NAME = "shipfast-status-api"
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")


@app.get("/status")
def status():
    return jsonify(
        service=SERVICE_NAME,
        status="ok",
        version=APP_VERSION,
        environment=os.getenv("APP_ENV", "development"),
        hostname=socket.gethostname(),  # shows which pod answered
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health")
def health():
    return jsonify(status="healthy"), 200


if __name__ == "__main__":
    # Local development only. In the container, gunicorn serves the app.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
