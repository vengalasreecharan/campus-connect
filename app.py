"""Campus Connect event API with no authentication or authorization."""

import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from postgrest import APIError
from supabase import Client, create_client

load_dotenv()


def create_app(supabase_client: Client | None = None) -> Flask:
    """Create the app; tests may pass a fake Supabase client."""
    app = Flask(__name__)
    if supabase_client is None:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be set in .env")
        supabase_client = create_client(url, key)
    app.config["SUPABASE_CLIENT"] = supabase_client

    def db() -> Client:
        return app.config["SUPABASE_CLIENT"]

    def error(message: str, status: int):
        return jsonify({"error": message}), status

    def first_or_404(rows: list[dict[str, Any]], resource: str):
        return rows[0] if rows else error(f"{resource} not found", 404)

    @app.get("/")
    def index():
        return jsonify({"service": "Campus Connect API", "status": "ok"})

    @app.get("/api/events")
    def list_events():
        try:
            query = db().table("events").select("*")
            if status := request.args.get("status"):
                query = query.eq("status", status)
            return jsonify(query.order("title").execute().data)
        except APIError as exc:
            return error(f"Unable to load events: {exc.message}", 502)

    @app.get("/api/events/<event_id>")
    def get_event(event_id: str):
        try:
            event = first_or_404(db().table("events").select("*").eq("id", event_id).execute().data, "Event")
            return event if isinstance(event, tuple) else jsonify(event)
        except APIError as exc:
            return error(f"Unable to load event: {exc.message}", 502)

    @app.post("/api/registrations")
    def create_registration():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return error("A JSON request body is required", 400)
        event_id, user_id = payload.get("event_id"), payload.get("user_id")
        if not event_id or not user_id:
            return error("event_id and user_id are required", 400)
        try:
            event = first_or_404(db().table("events").select("*").eq("id", event_id).execute().data, "Event")
            if isinstance(event, tuple):
                return event
            if event.get("status") and event["status"].lower() not in {"open", "active", "published"}:
                return error("Event is not open for registration", 409)
            if not db().table("users").select("id").eq("id", user_id).execute().data:
                return error("User not found", 404)
            duplicate = db().table("registrations").select("id").eq("event_id", event_id).eq("user_id", user_id).execute().data
            if duplicate:
                return error("User is already registered for this event", 409)
            count = db().table("registrations").select("id", count="exact").eq("event_id", event_id).execute().count or 0
            if event.get("capacity") is not None and count >= event["capacity"]:
                return error("Event capacity has been reached", 409)
            registration = db().table("registrations").insert({"event_id": event_id, "user_id": user_id}).execute().data[0]
            return jsonify(registration), 201
        except APIError as exc:
            if getattr(exc, "code", None) == "23505":
                return error("User is already registered for this event", 409)
            return error(f"Unable to create registration: {exc.message}", 502)

    @app.get("/api/me/registrations")
    def list_user_registrations():
        # `user_id` is a request value, not an authenticated identity.
        user_id = request.args.get("user_id") or request.headers.get("X-User-Id")
        if not user_id:
            return error("user_id query parameter or X-User-Id header is required", 400)
        try:
            registrations = db().table("registrations").select("*, events(*)").eq("user_id", user_id).order("created_at", desc=True).execute().data
            return jsonify(registrations)
        except APIError as exc:
            return error(f"Unable to load registrations: {exc.message}", 502)

    @app.get("/api/events/<event_id>/registrations")
    def list_event_registrations(event_id: str):
        """Public attendee list because authorization is intentionally omitted."""
        try:
            if not db().table("events").select("id").eq("id", event_id).execute().data:
                return error("Event not found", 404)
            attendees = db().table("registrations").select("id, event_id, user_id, created_at, users(id, email, role)").eq("event_id", event_id).order("created_at").execute().data
            return jsonify(attendees)
        except APIError as exc:
            return error(f"Unable to load attendees: {exc.message}", 502)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
