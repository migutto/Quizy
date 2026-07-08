-- ============================================================================
-- ANALITYKA — tabela zdarzeń (page_view / quiz_start / quiz_complete) + widoki
-- Wklej całość w Supabase → SQL Editor → Run. Idempotentne.
-- Front wysyła eventy metodą trackQuizEvent() (insert do quiz_events).
-- ============================================================================

create table if not exists public.quiz_events (
  id uuid primary key default gen_random_uuid(),

  event_type text not null check (
    event_type in ('page_view', 'quiz_start', 'quiz_complete')
  ),

  session_id text,
  module text,
  player_name text,
  scope text,
  session_length text,

  score integer,
  total integer,

  percent integer generated always as (
    case
      when score is null or total is null or total = 0 then null
      else round((score::numeric / total::numeric) * 100)::integer
    end
  ) stored,

  created_at timestamptz not null default now()
);

alter table public.quiz_events enable row level security;

drop policy if exists "Anyone can insert quiz events" on public.quiz_events;

create policy "Anyone can insert quiz events"
on public.quiz_events
for insert
to anon
with check (
  event_type in ('page_view', 'quiz_start', 'quiz_complete')
  and (module is null or char_length(module) between 1 and 40)
  and (player_name is null or char_length(player_name) between 1 and 40)
  and (score is null or score >= 0)
  and (total is null or total > 0)
  and (score is null or total is null or score <= total)
);

grant usage on schema public to anon;
grant insert on public.quiz_events to anon;

-- Widok: statystyki dzienne ---------------------------------------------------
create or replace view public.quiz_stats_daily as
select
  date_trunc('day', created_at)::date as dzien,

  count(*) filter (where event_type = 'page_view') as wejscia,
  count(*) filter (where event_type = 'quiz_start') as rozpoczecia,
  count(*) filter (where event_type = 'quiz_complete') as ukonczenia,

  count(distinct session_id) as unikalne_sesje,

  round(
    100.0 * count(*) filter (where event_type = 'quiz_complete')
    / nullif(count(*) filter (where event_type = 'quiz_start'), 0),
    1
  ) as procent_ukonczen,

  round(
    avg(percent) filter (where event_type = 'quiz_complete'),
    1
  ) as sredni_wynik_proc
from public.quiz_events
group by 1
order by 1 desc;

-- Widok: statystyki łączne ----------------------------------------------------
create or replace view public.quiz_stats_total as
select
  count(*) filter (where event_type = 'page_view') as wszystkie_wejscia,
  count(*) filter (where event_type = 'quiz_start') as wszystkie_rozpoczecia,
  count(*) filter (where event_type = 'quiz_complete') as wszystkie_ukonczenia,
  count(distinct session_id) as wszystkie_unikalne_sesje,

  round(
    100.0 * count(*) filter (where event_type = 'quiz_complete')
    / nullif(count(*) filter (where event_type = 'quiz_start'), 0),
    1
  ) as procent_ukonczen,

  round(
    avg(percent) filter (where event_type = 'quiz_complete'),
    1
  ) as sredni_wynik_proc
from public.quiz_events;
