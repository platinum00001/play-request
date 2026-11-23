/* Sign in (email link, password, Google, Facebook) and account dashboard. */
(function () {
  const PR = window.PR;
  const esc = PR.esc;
  const ACCOUNT_URL = function () { return PR.pageURL("account.html"); };
  const PROVIDERS = { google: "Google", facebook: "Facebook" };
  let recoveryMode = false;

  function googleIcon() { return '<svg aria-hidden="true" viewBox="0 0 48 48" width="20" height="20"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3 0 5.8 1.1 7.9 3l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z"/></svg>'; }
  function fbIcon() { return '<svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20"><path fill="#1877F2" d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12z"/></svg>'; }

  function urlAuthError() {
    const q = new URLSearchParams(location.search), h = new URLSearchParams(location.hash.replace(/^#/, ""));
    const d = h.get("error_description") || q.get("error_description");
    if (!d) return "";
    history.replaceState(null, "", location.pathname);
    if (/provider is not enabled|Unsupported provider/i.test(d)) return "That sign-in option isn't switched on yet. Please use email for now.";
    if (/expired|invalid/i.test(d)) return "That sign-in link has expired or was already used. Please request a new one.";
    return d.replace(/\+/g, " ");
  }
  function friendlyAuth(error) {
    const m = String(error.message || "");
    if (/rate limit|too many/i.test(m)) return "Too many tries — please wait a few minutes and try again.";
    if (/Invalid login credentials/i.test(m)) return "That email and password don't match. Try the email link instead?";
    if (/Email not confirmed/i.test(m)) return "Please confirm your email first (check your inbox), or use the email link.";
    if (/sending.*email|confirmation email/i.test(m)) return "We couldn't send the email right now. Please try again later.";
    if (/provider is not enabled|Unsupported provider/i.test(m)) return "That sign-in option isn't switched on yet. Please use email for now.";
    return m;
  }

  function localSummary() {
    const s = PR.loadLocal();
    const n = Object.keys(s.tastings || {}).length;
    return '<section class="card" id="on-this-device"><h2>Saved on this device</h2><p>' +
      (n ? "You have <strong>" + n + "</strong> tasting" + (n === 1 ? "" : "s") + " saved in this browser. Sign in to keep them if you switch phones."
        : "Nothing tasted yet. Progress is saved in this browser even without an account.") +
      '</p><p class="hint">You can also <button class="linklike" type="button" id="export-save">export a backup</button> or <label class="linklike">import one <input type="file" id="import-save" accept="application/json" hidden></label>.</p></section>';
  }

  function hookLocal() {
    const ex = document.getElementById("export-save");
    if (ex) ex.addEventListener("click", function () {
      const blob = new Blob([JSON.stringify(PR.loadLocal(), null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "play-request-save.json";
      a.click();
    });
    const im = document.getElementById("import-save");
    if (im) im.addEventListener("change", function () {
      const f = im.files && im.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = function () {
        try {
          const incoming = JSON.parse(reader.result);
          const merged = PR.mergeStates(PR.loadLocal(), incoming);
          PR.saveLocal(merged);
          render("Imported. Your tastings on this device were merged with the file.");
        } catch (e) { render("That file didn't look like a Play Request save."); }
      };
      reader.readAsText(f);
    });
  }

  async function authForm(area, sb, notice) {
    const settings = await PR.authSettings();
    const ext = (settings && settings.external) || {};
    const providers = ["google", "facebook"].map(function (p) {
      const on = !!(ext[p]);
      const icon = p === "google" ? googleIcon() : fbIcon();
      return '<button type="button" class="btn btn-line" data-provider="' + p + '" ' + (on ? "" : 'data-soon="1"') + ">" +
        icon + " Continue with " + PROVIDERS[p] + (on ? "" : ' <span class="soon">Soon</span>') + "</button>";
    }).join("");
    area.innerHTML = '<div class="card"><h2>Sign in to sync your tastings</h2>' +
      (notice ? '<div class="notice info">' + esc(notice) + "</div>" : "") +
      '<p>Progress is already saved on this device. An account keeps it when you switch phones.</p>' +
      '<div class="auth-grid" style="margin:14px 0">' + providers + "</div>" +
      '<form id="magic" class="auth-grid"><label for="email">Email</label><input id="email" name="email" type="email" required autocomplete="email" placeholder="you@example.com">' +
      '<button class="btn" type="submit">Email me a sign-in link</button><p id="magic-msg" class="hint"></p></form>' +
      '<details style="margin-top:16px"><summary>Use a password instead</summary>' +
      '<form id="pass" class="auth-grid" style="margin-top:12px">' +
      '<label for="pemail">Email</label><input id="pemail" name="email" type="email" required autocomplete="email">' +
      '<label for="password">Password</label><input id="password" name="password" type="password" required minlength="6" autocomplete="current-password">' +
      '<div class="form-actions"><button class="btn" type="submit">Sign in</button>' +
      '<button class="btn btn-line" type="button" id="signup">Create account</button>' +
      '<button class="linklike" type="button" id="forgot">Forgot password?</button></div>' +
      '<p id="pass-msg" class="hint"></p></form></details></div>' + localSummary();
    hookLocal();
    area.querySelectorAll("[data-provider]").forEach(function (b) {
      b.addEventListener("click", async function () {
        if (b.getAttribute("data-soon")) { document.getElementById("magic-msg").textContent = PROVIDERS[b.dataset.provider] + " sign-in isn't switched on yet. Use email for now — the setup steps are in the login guide on this site."; return; }
        const { error } = await sb.auth.signInWithOAuth({ provider: b.dataset.provider, options: { redirectTo: ACCOUNT_URL() } });
        if (error) document.getElementById("magic-msg").textContent = friendlyAuth(error);
      });
    });
    document.getElementById("magic").addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = document.getElementById("email").value.trim();
      const { error } = await sb.auth.signInWithOtp({ email: email, options: { emailRedirectTo: ACCOUNT_URL() } });
      document.getElementById("magic-msg").textContent = error ? friendlyAuth(error) : "Check your email for a sign-in link.";
    });
    document.getElementById("pass").addEventListener("submit", async function (e) {
      e.preventDefault();
      const { error } = await sb.auth.signInWithPassword({ email: document.getElementById("pemail").value.trim(), password: document.getElementById("password").value });
      if (error) document.getElementById("pass-msg").textContent = friendlyAuth(error);
      else render();
    });
    document.getElementById("signup").addEventListener("click", async function () {
      const { error } = await sb.auth.signUp({ email: document.getElementById("pemail").value.trim(), password: document.getElementById("password").value, options: { emailRedirectTo: ACCOUNT_URL() } });
      document.getElementById("pass-msg").textContent = error ? friendlyAuth(error) : "Account started. Check your email to confirm, then sign in.";
    });
    document.getElementById("forgot").addEventListener("click", async function () {
      const email = document.getElementById("pemail").value.trim();
      if (!email) { document.getElementById("pass-msg").textContent = "Enter your email first."; return; }
      const { error } = await sb.auth.resetPasswordForEmail(email, { redirectTo: ACCOUNT_URL() });
      document.getElementById("pass-msg").textContent = error ? friendlyAuth(error) : "Check your email for a reset link.";
    });
  }

  function recoveryForm(area, sb) {
    area.innerHTML = '<div class="card"><h2>Choose a new password</h2><form id="np" class="auth-grid"><label for="npw">New password</label><input id="npw" type="password" required minlength="6" autocomplete="new-password"><button class="btn" type="submit">Save password</button><p id="np-msg" class="hint"></p></form></div>';
    document.getElementById("np").addEventListener("submit", async function (e) {
      e.preventDefault();
      const { error } = await sb.auth.updateUser({ password: document.getElementById("npw").value });
      if (error) { document.getElementById("np-msg").textContent = friendlyAuth(error); return; }
      recoveryMode = false;
      render("Password updated. You are signed in.");
    });
  }

  async function dashboard(area, sb, user) {
    await PR.syncOnLogin();
    const state = PR.loadLocal();
    const n = Object.keys(state.tastings).length;
    const rows = Object.keys(state.tastings).sort().map(function (id) {
      const t = state.tastings[id];
      return "<tr><td>" + esc(id) + "</td><td>" + (t.rating || "—") + "</td><td>" + esc(t.example || t.dish || "") + "</td><td>" + esc((t.at || "").slice(0, 10)) + "</td></tr>";
    }).join("");
    area.innerHTML = '<div class="card"><h2>Welcome back</h2><p>Signed in as ' + esc(user.email || "your account") + '. ' + n + " tasting" + (n === 1 ? "" : "s") + " synced to this account and this device.</p>" +
      '<form id="prof" class="auth-grid"><label for="dname">Display name</label><input id="dname" maxlength="80" value="' + esc(state.displayName || "") + '"><button class="btn btn-line" type="submit">Save name</button><p id="p-msg" class="hint"></p></form>' +
      (n ? '<div style="overflow:auto;margin-top:16px"><table class="data"><thead><tr><th>Combo</th><th>Rating</th><th>What you tried</th><th>Date</th></tr></thead><tbody>' + rows + "</tbody></table></div>" : "") +
      '<p style="margin-top:16px"><a class="btn" href="index.html">Back to the board</a> <button class="btn btn-line" type="button" id="signout">Sign out</button></p>' +
      '<h2 style="margin-top:28px">Delete my data</h2><p>This removes your Play Request tastings and profile from the account. The copy on this device can be cleared too.</p>' +
      '<button class="btn btn-line" type="button" id="wipe">Delete my Play Request data</button><p id="wipe-msg" class="hint"></p></div>' + localSummary();
    hookLocal();
    document.getElementById("prof").addEventListener("submit", async function (e) {
      e.preventDefault();
      const name = document.getElementById("dname").value.trim();
      const st = PR.loadLocal(); st.displayName = name; PR.saveLocal(st);
      await PR.ensureProfile(name);
      document.getElementById("p-msg").textContent = "Saved.";
    });
    document.getElementById("signout").addEventListener("click", async function () { await sb.auth.signOut(); render("You are signed out. Progress is still on this device."); });
    document.getElementById("wipe").addEventListener("click", async function () {
      if (!confirm("Delete ALL your Play Request account data? This cannot be undone.")) return;
      try {
        const { error } = await sb.rpc("delete_my_data");
        if (error) throw error;
      } catch (e) {
        try { await PR.api("delete_my_data"); } catch (e2) {
          document.getElementById("wipe-msg").textContent = "Couldn't delete: " + PR.friendlyError(e);
          return;
        }
      }
      const empty = { version: 1, displayName: "", tastings: {}, updatedAt: new Date().toISOString() };
      PR.saveLocal(empty);
      await sb.auth.signOut();
      render("Your Play Request data was deleted and you are signed out.");
    });
  }

  async function render(notice) {
    const area = document.getElementById("account-area");
    const { sb, user } = await PR.getUser();
    if (!sb) { area.innerHTML = '<div class="notice info"><strong>Accounts are coming soon.</strong> Your tastings are still saved on this device.</div>' + localSummary(); hookLocal(); return; }
    if (!PR._authHooked) {
      PR._authHooked = true;
      sb.auth.onAuthStateChange(function (evt) { if (evt === "PASSWORD_RECOVERY") { recoveryMode = true; recoveryForm(area, sb); } if (evt === "SIGNED_IN") render(); });
    }
    if (recoveryMode) return recoveryForm(area, sb);
    if (!user) authForm(area, sb, typeof notice === "string" ? notice : urlAuthError());
    else dashboard(area, sb, user);
  }
  document.addEventListener("DOMContentLoaded", function () { render(); });
})();
