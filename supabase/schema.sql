-- Play Request — schema play_request in the shared "james-sites" project.
-- Lives in its OWN schema so it never touches other sites' tables. Safe to re-run.
-- No trigger on auth.users. Profiles are created by the site on first sign-in.
-- After running: Project Settings > Data API > Exposed schemas should include "play_request"
-- (the site also works through the play-request-api edge function if the schema is not exposed yet).

create extension if not exists pgcrypto with schema extensions;
create schema if not exists play_request;

create table if not exists play_request.profiles (
  id           uuid primary key default auth.uid() references auth.users (id) on delete cascade,
  display_name text check (char_length(display_name) <= 80),
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

create table if not exists play_request.admins (
  user_id    uuid primary key references auth.users (id) on delete cascade,
  note       text,
  created_at timestamptz not null default now()
);

create table if not exists play_request.tastings (
  id             uuid primary key default gen_random_uuid(),
  user_id        uuid not null default auth.uid() references auth.users (id) on delete cascade,
  combo_id       text not null check (char_length(combo_id) between 3 and 80),
  rating         int check (rating is null or rating between 1 and 5),
  note           text check (char_length(note) <= 2000),
  example        text check (char_length(example) <= 200),
  restaurant_id  text check (char_length(restaurant_id) <= 80),
  dish           text check (char_length(dish) <= 160),
  tasted_at      timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  unique (user_id, combo_id)
);
create index if not exists pr_tastings_user_idx on play_request.tastings (user_id, tasted_at desc);

create or replace function play_request.set_updated_at()
returns trigger language plpgsql
set search_path = play_request, public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists pr_profiles_updated_at on play_request.profiles;
create trigger pr_profiles_updated_at before update on play_request.profiles
  for each row execute function play_request.set_updated_at();

drop trigger if exists pr_tastings_updated_at on play_request.tastings;
create trigger pr_tastings_updated_at before update on play_request.tastings
  for each row execute function play_request.set_updated_at();

create or replace function play_request.is_admin()
returns boolean
language sql
stable
security definer
set search_path = play_request, public
as $$
  select exists (select 1 from play_request.admins where user_id = (select auth.uid()));
$$;

create or replace function play_request.health()
returns jsonb
language sql
stable
set search_path = play_request, public
as $$
  select jsonb_build_object('ok', true, 'schema', 'play_request', 'version', 1);
$$;

create or replace function play_request.my_roles()
returns jsonb
language sql
stable
security definer
set search_path = play_request, public
as $$
  select jsonb_build_object('admin', play_request.is_admin());
$$;

create or replace function play_request.admin_stats()
returns jsonb
language plpgsql
stable
security definer
set search_path = play_request, public
as $$
declare
  result jsonb;
begin
  if not play_request.is_admin() then
    raise exception 'Admins only' using errcode = '42501';
  end if;
  select jsonb_build_object(
    'members', (select count(*) from play_request.profiles),
    'tastings', (select count(*) from play_request.tastings),
    'popular', coalesce((
      select jsonb_agg(row_to_json(x))
      from (
        select combo_id, count(*)::int as n
        from play_request.tastings
        group by combo_id
        order by count(*) desc, combo_id
        limit 12
      ) x
    ), '[]'::jsonb)
  ) into result;
  return result;
end;
$$;

create or replace function play_request.delete_my_data()
returns void
language plpgsql
security definer
set search_path = play_request, public
as $$
declare
  uid uuid := (select auth.uid());
begin
  if uid is null then
    raise exception 'Not signed in' using errcode = '42501';
  end if;
  delete from play_request.tastings where user_id = uid;
  delete from play_request.profiles where id = uid;
end;
$$;

alter table play_request.profiles  enable row level security;
alter table play_request.admins    enable row level security;
alter table play_request.tastings  enable row level security;

drop policy if exists profiles_select on play_request.profiles;
drop policy if exists profiles_insert_own on play_request.profiles;
drop policy if exists profiles_update_own on play_request.profiles;
drop policy if exists profiles_delete_own on play_request.profiles;
create policy profiles_select on play_request.profiles
  for select to authenticated using (id = (select auth.uid()) or (select play_request.is_admin()));
create policy profiles_insert_own on play_request.profiles
  for insert to authenticated with check (id = (select auth.uid()));
create policy profiles_update_own on play_request.profiles
  for update to authenticated using (id = (select auth.uid())) with check (id = (select auth.uid()));
create policy profiles_delete_own on play_request.profiles
  for delete to authenticated using (id = (select auth.uid()));

-- admins table: no public policies (managed in the SQL editor only)
drop policy if exists admins_admin_read on play_request.admins;
create policy admins_admin_read on play_request.admins
  for select to authenticated using ((select play_request.is_admin()));

drop policy if exists tastings_select on play_request.tastings;
drop policy if exists tastings_insert_own on play_request.tastings;
drop policy if exists tastings_update_own on play_request.tastings;
drop policy if exists tastings_delete_own on play_request.tastings;
create policy tastings_select on play_request.tastings
  for select to authenticated using (user_id = (select auth.uid()) or (select play_request.is_admin()));
create policy tastings_insert_own on play_request.tastings
  for insert to authenticated with check (user_id = (select auth.uid()));
create policy tastings_update_own on play_request.tastings
  for update to authenticated using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));
create policy tastings_delete_own on play_request.tastings
  for delete to authenticated using (user_id = (select auth.uid()));

grant usage on schema play_request to anon, authenticated;
grant select, insert, update, delete on play_request.profiles to authenticated;
grant select, insert, update, delete on play_request.tastings to authenticated;
grant select on play_request.admins to authenticated;
grant execute on function play_request.health() to anon, authenticated;
grant execute on function play_request.is_admin() to authenticated;
grant execute on function play_request.my_roles(), play_request.admin_stats(), play_request.delete_my_data() to authenticated;
