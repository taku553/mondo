import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../public/static/account_ui.js", import.meta.url), "utf8");
const { setupAccount } = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);

function fixture(overrides = {}) {
  const ids = ["auth-message", "signed-out", "signed-in", "account-name", "email-form", "email", "password", "google-login", "logout",
    "password-section", "google-password-notice", "change-password-form", "current-password", "new-password", "confirm-password",
    "delete-account-form", "delete-method", "delete-method-choice", "delete-method-summary", "delete-message", "delete-submit",
    "delete-password-field", "delete-password", "delete-confirm", "password-policy", "change-policy", "change-message"];
  const elements = Object.fromEntries(ids.map(id => [id, {
    hidden: false, value: "", textContent: "", disabled: false, checked: false,
    addEventListener(type, handler) { this[type] = handler; },
    replaceChildren() { this.options = []; this.value = ""; },
    append(option) { this.options.push(option); if (!this.value) this.value = option.value; }
  }]));
  const formButtons = [{ disabled: false }, { disabled: false }];
  elements["email-form"].querySelectorAll = () => formButtons;
  elements["change-password-form"].querySelectorAll = () => [{ disabled: false }];
  elements["delete-account-form"].querySelectorAll = () => [elements["delete-submit"]];
  const calls = [];
  const firebase = {
    auth: {}, provider: {},
    onAuthStateChanged(_auth, next, error) { this.next = next; this.error = error; },
    async createUserWithEmailAndPassword(...args) { calls.push(["register", ...args]); },
    async signInWithEmailAndPassword(...args) { calls.push(["login", ...args]); },
    async signInWithPopup(...args) { calls.push(["google", ...args]); },
    async signOut(...args) { calls.push(["logout", ...args]); },
    emailCredential(email, password) { return { email, password }; },
    async reauthenticateWithCredential(...args) { calls.push(["reauth-password", ...args]); },
    async reauthenticateWithPopup(...args) { calls.push(["reauth-google", ...args]); },
    async updatePassword(...args) { calls.push(["update-password", ...args]); },
    async deleteUser(...args) { calls.push(["delete", ...args]); },
    async validatePassword() { return { passwordPolicy: { customStrengthOptions: { minPasswordLength: 8 }, allowedNonAlphanumericCharacters: "!@#" } }; }
  };
  Object.assign(firebase, overrides);
  setupAccount({ getElementById: id => elements[id], createElement: () => ({}) }, firebase);
  return { elements, firebase, calls, formButtons };
}

const flush = () => new Promise(resolve => setImmediate(resolve));

test("authentication state shows the correct screen and escapes user data as text", () => {
  const { elements, firebase } = fixture();
  firebase.next(null);
  assert.equal(elements["signed-out"].hidden, false);
  assert.equal(elements["signed-in"].hidden, true);
  firebase.next({ email: "<test@example.com>" });
  assert.equal(elements["signed-out"].hidden, true);
  assert.equal(elements["signed-in"].hidden, false);
  assert.equal(elements["account-name"].textContent, "<test@example.com>");
});

