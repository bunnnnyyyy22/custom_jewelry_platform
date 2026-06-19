import os


class Config:
    # Flask session / cookie 安全性用
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # SQLite（你也可替換成 Postgres）
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WordPress / WooCommerce（你要在 .env 設好）
    WP_BASE_URL = os.getenv("WP_BASE_URL", "https://your-wordpress-site.com")
    WP_USERNAME = os.getenv("WP_USERNAME", "")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

    # WooCommerce 用 REST API Key/Secret（二選一方式；下面給你通用寫法）
    # 如果你用 Application Password 直接認證 WP REST 也可以。
    WC_ORDER_ENDPOINT = "/wp-json/wc/v3/orders"
