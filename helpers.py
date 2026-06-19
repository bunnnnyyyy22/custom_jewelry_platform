import base64
import requests
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config


def hash_password(password: str) -> str:
    # 使用 werkzeug 的安全雜湊（PBKDF2）
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def wp_basic_auth():
    # WordPress Application Passwords 常用 Basic Auth
    return (Config.WP_USERNAME, Config.WP_APP_PASSWORD)


def push_design_to_wordpress_and_create_order(payload: dict, design_png_bytes: bytes):
    """
    這裡是「回傳設計圖至 WordPress 並創建訂單」的核心 API。
    你目前尚未提供 WordPress / WooCommerce 的具體設定，
    所以我給你一個可直接接 REST 的模板。

    payload 例如：
    {
      "product_slug": "star",
      "customer_email": "xxx@test.com",
      "customer_name": "Olsen",
      "custom_text": "..."
    }
    """
    # 1) 把 PNG 傳給 WordPress（做成媒體上傳 or 放進訂單 meta）
    # WooCommerce 常見做法：把圖當成 media attachment 再放入訂單 meta。
    # 這裡先用「把 base64 存到訂單 meta」的簡化做法（不用真的上傳 media）。
    png_b64 = base64.b64encode(design_png_bytes).decode("utf-8")

    # 2) 建立 WooCommerce 訂單
    # 你需要把 items / billing / shipping 等欄位依你的 WooCommerce 設定改掉
    data = {
        "status": "pending",
        "billing": {"email": payload.get("customer_email", "")},
        "line_items": [
            {
                # 這裡假設你 WooCommerce 已經有對應的商品 SKU 或 id
                # 你可以用 product_slug 去映射到 WooCommerce product id
                "product_id": payload.get("woocommerce_product_id", 0),
                "quantity": 1,
            }
        ],
        "meta_data": [
            {"key": "custom_product_slug", "value": payload.get("product_slug")},
            {"key": "custom_text", "value": payload.get("custom_text", "")},
            {"key": "custom_design_png_base64", "value": png_b64},
        ],
    }

    url = Config.WP_BASE_URL + Config.WC_ORDER_ENDPOINT
    resp = requests.post(url, json=data, auth=wp_basic_auth(), timeout=30)

    # 若失敗，把錯誤回傳方便你除錯
    if not resp.ok:
        raise RuntimeError(
            f"WordPress/ WooCommerce order API failed: {resp.status_code} {resp.text}"
        )

    return resp.json()
