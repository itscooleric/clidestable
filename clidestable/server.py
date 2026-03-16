"""clidestable web server — dashboard + API + ttyd proxy."""

from __future__ import annotations

import atexit
import logging
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request

from .stall import StallManager

logger = logging.getLogger("clidestable")


def create_app(log_dir: str = "/opt/stacks", base_port: int = 7701) -> Flask:
    """Create the Flask application."""
    # Templates may be alongside the package (dev) or one level up (Docker)
    for candidate in [
        Path(__file__).parent.parent / "templates",
        Path(__file__).parent / "templates",
        Path("/app/templates"),
    ]:
        if candidate.is_dir():
            template_dir = candidate
            break
    else:
        template_dir = Path(__file__).parent.parent / "templates"
    app = Flask("clidestable", template_folder=str(template_dir))

    manager = StallManager(log_dir=log_dir, base_port=base_port)
    atexit.register(manager.destroy_all)

    # -- Dashboard --

    @app.route("/")
    def dashboard():
        stalls = [s.to_dict() for s in manager.stalls.values()]
        return render_template("dashboard.html", stalls=stalls)

    # -- API --

    @app.route("/api/stalls", methods=["GET"])
    def api_list_stalls():
        return jsonify({
            "stalls": [s.to_dict() for s in manager.stalls.values()]
        })

    @app.route("/api/stalls", methods=["POST"])
    def api_create_stall():
        data = request.get_json(silent=True) or {}
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "name is required"}), 400
        if not name.isidentifier() and not all(c.isalnum() or c in "-_" for c in name):
            return jsonify({"error": "invalid name — use alphanumeric, dash, underscore"}), 400
        try:
            stall = manager.create(name)
            return jsonify({"ok": True, "stall": stall.to_dict()}), 201
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 409
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/stalls/<name>", methods=["DELETE"])
    def api_destroy_stall(name: str):
        if manager.destroy(name):
            return jsonify({"ok": True})
        return jsonify({"error": "not found"}), 404

    @app.route("/api/stalls/<name>/log", methods=["GET"])
    def api_stall_log(name: str):
        lines = request.args.get("lines", 200, type=int)
        log_text = manager.get_log(name, lines=lines)
        return jsonify({"name": name, "log": log_text})

    # -- Stall terminal (proxy to ttyd) --

    @app.route("/stall/<name>/")
    def stall_view(name: str):
        stall = manager.get(name)
        if not stall or not stall.alive:
            return f"Stall '{name}' not found or not running.", 404
        # Render a page that iframes the ttyd port
        return render_template("stall.html", stall=stall.to_dict())

    # -- Split view (all stalls side by side) --

    @app.route("/view")
    def split_view():
        stalls = [s.to_dict() for s in manager.stalls.values() if s.alive]
        return render_template("split.html", stalls=stalls)

    # -- Log viewer --

    @app.route("/log/<name>")
    def log_view(name: str):
        log_text = manager.get_log(name, lines=500)
        return render_template("log.html", name=name, log=log_text)

    return app
