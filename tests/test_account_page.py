import os
import unittest

os.environ["APP_ENV"] = "development"

from py.main import app


class AccountPageTest(unittest.TestCase):
    def test_account_page_and_home_link(self):
        client = app.test_client()
        home = client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn(b'href="/account"', home.data)

        account = client.get("/account")
        self.assertEqual(account.status_code, 200)
        for value in (b'id="email-form"', b'id="google-login"', b'id="logout"',
                      b'/static/account.js', b'href="/"'):
            self.assertIn(value, account.data)

    def test_auth_assets_are_served(self):
        client = app.test_client()
        for name in ("account.js", "account_ui.js", "firebase_init.js"):
            response = client.get("/static/" + name)
            self.assertEqual(response.status_code, 200)
            response.close()


if __name__ == "__main__":
    unittest.main()
