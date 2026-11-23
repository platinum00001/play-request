# Play Request — setup and James's manual steps

Live site: https://platinum00001.github.io/play-request/
Repo: https://github.com/platinum00001/play-request
Database: Supabase project **james-sites** (`oiousqgzqcjanikglkxl`), schema **`play_request`**
Contact email (one constant in `config.js` → `CONTACT_EMAIL`): **not set yet** — add it there and every page follows.

The game works today without any of the steps below: tastings are saved in the browser (localStorage). Steps 1–2 switch on accounts and cross-device sync.

## 1. Expose the `play_request` schema (recommended — 1 minute)

Until this is done, the site talks to the database through the **play-request-api** edge function, which already works without a dashboard change. Exposing the schema lets the browser talk to the tables directly as a backup path.

1. Open https://supabase.com/dashboard/project/oiousqgzqcjanikglkxl/integrations/data_api/overview (Project Settings → Data API).
2. Under **Exposed schemas**, add `play_request` (keep `public` and `graphql_public`; add `milestones`, `rtr_app`, `clubs4love` and `boatservice` too if they aren't there yet).
3. Save.

## 2. Add the sign-in redirect URL (required for login links)

1. Open https://supabase.com/dashboard/project/oiousqgzqcjanikglkxl/auth/url-configuration
2. Under **Redirect URLs**, add: `https://platinum00001.github.io/play-request/**`
3. Save. **Do not change the Site URL** — it's shared with the other sites.

## 3. Make yourself an admin (for the Staff page)

Sign in once on https://platinum00001.github.io/play-request/account.html, then run in the Supabase SQL editor (replace the email):

```sql
insert into play_request.admins (user_id, note)
select id, 'James' from auth.users where email = 'YOUR-EMAIL@example.com'
on conflict do nothing;
```

The staff page then shows member and tasting counts, popular combos, and a CSV download.

Remove an admin: `delete from play_request.admins where user_id = (select id from auth.users where email = '…');`

## 4. Google and Facebook sign-in

The buttons are already on the account page with a **Soon** tag until the providers are enabled. One project-wide setup covers Play Request and the other apps.

See **[FACEBOOK-GOOGLE-LOGIN-SETUP.md](FACEBOOK-GOOGLE-LOGIN-SETUP.md)** for the exact redirect URLs and click-by-click steps. You will need to create a Facebook Developer app and a Google OAuth client; I cannot create those on your accounts.

## 5. Email sending via Resend (recommended)

Supabase's built-in email is rate-limited. For reliable magic links and password resets:

1. Create a free account at https://resend.com (3,000 emails/month free) and verify a domain you own.
2. Supabase → Authentication → Emails → SMTP Settings → Enable custom SMTP:
   host `smtp.resend.com`, port `465`, user `resend`, password = your Resend API key,
   sender e.g. `Play Request <hello@yourdomain>`.
3. One SMTP setting covers all the apps in this project.

## 6. Reserve social handles and a contact email

Suggested handles (not created — do this yourself): `playrequest`, `play_request`. Paste full profile URLs into `SOCIAL` in `config.js` once they exist. Set `CONTACT_EMAIL` in the same file.

## 7. Housekeeping

- Schema file: `supabase/schema.sql` (safe to re-run). Edge function: `play-request-api`.
- RLS test: `tests/rls.test.sql` (run in the SQL editor; it rolls itself back).
- Path test: `node tests/paths.test.js`. Unlock test: `node tests/unlock.test.js`.
- Restaurant/dish CSV: `data/play-request-restaurants-dishes.csv`.
- Printable game: `play-request-board-game.pdf`.

## Schema summary

| Table | Who can do what |
|---|---|
| `profiles` | Member: own row (created on first sign-in by the site — no trigger on `auth.users`). Admin: read. |
| `tastings` | Member: CRUD own tastings only. Admin: read. |
| `admins` | Managed in the SQL editor only. |

Functions: `health()`, `my_roles()`, `admin_stats()`, `delete_my_data()`, `is_admin()`.
