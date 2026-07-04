-- ============================================================================
-- FIX rankingu: podniesienie limitu liczby pytań w sesji z 200 na 500
-- Powód: moduł Marketing ma 230 pytań, wiec sesja „Wszystkie" (total=230)
-- przekraczala limit total<=200 i nie zapisywala sie do rankingu.
-- Wklej całość w Supabase → SQL Editor → Run. Idempotentne.
-- ============================================================================

-- 1) Usun KAZDY check constraint na quiz_scores odwolujacy sie do limitu 200
--    (nazwa moze byc niestandardowa — dlatego dynamicznie).
do $$
declare c record;
begin
  for c in
    select conname
    from pg_constraint
    where conrelid = 'public.quiz_scores'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) ilike '%200%'
  loop
    execute format('alter table public.quiz_scores drop constraint %I', c.conname);
  end loop;
end $$;

-- 2) Dodaj nowy, nazwany constraint z limitem 500 (idempotentnie)
alter table public.quiz_scores drop constraint if exists quiz_scores_total_check;
alter table public.quiz_scores
  add constraint quiz_scores_total_check check (total > 0 and total <= 500);

-- 3) Polityka RLS na INSERT — odtworzenie z nowym limitem
drop policy if exists "Anyone can submit valid score" on public.quiz_scores;
create policy "Anyone can submit valid score"
on public.quiz_scores
for insert
to anon
with check (
  char_length(player_name) between 1 and 40
  and score >= 0
  and total > 0
  and total <= 500
  and score <= total
);
