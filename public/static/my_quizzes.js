import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/13.2.0/firebase-auth.js";
import { app } from "./firebase_init.js";

const OFFICIAL_TAG = "公式";
const MAX_QUESTIONS = 20;
const MAX_IMAGE_BYTES = 100 * 1024;
const IMAGE_WIDTH = 800;
const IMAGE_HEIGHT = 450;
const auth = getAuth(app);
const $ = id => document.getElementById(id);

let editingId = null;
let isAdmin = false;
let pendingImage = null;
let questionSeq = 0;

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

function updateQuestionCount() {
  const count = document.querySelectorAll(".mq-question").length;
  $("mq-question-count").textContent = `${count} / ${MAX_QUESTIONS}問`;
  $("mq-add-question").disabled = count >= MAX_QUESTIONS;
  document.querySelectorAll(".mq-question").forEach((block, index) => {
    block.querySelector(".mq-question-legend").textContent = `問題${index + 1}`;
    block.querySelector(".mq-q-remove").disabled = count <= 1;
  });
}

function addQuestion(question = null) {
  if (document.querySelectorAll(".mq-question").length >= MAX_QUESTIONS) return;
  const fragment = $("mq-question-template").content.cloneNode(true);
  const block = fragment.querySelector(".mq-question");
  questionSeq += 1;
  const groupName = `mq-correct-${questionSeq}`;
  block.querySelectorAll(".mq-q-correct").forEach(radio => { radio.name = groupName; });
  block.querySelector(".mq-q-remove").addEventListener("click", () => {
    block.remove();
    updateQuestionCount();
  });
  if (question) {
    block.querySelector(".mq-q-text").value = question.text;
    block.querySelector(".mq-q-explanation").value = question.explanation || "";
    question.choices.forEach((choice, i) => {
      block.querySelectorAll(".mq-q-choice")[i].value = choice.text;
    });
    const radio = block.querySelector(`.mq-q-correct[value="${question.correct_choice_id}"]`);
    if (radio) radio.checked = true;
  }
  $("mq-questions").append(fragment);
  updateQuestionCount();
}

function resetQuestions() {
  $("mq-questions").replaceChildren();
  addQuestion();
}

function setImagePreview(src) {
  const preview = $("mq-image-preview");
  preview.src = src || "";
  preview.hidden = !src;
}

function loadImageElement(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => { URL.revokeObjectURL(url); resolve(image); };
    image.onerror = () => { URL.revokeObjectURL(url); reject(new Error("画像を読み込めませんでした")); };
    image.src = url;
  });
}

function canvasToJpeg(canvas, quality) {
  return new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", quality));
}

function blobToDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error("画像の変換に失敗しました"));
    reader.readAsDataURL(blob);
  });
}

// 800×450に中央切り抜きし、100KB以下になるまで JPEG の品質を下げる
async function processImage(file) {
  const image = await loadImageElement(file);
  const canvas = document.createElement("canvas");
  canvas.width = IMAGE_WIDTH;
  canvas.height = IMAGE_HEIGHT;
  const scale = Math.max(IMAGE_WIDTH / image.naturalWidth, IMAGE_HEIGHT / image.naturalHeight);
  const drawWidth = image.naturalWidth * scale;
  const drawHeight = image.naturalHeight * scale;
  canvas.getContext("2d").drawImage(
    image,
    (IMAGE_WIDTH - drawWidth) / 2,
    (IMAGE_HEIGHT - drawHeight) / 2,
    drawWidth,
    drawHeight,
  );
  for (let quality = 0.92; quality >= 0.5; quality -= 0.06) {
    const blob = await canvasToJpeg(canvas, quality);
    if (blob && blob.size <= MAX_IMAGE_BYTES) return blobToDataUrl(blob);
  }
  throw new Error("画像を100KB以下に圧縮できませんでした。別の画像を選んでください。");
}

function readQuestions() {
  return [...document.querySelectorAll(".mq-question")].map(block => {
    const correct = block.querySelector(".mq-q-correct:checked");
    return {
      text: block.querySelector(".mq-q-text").value,
      choices: [...block.querySelectorAll(".mq-q-choice")].map(input => input.value),
      correct_choice_id: correct ? Number(correct.value) : null,
      explanation: block.querySelector(".mq-q-explanation").value,
    };
  });
}

function readForm() {
  return {
    title: $("mq-title").value,
    genre: $("mq-genre").value,
    summary: $("mq-summary").value,
    tags: $("mq-tags").value.split(/[,、]/),
    status: $("mq-status").value,
    questions: readQuestions(),
    image: pendingImage,
  };
}

function resetForm() {
  editingId = null;
  pendingImage = null;
  $("mq-form").reset();
  $("mq-form-title").textContent = "新しいクイズを作成";
  $("mq-submit").textContent = "保存";
  $("mq-status").value = "published";
  setImagePreview(null);
  resetQuestions();
  showMessage("");
}

function fillForm(quiz) {
  editingId = quiz.id;
  pendingImage = null;
  $("mq-form-title").textContent = "クイズを編集";
  $("mq-submit").textContent = "更新";
  $("mq-title").value = quiz.title;
  $("mq-genre").value = quiz.genre || "";
  $("mq-summary").value = quiz.summary || "";
  $("mq-tags").value = quiz.tags.filter(tag => tag !== OFFICIAL_TAG).join(", ");
  $("mq-status").value = quiz.status;
  $("mq-image-input").value = "";
  setImagePreview(quiz.image);
  $("mq-questions").replaceChildren();
  quiz.questions.forEach(question => addQuestion(question));
  updateQuestionCount();
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

function validateClientSide(body) {
  if (!body.genre.trim()) return "ジャンルを入力してください";
  if (!body.summary.trim()) return "説明を入力してください";
  if (!editingId && !body.image) return "画像を選択してください";
  if (body.questions.length < 1 || body.questions.length > MAX_QUESTIONS) return `問題は1〜${MAX_QUESTIONS}問で作成してください`;
  for (const [index, question] of body.questions.entries()) {
    const label = `問題${index + 1}`;
    if (!question.text.trim()) return `${label}の問題文を入力してください`;
    if (question.choices.some(choice => !choice.trim())) return `${label}の選択肢をすべて入力してください`;
    if (!question.correct_choice_id) return `${label}の正解を選んでください`;
  }
  return null;
}

$("mq-image-input").addEventListener("change", async event => {
  const file = event.target.files[0];
  pendingImage = null;
  setImagePreview(null);
  if (!file) return;
  try {
    pendingImage = await processImage(file);
    setImagePreview(pendingImage);
  } catch (error) {
    event.target.value = "";
    showMessage(error.message);
  }
});

$("mq-add-question").addEventListener("click", () => addQuestion());

$("mq-form").addEventListener("submit", async event => {
  event.preventDefault();
  showMessage("");
  const body = readForm();
  const problem = validateClientSide(body);
  if (problem) {
    showMessage(problem);
    return;
  }
  const submit = $("mq-submit");
  submit.disabled = true;
  try {
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
resetQuestions();

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
