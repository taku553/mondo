import {
  createUserWithEmailAndPassword,
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut
} from "https://www.gstatic.com/firebasejs/13.2.0/firebase-auth.js";
import { app } from "./firebase_init.js";
import { setupAccount } from "./account_ui.js";

setupAccount(document, {
  auth: getAuth(app),
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  provider: new GoogleAuthProvider(),
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut
});
