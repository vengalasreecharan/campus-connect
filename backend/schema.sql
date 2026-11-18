-- Campus Connect schema matching database.png.
create table if not exists public.users (
    id uuid primary key,
    email text not null unique,
    role text not null
);

create table if not exists public.events (
    id uuid primary key default gen_random_uuid(),
    organizer_id uuid not null references public.users(id),
    title text not null,
    capacity integer not null check (capacity >= 0),
    status text not null
);

create table if not exists public.registrations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id),
    event_id uuid not null references public.events(id),
    created_at timestamptz not null default now(),
    constraint registrations_user_event_key unique (user_id, event_id)
);

create index if not exists registrations_event_id_idx on public.registrations (event_id, created_at);
create index if not exists registrations_user_id_idx on public.registrations (user_id, created_at desc);