test("policy and provider-specific controls are displayed", async () => {
  const { elements, firebase } = fixture();
  await flush();
  assert.match(elements["password-policy"].textContent, /最低8文字/);
  assert.match(elements["change-policy"].textContent, /!@#/);
  firebase.next({ email: "g@example.com", providerData: [{ providerId: "google.com" }] });
  assert.equal(elements["password-section"].hidden, true);
  assert.equal(elements["google-password-notice"].hidden, false);
  assert.equal(elements["delete-method"].value, "google.com");
  assert.equal(elements["delete-method-choice"].hidden, true);
  assert.match(elements["delete-method-summary"].textContent, /Google/);
  assert.equal(elements["delete-password-field"].hidden, true);
  firebase.next({ email: "p@example.com", providerData: [{ providerId: "password" }] });
  assert.equal(elements["password-section"].hidden, false);
  assert.match(elements["delete-method-summary"].textContent, /メール／パスワード/);
  assert.equal(elements["delete-password-field"].hidden, false);
  firebase.next({ providerData: [] });
  assert.equal(elements["delete-submit"].disabled, true);
  assert.match(elements["delete-message"].textContent, /利用できる本人確認方法がありません/);
});

test("password changes require matching passwords and reauthenticate first", async () => {
  const { elements, firebase, calls } = fixture();
  const user = { email: "p@example.com", providerData: [{ providerId: "password" }] };
  firebase.next(user);
  elements["current-password"].value = "old";
  elements["new-password"].value = "new-password";
  elements["confirm-password"].value = "wrong";
  elements["change-password-form"].submit({ preventDefault() {} });
  assert.equal(calls.length, 0);
  assert.match(elements["change-message"].textContent, /一致しません/);
  elements["confirm-password"].value = "new-password";
  elements["change-password-form"].submit({ preventDefault() {} });
  await flush();
  assert.deepEqual(calls, [
    ["reauth-password", user, { email: "p@example.com", password: "old" }],
    ["update-password", user, "new-password"]
  ]);
  assert.match(elements["change-message"].textContent, /変更しました/);
  assert.equal(elements["current-password"].value, "");
});

test("deletion requires consent and reauthenticates using the selected provider", async () => {
  const { elements, firebase, calls } = fixture();
  const user = { email: "both@example.com", providerData: [{ providerId: "password" }, { providerId: "google.com" }] };
  firebase.next(user);
  assert.equal(elements["delete-method-choice"].hidden, false);
  assert.equal(elements["delete-method-summary"].hidden, true);
  assert.deepEqual(elements["delete-method"].options.map(option => option.value), ["password", "google.com"]);
  elements["delete-account-form"].submit({ preventDefault() {} });
  assert.equal(calls.length, 0);
  elements["delete-confirm"].checked = true;
  elements["delete-method"].value = "google.com";
  elements["delete-method"].change();
  assert.equal(elements["delete-password-field"].hidden, true);
  elements["delete-account-form"].submit({ preventDefault() {} });
  await flush();
  assert.deepEqual(calls, [["reauth-google", user, firebase.provider], ["delete", user]]);
  assert.match(elements["auth-message"].textContent, /削除しました/);
});

test("failed reauthentication never changes or deletes the account", async () => {
  const { elements, firebase, calls } = fixture();
  const user = { email: "p@example.com", providerData: [{ providerId: "password" }] };
  firebase.next(user);
  firebase.reauthenticateWithCredential = async () => { throw { code: "auth/wrong-password" }; };
  elements["delete-confirm"].checked = true;
  elements["delete-password"].value = "wrong";
  elements["delete-account-form"].submit({ preventDefault() {} });
  await flush();
  assert.deepEqual(calls, []);
  assert.match(elements["delete-message"].textContent, /パスワードを確認/);
  assert.equal(elements["delete-password"].value, "");
});

test("password-based account deletion reauthenticates before deleting", async () => {
  const { elements, firebase, calls } = fixture();
  const user = { email: "p@example.com", providerData: [{ providerId: "password" }] };
  firebase.next(user);
  elements.email.value = user.email;
  elements["delete-confirm"].checked = true;
  elements["delete-password"].value = "old";
  elements["delete-account-form"].submit({ preventDefault() {} });
  await flush();
  assert.deepEqual(calls, [
    ["reauth-password", user, { email: "p@example.com", password: "old" }],
    ["delete", user]
  ]);
  assert.equal(elements.email.value, "");
  firebase.next(null);
  assert.match(elements["auth-message"].textContent, /削除しました/);
});

test("failed account deletion preserves the email and displays the error", async () => {
  const { elements, firebase } = fixture();
  firebase.next({ email: "p@example.com", providerData: [{ providerId: "password" }] });
  elements.email.value = "p@example.com";
  elements["delete-confirm"].checked = true;
  elements["delete-password"].value = "old";
  firebase.deleteUser = async () => { throw { code: "auth/network-request-failed" }; };
  elements["delete-account-form"].submit({ preventDefault() {} });
  await flush();
  assert.equal(elements.email.value, "p@example.com");
  assert.match(elements["delete-message"].textContent, /通信に失敗/);
  assert.equal(elements["signed-in"].hidden, false);
});

test("policy fetch failure is displayed without hiding sign-in", async () => {
  const original = console.error;
  console.error = () => {};
  try {
    const { elements, firebase } = fixture({ validatePassword: async () => { throw new Error("offline"); } });
    firebase.next(null);
    await flush();
    assert.match(elements["password-policy"].textContent, /取得できません/);
    assert.equal(elements["signed-out"].hidden, false);
  } finally {
    console.error = original;
  }
});

test("email registration and login invoke their respective Firebase methods", async () => {
  const { elements, firebase, calls } = fixture();
  firebase.next(null);
  elements.email.value = " user@example.com ";
  elements.password.value = "password";
  let prevented = false;
  elements["email-form"].submit({ preventDefault() { prevented = true; }, submitter: { value: "register" } });
  await flush();
  assert.ok(prevented);
  assert.deepEqual(calls[0], ["register", firebase.auth, "user@example.com", "password"]);
  assert.equal(elements.password.value, "");
  elements.password.value = "password";
  elements["email-form"].submit({ preventDefault() {}, submitter: { value: "login" } });
  await flush();
  assert.deepEqual(calls[1], ["login", firebase.auth, "user@example.com", "password"]);
});

test("Google login and logout invoke Firebase", async () => {
  const { elements, firebase, calls } = fixture();
  firebase.next(null);
  elements["google-login"].click();
  await flush();
  firebase.next({ email: "user@example.com" });
  elements.logout.click();
  await flush();
  assert.deepEqual(calls, [["google", firebase.auth, firebase.provider], ["logout", firebase.auth]]);
});

test("errors are displayed and buttons are re-enabled", async () => {
  const { elements, firebase, formButtons } = fixture();
  firebase.next(null);
  firebase.signInWithPopup = async () => { throw { code: "auth/popup-blocked" }; };
  elements["google-login"].click();
  await flush();
  assert.match(elements["auth-message"].textContent, /ポップアップがブロック/);
  assert.equal(elements["google-login"].disabled, false);
  assert.ok(formButtons.every(button => !button.disabled));
});

test("prevents duplicate submissions while authentication is pending", async () => {
  const { elements, firebase, calls } = fixture();
  firebase.next(null);
  let finish;
  firebase.signInWithPopup = () => {
    calls.push("google");
    return new Promise(resolve => { finish = resolve; });
  };
  elements["google-login"].click();
  elements["google-login"].click();
  assert.deepEqual(calls, ["google"]);
  assert.equal(elements["google-login"].disabled, true);
  finish();
  await flush();
  assert.equal(elements["google-login"].disabled, false);
});
