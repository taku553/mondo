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
  "auth/account-exists-with-different-credential": "このメールアドレスは別のログイン方法で登録されています。元の方法でログインしてください。",
  "auth/requires-recent-login": "本人確認の有効期限が切れました。もう一度お試しください。",
  "auth/user-mismatch": "ログイン中のアカウントと同じ Google アカウントを選択してください。",
  "auth/user-disabled": "このアカウントは無効になっています。"
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
  const passwordSection = document.getElementById("password-section");
  const googlePasswordNotice = document.getElementById("google-password-notice");
  const changeForm = document.getElementById("change-password-form");
  const currentPassword = document.getElementById("current-password");
  const newPassword = document.getElementById("new-password");
  const confirmPassword = document.getElementById("confirm-password");
  const changeMessage = document.getElementById("change-message");
  const deleteForm = document.getElementById("delete-account-form");
  const deleteMethod = document.getElementById("delete-method");
  const deleteMethodChoice = document.getElementById("delete-method-choice");
  const deleteMethodSummary = document.getElementById("delete-method-summary");
  const deleteMessage = document.getElementById("delete-message");
  const deleteSubmit = document.getElementById("delete-submit");
  const deletePasswordField = document.getElementById("delete-password-field");
  const deletePassword = document.getElementById("delete-password");
  const deleteConfirm = document.getElementById("delete-confirm");
  const policyMessages = [document.getElementById("password-policy"), document.getElementById("change-policy")];
  const buttons = [...form.querySelectorAll("button"), ...changeForm.querySelectorAll("button"),
    ...deleteForm.querySelectorAll("button"), google, logout];
  let currentUser = null;
  let initialStateReceived = false;
  let busy = false;

  function showError(error, feedback = message) {
    console.error("Firebase Authentication error:", error);
    feedback.textContent = errorMessages[error?.code] || "認証に失敗しました。しばらくしてからもう一度お試しください。";
  }

  async function run(operation, successMessage = "", feedback = message, successTarget = feedback) {
    if (busy) return;
    busy = true;
    buttons.forEach(button => { button.disabled = true; });
    message.textContent = "";
    feedback.textContent = "処理中です…";
    try {
      await operation();
      password.value = "";
      currentPassword.value = "";
      newPassword.value = "";
      confirmPassword.value = "";
      deletePassword.value = "";
      deleteConfirm.checked = false;
      feedback.textContent = "";
      successTarget.textContent = successMessage;
    } catch (error) {
      currentPassword.value = "";
      deletePassword.value = "";
      showError(error, feedback);
    } finally {
      busy = false;
      buttons.forEach(button => { button.disabled = false; });
      deleteSubmit.disabled = !deleteMethod.value;
    }
  }

  async function loadPasswordPolicy() {
    try {
      const { passwordPolicy } = await firebase.validatePassword(firebase.auth, "");
      const options = passwordPolicy.customStrengthOptions;
      const requirements = [`最低${options.minPasswordLength}文字`];
      if (options.maxPasswordLength) requirements.push(`最大${options.maxPasswordLength}文字`);
      if (options.containsLowercaseLetter) requirements.push("英小文字");
      if (options.containsUppercaseLetter) requirements.push("英大文字");
      if (options.containsNumericCharacter) requirements.push("数字");
      if (options.containsNonAlphanumericCharacter) requirements.push("記号");
      const symbols = passwordPolicy.allowedNonAlphanumericCharacters;
      const text = `パスワード条件: ${requirements.join("・")}。${symbols
        ? `記号の要件を満たす文字: ${symbols}。`
        : "記号の例（記号必須の場合に要件を満たす文字）: ^ $ * . [ ] { } ( ) ? \" ! @ # % & / \\ , > < ' : ; | _ ~。"}`
        + " ほかの文字を使える場合もあります。Firebase の設定によって追加条件が適用される場合があります。";
      policyMessages.forEach(element => { element.textContent = text; });
    } catch (error) {
      console.error("Firebase password policy error:", error);
      policyMessages.forEach(element => { element.textContent = "パスワード条件を取得できませんでした。通信を確認し、ページを再読み込みしてください。"; });
    }
  }

  function updateDeleteMethod() {
    const usesPassword = deleteMethod.value === "password";
    deletePasswordField.hidden = !usesPassword;
    deletePassword.required = usesPassword;
    deletePassword.value = "";
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

  changeForm.addEventListener("submit", event => {
    event.preventDefault();
    if (!currentUser || busy) return;
    if (newPassword.value !== confirmPassword.value) {
      changeMessage.textContent = "新しいパスワードが一致しません。";
      return;
    }
    const user = currentUser;
    run(async () => {
      const credential = firebase.emailCredential(user.email, currentPassword.value);
      await firebase.reauthenticateWithCredential(user, credential);
      await firebase.updatePassword(user, newPassword.value);
    }, "パスワードを変更しました。", changeMessage);
  });

  deleteMethod.addEventListener("change", updateDeleteMethod);
  deleteForm.addEventListener("submit", event => {
    event.preventDefault();
    if (!currentUser || busy) return;
    if (!deleteConfirm.checked) {
      deleteMessage.textContent = "アカウント削除への同意を確認してください。";
      return;
    }
    const user = currentUser;
    const method = deleteMethod.value;
    if (method !== "password" && method !== "google.com") {
      deleteMessage.textContent = "本人確認方法を選択してください。";
      return;
    }
    run(async () => {
      if (method === "password") {
        await firebase.reauthenticateWithCredential(user, firebase.emailCredential(user.email, deletePassword.value));
      } else {
        await firebase.reauthenticateWithPopup(user, firebase.provider);
      }
      await firebase.deleteUser(user);
      email.value = "";
    }, "アカウントを削除しました。ブラウザに保存されたログイン情報は別途削除してください。", deleteMessage, message);
  });

  firebase.onAuthStateChanged(firebase.auth, user => {
    currentUser = user;
    signedOut.hidden = Boolean(user);
    signedIn.hidden = !user;
    accountName.textContent = user ? (user.email || user.displayName || "ログイン済み") : "";
    const providers = user?.providerData || [];
    const hasPassword = providers.some(provider => provider.providerId === "password");
    const hasGoogle = providers.some(provider => provider.providerId === "google.com");
    passwordSection.hidden = !hasPassword;
    googlePasswordNotice.hidden = !hasGoogle || hasPassword;
    deleteMethod.replaceChildren();
    const availableMethods = [];
    for (const [value, label, enabled] of [["password", "メール／パスワード", hasPassword], ["google.com", "Google", hasGoogle]]) {
      if (enabled) {
        availableMethods.push(label);
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        deleteMethod.append(option);
      }
      deleteMethodChoice.hidden = availableMethods.length < 2;
      deleteMethodSummary.hidden = availableMethods.length !== 1;
      deleteMethodSummary.textContent = availableMethods.length === 1 ? `本人確認方法: ${availableMethods[0]}` : "";
      deleteSubmit.disabled = busy || availableMethods.length === 0;
      deleteMessage.textContent = user && availableMethods.length === 0
        ? "利用できる本人確認方法がありません。管理者にお問い合わせください。"
        : "";
      changeMessage.textContent = "";
    }
    updateDeleteMethod();
    if (!initialStateReceived && !busy) message.textContent = "";
    initialStateReceived = true;
  }, error => {
    signedOut.hidden = true;
    signedIn.hidden = true;
    showError(error);
  });
  loadPasswordPolicy();
}
