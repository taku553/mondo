from py.main import app
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# プロキシ環境への対応
app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))