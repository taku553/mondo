import {
  createUserWithEmailAndPassword,
  deleteUser,
  EmailAuthProvider,
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  reauthenticateWithCredential,
  reauthenticateWithPopup,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updatePassword,
  validatePassword
} from "https://www.gstatic.com/firebasejs/13.2.0/firebase-auth.js";
import { app } from "./firebase_init.js";
import { setupAccount } from "./account_ui.js";

setupAccount(document, {
  auth: getAuth(app),
  createUserWithEmailAndPassword,
  deleteUser,
  emailCredential: EmailAuthProvider.credential,
  onAuthStateChanged,
  provider: new GoogleAuthProvider(),
  reauthenticateWithCredential,
  reauthenticateWithPopup,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut,
  updatePassword,
  validatePassword
});
