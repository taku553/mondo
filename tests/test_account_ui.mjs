import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const source = await readFile(new URL("../public/static/account_ui.js", import.meta.url), "utf8");
const { setupAccount } = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);

function fixture() {
  const ids = ["auth-message", "signed-out", "signed-in", "account-name", "email-form", "email", "password", "google-login", "logout"];
  const elements = Object.fromEntries(ids.map(id => [id, {
    hidden: false, value: "", textContent: "", disabled: false,
    addEventListener(type, handler) { this[type] = handler; }
  }]));
  const formButtons = [{ disabled: false }, { disabled: false }];
  elements["email-form"].querySelectorAll = () => formButtons;
  const calls = [];
  const firebase = {
    auth: {}, provider: {},
    onAuthStateChanged(_auth, next, error) { this.next = next; this.error = error; },
    async createUserWithEmailAndPassword(...args) { calls.push(["register", ...args]); },
    async signInWithEmailAndPassword(...args) { calls.push(["login", ...args]); },
    async signInWithPopup(...args) { calls.push(["google", ...args]); },
    async signOut(...args) { calls.push(["logout", ...args]); }
  };
  setupAccount({ getElementById: id => elements[id] }, firebase);
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
