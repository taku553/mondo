const errorMessages = {
  "auth/invalid-email": "メールアドレスの形式を確認してください。",
  "auth/invalid-credential": "メールアドレスまたはパスワードを確認してください。",
  "auth/wrong-password": "メールアドレスまたはパスワードを確認してください。",
  "auth/user-not-found": "メールアドレスまたはパスワードを確認してください。",
  "auth/email-already-in-use": "このメールアドレスは既に使われています。ログインしてください。",
  "auth/weak-password": "パスワードが要件を満たしていません。別のパスワードをお試しください。",
  "auth/too-many-requests": "試行回数が多すぎます。しばらく待ってからお試しください。",
  "auth/network-request-failed": "通信に失敗しました。接続を確認してください。",
  "auth/popup-blocked": "ポップアップがブロックされました。許可してからお試しください。",
  "auth/popup-closed-by-user": "Google ログインがキャンセルされました。",
  "auth/unauthorized-domain": "このドメインは認証に許可されていません。管理者にお問い合わせください。",
  "auth/operation-not-allowed": "このログイン方法は利用できません。管理者にお問い合わせください。",
  "auth/account-exists-with-different-credential": "このメールアドレスは別のログイン方法で登録されています。元の方法でログインしてください。"
};

export function setupAccount(document, firebase) {
  const message = document.getElementById("auth-message");
  const signedOut = document.getElementById("signed-out");
  const signedIn = document.getElementById("signed-in");
  const accountName = document.getElementById("account-name");
  const form = document.getElementById("email-form");
  const email = document.getElementById("email");
  const password = document.getElementById("password");
  const google = document.getElementById("google-login");
  const logout = document.getElementById("logout");
  const buttons = [...form.querySelectorAll("button"), google, logout];
  let busy = false;

  function showError(error) {
    console.error("Firebase Authentication error:", error);
    message.textContent = errorMessages[error.code] || "認証に失敗しました。しばらくしてからもう一度お試しください。";
  }

  async function run(operation) {
    if (busy) return;
    busy = true;
    buttons.forEach(button => { button.disabled = true; });
    message.textContent = "処理中です…";
    try {
      await operation();
      password.value = "";
      message.textContent = "";
    } catch (error) {
      showError(error);
    } finally {
      busy = false;
      buttons.forEach(button => { button.disabled = false; });
    }
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    const action = event.submitter?.value || "login";
    run(() => action === "register"
      ? firebase.createUserWithEmailAndPassword(firebase.auth, email.value.trim(), password.value)
      : firebase.signInWithEmailAndPassword(firebase.auth, email.value.trim(), password.value));
  });
  google.addEventListener("click", () => run(() => firebase.signInWithPopup(firebase.auth, firebase.provider)));
  logout.addEventListener("click", () => run(() => firebase.signOut(firebase.auth)));

  firebase.onAuthStateChanged(firebase.auth, user => {
    signedOut.hidden = Boolean(user);
    signedIn.hidden = !user;
    accountName.textContent = user ? (user.email || user.displayName || "ログイン済み") : "";
    if (!busy) message.textContent = "";
  }, error => {
    signedOut.hidden = true;
    signedIn.hidden = true;
    showError(error);
  });
}
