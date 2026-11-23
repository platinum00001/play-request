-- Run in the Supabase SQL editor. Rolls itself back.
-- Expect: RLS TEST RESULT: ALL PASS
begin;
create extension if not exists pgcrypto with schema extensions;

-- Temporary test users in this transaction only (rolled back). No triggers are added to auth.users.
insert into auth.users (id, email, aud, role, encrypted_password, instance_id, created_at, updated_at)
values
  ('00000000-0000-4000-8000-000000000001', 'pr-member-a@example.com', 'authenticated', 'authenticated', crypt('x', gen_salt('bf')), '00000000-0000-0000-0000-000000000000', now(), now()),
  ('00000000-0000-4000-8000-000000000002', 'pr-member-b@example.com', 'authenticated', 'authenticated', crypt('x', gen_salt('bf')), '00000000-0000-0000-0000-000000000000', now(), now()),
  ('00000000-0000-4000-8000-000000000003', 'pr-admin@example.com', 'authenticated', 'authenticated', crypt('x', gen_salt('bf')), '00000000-0000-0000-0000-000000000000', now(), now())
on conflict (id) do nothing;

insert into play_request.admins (user_id, note)
values ('00000000-0000-4000-8000-000000000003', 'rls test')
on conflict do nothing;

create temp table pr_checks (name text, ok boolean);

create or replace function pg_temp.as_user(uid uuid, fn text) returns void language plpgsql as $$
begin
  perform set_config('request.jwt.claims', json_build_object('sub', uid, 'role', 'authenticated', 'aud', 'authenticated')::text, true);
  execute 'set local role authenticated';
  execute fn;
end;
$$;

-- anon cannot read tastings or profiles
set local role anon;
select set_config('request.jwt.claims', '{"role":"anon"}', true);
insert into pr_checks values ('anon no tastings', (select count(*) from play_request.tastings) = 0);
insert into pr_checks values ('anon no profiles', (select count(*) from play_request.profiles) = 0);
reset role;

-- member A can insert own profile + tasting
select pg_temp.as_user('00000000-0000-4000-8000-000000000001', $q$
  insert into play_request.profiles (id, display_name) values (auth.uid(), 'A');
  insert into play_request.tastings (combo_id, note) values ('sweet', 'honey');
$q$);
reset role;

select pg_temp.as_user('00000000-0000-4000-8000-000000000002', $q$
  insert into play_request.profiles (id, display_name) values (auth.uid(), 'B');
  insert into play_request.tastings (combo_id, note) values ('sour', 'lemon');
$q$);
reset role;

-- A sees only A's tasting
select pg_temp.as_user('00000000-0000-4000-8000-000000000001', $q$
  insert into pr_checks values ('A sees only own tastings', (select count(*) from play_request.tastings) = 1);
  insert into pr_checks values ('A cannot see B profile', (select count(*) from play_request.profiles where display_name = 'B') = 0);
$q$);
reset role;

-- A cannot insert as B
select pg_temp.as_user('00000000-0000-4000-8000-000000000001', $q$
  begin
    insert into play_request.tastings (user_id, combo_id) values ('00000000-0000-4000-8000-000000000002', 'salty');
    insert into pr_checks values ('A cannot write B tasting', false);
  exception when others then
    insert into pr_checks values ('A cannot write B tasting', true);
  end;
$q$);
reset role;

-- A cannot update B
do $$
declare n int;
begin
  perform set_config('request.jwt.claims', json_build_object('sub', '00000000-0000-4000-8000-000000000001', 'role', 'authenticated', 'aud', 'authenticated')::text, true);
  set local role authenticated;
  update play_request.tastings set note = 'hacked' where combo_id = 'sour';
  get diagnostics n = row_count;
  insert into pr_checks values ('A cannot update B tasting', n = 0);
  reset role;
end;
$$;

-- admin can read both and call admin_stats
select pg_temp.as_user('00000000-0000-4000-8000-000000000003', $q$
  insert into pr_checks values ('admin sees tastings', (select count(*) from play_request.tastings) >= 2);
  insert into pr_checks values ('admin_stats works', (play_request.admin_stats()->>'tastings')::int >= 2);
$q$);
reset role;

-- member cannot call admin_stats
select pg_temp.as_user('00000000-0000-4000-8000-000000000001', $q$
  begin
    perform play_request.admin_stats();
    insert into pr_checks values ('member blocked from admin_stats', false);
  exception when others then
    insert into pr_checks values ('member blocked from admin_stats', true);
  end;
$q$);
reset role;

-- delete_my_data only clears A
select pg_temp.as_user('00000000-0000-4000-8000-000000000001', $q$
  select play_request.delete_my_data();
$q$);
reset role;
select pg_temp.as_user('00000000-0000-4000-8000-000000000002', $q$
  insert into pr_checks values ('B remains after A deletes', (select count(*) from play_request.tastings) = 1);
$q$);
reset role;

-- health is public
set local role anon;
insert into pr_checks values ('anon health', (play_request.health()->>'ok')::boolean is true);
reset role;

do $$
declare fails int;
begin
  select count(*) into fails from pr_checks where ok is not true;
  if fails > 0 then
    raise exception 'RLS TEST RESULT: FAIL — %', (select string_agg(name, ', ') from pr_checks where ok is not true);
  else
    raise notice 'RLS TEST RESULT: ALL PASS (% checks)', (select count(*) from pr_checks);
  end if;
end;
$$;

rollback;
