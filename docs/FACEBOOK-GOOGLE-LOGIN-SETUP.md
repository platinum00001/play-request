# Google and Facebook login setup (Play Request)

The Sign in page already has **Continue with Google** and **Continue with Facebook** buttons. They stay marked “Soon” and show a friendly message until the providers are switched on in the shared Supabase project **james-sites** (`oiousqgzqcjanikglkxl`). One setup covers Play Request and the other sites in that project.

You have to create the Google and Facebook apps yourself (I cannot create developer apps on your accounts). Use the exact callback URLs below. **Do not change the Supabase Site URL** — only add redirect URLs.

Play Request live origin: `https://platinum00001.github.io/play-request/`

## A. Add the Play Request redirect in Supabase (2 minutes)

1. Open https://supabase.com/dashboard/project/oiousqgzqcjanikglkxl/auth/url-configuration
2. Under **Redirect URLs**, add:

   `https://platinum00001.github.io/play-request/**`

3. Save. Leave the Site URL alone.

## B. Google (Google Cloud OAuth)

1. Open https://console.cloud.google.com/apis/credentials
2. Create credentials → **OAuth client ID** → application type **Web application**.
3. Authorized JavaScript origins (optional but tidy):

   `https://oiousqgzqcjanikglkxl.supabase.co`

   `https://platinum00001.github.io`

4. Authorized redirect URI — this must be exact:

   `https://oiousqgzqcjanikglkxl.supabase.co/auth/v1/callback`

5. OAuth consent screen: app name (e.g. Play Request), support email, and the privacy policy URL:

   `https://platinum00001.github.io/play-request/privacy.html`

6. Copy the Client ID and Client Secret.
7. In Supabase: Authentication → Sign In / Providers → **Google** → Enable. Paste the Client ID and Secret. Save.

The Google button on https://platinum00001.github.io/play-request/account.html will then sign people in and return them to the account page. After that, their tastings sync.

## C. Facebook (Meta / Facebook Login)

You need a Facebook Developer app.

1. Open https://developers.facebook.com/apps and create an app. Choose **Authenticate and request data from users with Facebook Login**.
2. Add the **Facebook Login** product if it is not already added.
3. Facebook Login → Settings → **Valid OAuth Redirect URIs**. Add exactly:

   `https://oiousqgzqcjanikglkxl.supabase.co/auth/v1/callback`

4. App settings → Basic:
   - Privacy Policy URL: `https://platinum00001.github.io/play-request/privacy.html`
   - User data deletion → “Data deletion instructions URL”:

     `https://platinum00001.github.io/play-request/privacy.html#data-deletion`

5. Copy the App ID and App Secret.
6. In Supabase: Authentication → Sign In / Providers → **Facebook** → Enable. Paste the App ID and Secret. Save.
7. Switch the Facebook app from Development to **Live** when you are ready for the public. Facebook will not let random users sign in while the app is in Development mode.

## D. Check that it worked

1. Open https://platinum00001.github.io/play-request/account.html
2. The Soon tags on Google and Facebook should disappear once the providers are enabled (the page reads the public auth settings).
3. Sign in with one provider, then try a flavor on the board. Sign out, sign in on another browser, and confirm the tasting is still there.

If a provider is still marked Soon after you enable it, wait a minute and refresh. If you get “provider is not enabled,” the secret was not saved or the wrong project was edited.

## E. Email login (already wired)

Magic-link and password sign-in work as soon as step A is done. For reliable email delivery, add Resend SMTP (see `SETUP.md` step 5). Without it, test emails may be rate-limited.
