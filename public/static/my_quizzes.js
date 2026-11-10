import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/13.2.0/firebase-auth.js";
import { app } from "./firebase_init.js";

const OFFICIAL_TAG = "公式";
const auth = getAuth(app);
const $ = id => document.getElementById(id);

let editingId = null;
let isAdmin = false;

async function api(path, options = {}) {
  const user = auth.currentUser;
  if (!user) throw new Error("ログインが必要です");
  const token = await user.getIdToken();
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.errors ? data.errors.join(" / ") : (data.error || `エラー（${response.status}）`));
  }
  return data;
}

function showMessage(text, isError = true) {
  const message = $("mq-message");
  message.textContent = text;
  message.style.color = isError ? "#b00020" : "#1b7f3b";
}

function readForm() {
  const correct = document.querySelector('input[name="mq-correct"]:checked');
  return {
    title: $("mq-title").value,
    tags: $("mq-tags").value.split(/[,、]/),
    status: $("mq-status").value,
    text: $("mq-text").value,
    explanation: $("mq-explanation").value,
    choices: [0, 1, 2, 3].map(i => $(`mq-choice-${i}`).value),
    correct_choice_id: correct ? Number(correct.value) : null,
  };
}

function resetForm() {
  editingId = null;
  $("mq-form").reset();
  $("mq-form-title").textContent = "新しいクイズを作成";
  $("mq-submit").textContent = "保存";
  $("mq-status").value = "published";
  showMessage("");
}

function fillForm(quiz) {
  editingId = quiz.id;
  $("mq-form-title").textContent = "クイズを編集";
  $("mq-submit").textContent = "更新";
  $("mq-title").value = quiz.title;
  $("mq-tags").value = quiz.tags.filter(tag => tag !== OFFICIAL_TAG).join(", ");
  $("mq-status").value = quiz.status;
  $("mq-text").value = quiz.text;
  $("mq-explanation").value = quiz.explanation;
  quiz.choices.forEach((choice, i) => { $(`mq-choice-${i}`).value = choice.text; });
  const radio = document.querySelector(`input[name="mq-correct"][value="${quiz.correct_choice_id}"]`);
  if (radio) radio.checked = true;
  showMessage("");
  $("mq-form").scrollIntoView({ behavior: "smooth" });
}

function makeButton(label, className, onClick, disabled = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `mq-button ${className}`;
  button.textContent = label;
  button.disabled = disabled;
  button.addEventListener("click", onClick);
  return button;
}

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleDateString("ja-JP") : "";
}

function makeBadge(text, hidden = false) {
  const badge = document.createElement("span");
  badge.className = hidden ? "mq-badge hidden" : "mq-badge";
  badge.textContent = text;
  return badge;
}

function renderMyList(quizzes) {
  const list = $("mq-my-list");
  list.replaceChildren();
  if (quizzes.length === 0) {
    const empty = document.createElement("p");
    empty.className = "mq-meta";
    empty.textContent = "まだクイズがありません。";
    list.append(empty);
    return;
  }
  quizzes.forEach(quiz => {
    const row = document.createElement("div");
    row.className = "mq-list-item";

    const info = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = quiz.title;
    const meta = document.createElement("div");
    meta.className = "mq-meta";
    meta.textContent = `${formatDate(quiz.created_at)} ・ ${quiz.status === "published" ? "公開中" : "非公開"}`;
    info.append(title, meta);
    if (quiz.moderation === "hidden") {
      info.append(makeBadge("運営により非公開", true));
    }

    const buttons = document.createElement("div");
    buttons.className = "mq-buttons";
    const locked = quiz.moderation === "hidden";
    buttons.append(
      makeButton("編集", "secondary", () => fillForm(quiz), locked),
      makeButton("削除", "danger", () => deleteQuiz(quiz)),
    );
    row.append(info, buttons);
    list.append(row);
  });
}

function renderAdminList(quizzes) {
  const list = $("mq-admin-list");
  list.replaceChildren();
  if (quizzes.length === 0) {
    const empty = document.createElement("p");
    empty.className = "mq-meta";
    empty.textContent = "ユーザー作成クイズはまだありません。";
    list.append(empty);
    return;
  }
  quizzes.forEach(quiz => {
    const row = document.createElement("div");
    row.className = "mq-list-item";

    const info = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = quiz.title;
    const meta = document.createElement("div");
    meta.className = "mq-meta";
    meta.textContent = `${formatDate(quiz.created_at)} ・ ${quiz.status === "published" ? "公開中" : "非公開"} ・ 作成者 ${quiz.author_uid}`;
    info.append(title, meta);
    if (quiz.moderation === "hidden") {
      info.append(makeBadge("運営により非公開", true));
    }

    const isHidden = quiz.moderation === "hidden";
    const toggle = makeButton(
      isHidden ? "非公開を解除" : "非公開にする",
      isHidden ? "secondary" : "danger",
      () => moderate(quiz, isHidden ? "none" : "hidden"),
    );
    const buttons = document.createElement("div");
    buttons.className = "mq-buttons";
    buttons.append(toggle);
    row.append(info, buttons);
    list.append(row);
  });
}

async function moderate(quiz, moderation) {
  try {
    await api(`/api/admin/my_quizzes/${quiz.id}/moderation`, { method: "PATCH", body: { moderation } });
    await loadAdminList();
  } catch (error) {
    showMessage(error.message);
  }
}

async function deleteQuiz(quiz) {
  if (!window.confirm(`「${quiz.title}」を削除しますか？この操作は取り消せません。`)) return;
  try {
    await api(`/api/my_quizzes/${quiz.id}`, { method: "DELETE" });
    if (editingId === quiz.id) resetForm();
    await loadMyList();
  } catch (error) {
    showMessage(error.message);
  }
}

async function loadMyList() {
  const data = await api("/api/my_quizzes");
  isAdmin = data.is_admin;
  $("mq-tags-note").textContent = isAdmin ? "管理者の作成したクイズには「公式」タグが自動で付きます。" : "";
  renderMyList(data.quizzes);
  $("mq-admin-section").hidden = !isAdmin;
  if (isAdmin) await loadAdminList();
}

async function loadAdminList() {
  const data = await api("/api/admin/my_quizzes");
  renderAdminList(data.quizzes);
}

$("mq-form").addEventListener("submit", async event => {
  event.preventDefault();
  showMessage("");
  const submit = $("mq-submit");
  submit.disabled = true;
  try {
    const body = readForm();
    if (editingId) {
      await api(`/api/my_quizzes/${editingId}`, { method: "PUT", body });
    } else {
      await api("/api/my_quizzes", { method: "POST", body });
    }
    const saved = editingId ? "更新しました" : "作成しました";
    resetForm();
    await loadMyList();
    showMessage(saved, false);
  } catch (error) {
    showMessage(error.message);
  } finally {
    submit.disabled = false;
  }
});

$("mq-reset").addEventListener("click", resetForm);

onAuthStateChanged(auth, async user => {
  $("mq-login-required").hidden = Boolean(user);
  $("mq-content").hidden = !user;
  if (!user) return;
  try {
    await loadMyList();
  } catch (error) {
    showMessage(error.message);
  }
});
