-- ============================================================================
-- Quiz z marketingu — konfiguracja tabeli wyników (leaderboard) w Supabase
-- Wklej całość w Supabase → SQL Editor → Run.
-- Idempotentne: można uruchomić ponownie bez błędów.
-- ============================================================================

-- 1) Tabela wyników --------------------------------------------------------
create table if not exists public.quiz_scores (
  id uuid primary key default gen_random_uuid(),
  player_name text not null check (char_length(player_name) between 1 and 40),
  score integer not null check (score >= 0),
  total integer not null check (total > 0 and total <= 200),
  -- percent liczony automatycznie po stronie bazy (nie ufamy klientowi):
  percent integer generated always as (
    round((score::numeric / total::numeric) * 100)::integer
  ) stored,
  scope text not null default 'all',
  session_length text,
  best_streak integer not null default 0 check (best_streak >= 0),
  -- spójność: liczba poprawnych nie może przekroczyć liczby pytań
  created_at timestamptz not null default now(),
  constraint quiz_scores_score_le_total check (score <= total)
);

-- Indeks pod dokładnie taki sort, jaki robi front (percent↓, score↓, created_at↑)
create index if not exists quiz_scores_rank_idx
  on public.quiz_scores (percent desc, score desc, created_at asc);

-- 2) Row Level Security ----------------------------------------------------
alter table public.quiz_scores enable row level security;

-- SELECT: publicznie czytelne
drop policy if exists "Anyone can read leaderboard" on public.quiz_scores;
create policy "Anyone can read leaderboard"
on public.quiz_scores
for select
to anon
using (true);

-- INSERT: każdy anon może dodać wynik, ale tylko sensowny/poprawny
drop policy if exists "Anyone can submit valid score" on public.quiz_scores;
create policy "Anyone can submit valid score"
on public.quiz_scores
for insert
to anon
with check (
  char_length(player_name) between 1 and 40
  and score >= 0
  and total > 0
  and total <= 200
  and score <= total
);

-- Brak polityk UPDATE/DELETE dla anon => operacje te są zablokowane przez RLS.

-- 3) Uprawnienia dla roli anon --------------------------------------------
grant usage on schema public to anon;
grant select, insert on public.quiz_scores to anon;

-- 4) Realtime (live ranking) ----------------------------------------------
-- Dodaj tabelę do publikacji realtime tylko jeśli jej tam jeszcze nie ma,
-- inaczej ponowne uruchomienie skryptu rzuci błędem "is already member".
do $$
begin
  if not exists (
    select 1
    from pg_publication_tables
    where pubname = 'supabase_realtime'
      and schemaname = 'public'
      and tablename = 'quiz_scores'
  ) then
    execute 'alter publication supabase_realtime add table public.quiz_scores';
  end if;
end
$$;
