"""Mini web UI for mobile SoundTouch controls."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from waitress import serve

from soundtouchbose.services import Services


def create_web_app(services: Services) -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/devices")
    def devices():
        cache = services.preset_manager.load_cache()
        payload = []
        for device in services.device_manager.all_devices():
            payload.append({
                **device.to_dict(),
                "presets": cache.get(device.ip_address, {}),
            })
        return jsonify(payload)

    @app.get("/api/zones")
    def zones():
        return jsonify(services.zone_manager.load_groups())

    @app.post("/api/devices/<path:device_ip>/preset/<int:preset_number>")
    def trigger_preset(device_ip: str, preset_number: int):
        client = services.client_factory(device_ip)
        client.send_key(f"PRESET_{preset_number}", "press")
        client.send_key(f"PRESET_{preset_number}", "release")
        return jsonify({"status": "ok"})

    @app.post("/api/devices/<path:device_ip>/volume")
    def set_volume(device_ip: str):
        payload = request.get_json(force=True)
        services.client_factory(device_ip).set_volume(int(payload["volume"]))
        return jsonify({"status": "ok"})

    @app.post("/api/devices/<path:device_ip>/playpause")
    def play_pause(device_ip: str):
        client = services.client_factory(device_ip)
        client.send_key("PLAY_PAUSE", "press")
        client.send_key("PLAY_PAUSE", "release")
        return jsonify({"status": "ok"})

    @app.post("/api/zones/<group_name>/activate")
    def activate_zone(group_name: str):
        for group in services.zone_manager.load_groups():
            if group.get("name") == group_name:
                services.zone_manager.create_zone(str(group.get("master_ip")), list(group.get("members", [])))
                return jsonify({"status": "ok"})
        return jsonify({"status": "missing"}), 404

    return app


def run_waitress(app: Flask, port: int, host: str = "0.0.0.0") -> None:
    serve(app, host=host, port=port)
