-- MeetLens — backend ke liye extra columns.
-- Supabase → SQL Editor mein ek dafa chalayein. Dobara chalane se kuch nahi bigarta.

-- Meeting kahan se aayi (paste / audio) aur AI analysis kab, kis model se hui
alter table public.meetings add column if not exists source text not null default 'paste';
alter table public.meetings add column if not exists audio_filename text;
alter table public.meetings add column if not exists model_used text;
alter table public.meetings add column if not exists analyzed_at timestamptz;

-- Follow-up: AI ne banaya ya haath se, kab complete hua, reminder kab gayi
alter table public.followups add column if not exists source text not null default 'manual';
alter table public.followups add column if not exists completed_at timestamptz;
alter table public.followups add column if not exists reminder_sent_at timestamptz;

-- Frontend "Dropped" status bhi bhejta hai, lekin purana check sirf pending/done allow karta tha
alter table public.followups drop constraint if exists followups_status_check;
alter table public.followups add constraint followups_status_check
  check (status in ('pending', 'done', 'dropped'));
