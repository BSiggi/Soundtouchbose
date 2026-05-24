"""Optional Home Assistant bridge."""

from __future__ import annotations

from functools import wraps

from flask import Flask, jsonify, request
from waitress import serve

from soundtouchbose.services import Services


def create_homeassistant_app(services: Services) -> Flask:
    app = Flask(__name__)

    def requires_token(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            token = services.config_store.load_settings().get("home_assistant_token", "change-me")
            header = request.headers.get("Authorization", "")
            supplied = header.removeprefix("Bearer ") if header.startswith("Bearer ") else request.headers.get("X-Token", "")
            if supplied != token:
                return jsonify({"error": "unauthorized"}), 401
            return view(*args, **kwargs)

        return wrapped

    def find_device(name: str):
        for device in services.device_manager.all_devices():
            if device.name == name or device.ip_address == name:
                return device
        return None

    @app.get("/api/devices")
    @requires_token
    def devices():
        return jsonify([device.to_dict() for device in services.device_manager.all_devices()])

    @app.post("/api/devices/<path:name>/preset/<int:preset_number>")
    @requires_token
    def preset(name: str, preset_number: int):
        device = find_device(name)
        if not device:
            return jsonify({"error": "not_found"}), 404
        client = services.client_factory(device.ip_address)
        client.send_key(f"PRESET_{preset_number}", "press")
        client.send_key(f"PRESET_{preset_number}", "release")
        return jsonify({"status": "ok"})

    @app.post("/api/devices/<path:name>/volume")
    @requires_token
    def volume(name: str):
        device = find_device(name)
        if not device:
            return jsonify({"error": "not_found"}), 404
        services.client_factory(device.ip_address).set_volume(int(request.get_json(force=True)["volume"]))
        return jsonify({"status": "ok"})

    @app.post("/api/devices/<path:name>/power")
    @requires_token
    def power(name: str):
        device = find_device(name)
        if not device:
            return jsonify({"error": "not_found"}), 404
        services.client_factory(device.ip_address).power(str(request.get_json(force=True)["state"]))
        return jsonify({"status": "ok"})

    return app


def run_waitress(app: Flask, port: int, host: str = "127.0.0.1") -> None:
    serve(app, host=host, port=port)
