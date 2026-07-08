-- ============================================================================
-- Quizy - bezpieczny panel admina przez Supabase Auth
-- Wklej calosc w Supabase -> SQL Editor -> Run.
--
-- Po uruchomieniu:
-- 1. Utworz konto w Supabase Auth (Authentication -> Users).
-- 2. Oznacz je jako admina:
--    insert into public.quiz_admins (user_id)
--    select id from auth.users where email = 'twoj-email@example.com'
--    on conflict do nothing;
--
-- Ten skrypt zastepuje stare funkcje oparte o haslo przekazywane z frontendu.
-- Autoryzacja opiera sie o Supabase Auth + RLS, bez sekretow w HTML/JS.
-- ============================================================================

create table if not exists public.quiz_admins (
  user_id uuid primary key references auth.users(id) on delete cascade,
  created_at timestamptz not null default now()
);

alter table public.quiz_admins enable row level security;

drop policy if exists "Admins can read own admin flag" on public.quiz_admins;
create policy "Admins can read own admin flag"
on public.quiz_admins
for select
to authenticated
using (user_id = (select auth.uid()));

grant select on public.quiz_admins to authenticated;

-- Po zalogowaniu panel dziala jako rola authenticated, wiec potrzebuje
-- osobnych polityk odczytu obok dotychczasowych polityk dla anon.
drop policy if exists "Authenticated can read leaderboard" on public.quiz_scores;
create policy "Authenticated can read leaderboard"
on public.quiz_scores
for select
to authenticated
using (true);

grant select on public.quiz_scores to authenticated;

-- Usun stare warianty funkcji, ktore przyjmowaly sekret z klienta.
drop function if exists public.admin_delete_score(uuid, text);
drop function if exists public.admin_delete_score(text, text);
drop function if exists public.admin_reset_module(text, text);

create or replace function public.is_quiz_admin()
returns boolean
language sql
stable
security invoker
set search_path = ''
as $$
  select (select auth.uid()) is not null
    and exists (
      select 1
      from public.quiz_admins qa
      where qa.user_id = (select auth.uid())
    );
$$;

drop policy if exists "Quiz admins can delete scores" on public.quiz_scores;
create policy "Quiz admins can delete scores"
on public.quiz_scores
for delete
to authenticated
using ((select public.is_quiz_admin()));

grant delete on public.quiz_scores to authenticated;

create or replace function public.require_quiz_admin()
returns void
language plpgsql
security invoker
set search_path = ''
as $$
begin
  if not public.is_quiz_admin() then
    raise exception 'not authorized' using errcode = '42501';
  end if;
end;
$$;

create or replace function public.admin_delete_score(p_id uuid)
returns integer
language plpgsql
security invoker
set search_path = ''
as $$
declare
  deleted_count integer;
begin
  perform public.require_quiz_admin();

  delete from public.quiz_scores
  where id = p_id;

  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$;

create or replace function public.admin_reset_module(p_module text)
returns integer
language plpgsql
security invoker
set search_path = ''
as $$
declare
  deleted_count integer;
begin
  perform public.require_quiz_admin();

  delete from public.quiz_scores
  where module = p_module;

  get diagnostics deleted_count = row_count;
  return deleted_count;
end;
$$;

revoke all on function public.is_quiz_admin() from public, anon;
revoke all on function public.require_quiz_admin() from public, anon;
revoke all on function public.admin_delete_score(uuid) from public, anon;
revoke all on function public.admin_reset_module(text) from public, anon;

grant execute on function public.is_quiz_admin() to authenticated;
grant execute on function public.require_quiz_admin() to authenticated;
grant execute on function public.admin_delete_score(uuid) to authenticated;
grant execute on function public.admin_reset_module(text) to authenticated;

-- Opcjonalna tabela analityki. Jesli istnieje, pozwol zalogowanemu adminowi
-- czytac eventy w panelu.
do $$
begin
  if to_regclass('public.quiz_events') is not null then
    execute 'drop policy if exists "Authenticated can read quiz events" on public.quiz_events';
    execute 'create policy "Authenticated can read quiz events" on public.quiz_events for select to authenticated using (true)';
    execute 'grant select on public.quiz_events to authenticated';
  end if;
end
$$;
