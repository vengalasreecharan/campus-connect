# Campus Connect backend

Flask API backed by the Supabase tables in `schema.sql`. Authentication and authorization are deliberately not implemented.

## Setup

1. Apply `schema.sql` in the Supabase SQL editor if the tables do not already exist.
2. Ensure `.env` defines `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`.
3. Run `./venv/bin/python app.py`.

## API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/events` | Browse events; optional `?status=open`. |
| GET | `/api/events/:id` | Retrieve event details. |
| POST | `/api/registrations` | Create a registration. Returns `201` or `409`. |
| GET | `/api/me/registrations?user_id=:uuid` | List one user's registrations. `X-User-Id` also works. |
| GET | `/api/events/:id/registrations` | List attendees; public until authorization is added. |

Create a registration with:

```json
{"event_id": "event-uuid", "user_id": "user-uuid"}
```

The database unique constraint on `(user_id, event_id)` prevents duplicate registrations, including concurrent requests.
