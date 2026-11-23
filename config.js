/*
 * Play Request — public site configuration (edit here, nowhere else).
 * The Supabase URL and publishable key are PUBLIC by design: security is enforced by
 * Row Level Security in supabase/schema.sql and the play-request-api edge function.
 * NEVER put a service_role / secret key here.
 */
window.PR_CONFIG = {
  SUPABASE_URL: "https://oiousqgzqcjanikglkxl.supabase.co",
  SUPABASE_ANON_KEY: "sb_publishable_IJHa5taHcttV2DSZq45fWQ_bVbRDbA2", // publishable key (safe to publish)
  SUPABASE_SCHEMA: "play_request",     // this site's own schema in the shared "james-sites" project
  API_FUNCTION: "play-request-api",    // used if the schema is not yet exposed to the Data API

  // TODO(James): add a real inbox. Empty = the footer does not show an email address.
  CONTACT_EMAIL: "",

  // TODO(James): social accounts are NOT created yet. Paste the full profile URL once each
  // account exists; empty entries show as "coming soon".
  SOCIAL: {
    instagram: "", // TODO e.g. https://www.instagram.com/playrequest/
    facebook: "",  // TODO e.g. https://www.facebook.com/playrequest
    x: ""          // TODO e.g. https://x.com/playrequest
  }
};
