import io
import base64

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from models import db, User
from config import Config
from helpers import (
    hash_password,
    verify_password,
    push_design_to_wordpress_and_create_order,
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.route("/")
    def hero():
        """
        Hero Section（登入/付費導流）
        左：免費體驗 -> 1畫面（只允許海星、不能下載）
        右：付費訂購 -> 2畫面（登入/註冊）
        """
        return render_template("hero.html")

    @app.route("/free")
    def free_experience():
        """
        1畫面：只有一個客製化畫布（海星），不能下載設計圖。
        底下按鈕回 Hero。
        """
        return render_template("free_star.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """
        2畫面：登入/註冊
        - 登入若沒有此用戶：顯示警告訊息
        - 登入成功：進入 3畫面（商品選擇）
        """
        message = None

        if request.method == "POST":
            mode = request.form.get("mode")  # "login" or "register"
            email = (request.form.get("email") or "").strip().lower()
            password = request.form.get("password") or ""

            if not email or not password:
                message = "請輸入 Email 與密碼"
            else:
                if mode == "register":
                    # 註冊：若 email 已存在就拒絕
                    if User.query.filter_by(email=email).first():
                        message = "此 Email 已註冊過，請直接登入"
                    else:
                        # 註冊後先給 free，實務上你可接付款後改 paid
                        # 這裡為了符合你需求：註冊後仍進入登入流程（你可改為 paid）
                        user = User(
                            email=email,
                            password_hash=hash_password(password),
                            plan="paid",
                        )
                        db.session.add(user)
                        db.session.commit()

                        login_user(user)
                        return redirect(url_for("products"))
                else:
                    # login
                    user = User.query.filter_by(email=email).first()
                    if not user:
                        # 你要求：沒有此用戶就跳警告
                        message = "找不到此用戶，請先註冊或確認 Email"
                    elif not verify_password(password, user.password_hash):
                        message = "密碼錯誤，請再試一次"
                    else:
                        login_user(user)
                        return redirect(url_for("products"))

        return render_template("login.html", message=message)

    @app.route("/products")
    @login_required
    def products():
        """
        3畫面：三個商品（葉子/酪梨/海星），選擇後導入各自客製化畫布（進入 4畫面）
        """
        # 付費方案限制：只允許 paid 進入
        if current_user.plan != "paid":
            return redirect(url_for("hero"))

        return render_template("products.html")

    @app.route("/customize/<product_slug>")
    def customize(product_slug):
        """
        4畫面：客製化畫布，可下載 PNG（paid）或不可下載（free）。
        下載 PNG 在前端匯出，回傳 WordPress 需要 server 端驗權限與拿到 PNG bytes。
        """
        # 判斷 free/paid
        is_paid = current_user.is_authenticated and current_user.plan == "paid"

        # free 版本只允許 star
        if not is_paid and product_slug != "star":
            return redirect(url_for("free_experience"))

        return render_template(
            "customize.html",
            product_slug=product_slug,
            allow_download=is_paid,  # paid 顯示下載與回傳
        )

    @app.route("/api/push-wordpress", methods=["POST"])
    @login_required
    def api_push_wordpress():
        """
        4畫面：一鍵回傳設計圖至 WordPress，生成商品訂單進入購物車。
        這裡只允許 paid。
        """
        if current_user.plan != "paid":
            return (
                jsonify({"success": False, "message": "需要付費方案才能回傳訂單"}),
                403,
            )

        data = request.get_json(force=True)

        # 前端送來 base64 PNG（dataURL 去掉前綴）
        design_data_url = data.get("design_png_data_url", "")
        if not design_data_url.startswith("data:image/png;base64,"):
            return (
                jsonify({"success": False, "message": "design_png_data_url 格式錯誤"}),
                400,
            )

        design_b64 = design_data_url.split(",", 1)[1]
        try:
            design_png_bytes = base64.b64decode(design_b64)
        except Exception:
            return jsonify({"success": False, "message": "PNG base64 解碼失敗"}), 400

        payload = {
            "product_slug": data.get("product_slug"),
            "customer_email": current_user.email,
            "customer_name": data.get("customer_name", ""),
            "custom_text": data.get("custom_text", ""),
            "woocommerce_product_id": data.get(
                "woocommerce_product_id", 0
            ),  # 你後續要補對映
        }

        try:
            result = push_design_to_wordpress_and_create_order(
                payload, design_png_bytes
            )
            return jsonify(
                {
                    "success": True,
                    "message": "已送出到 WordPress，訂單建立完成",
                    "wp_result": result,
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # 建表
        db.create_all()

    app.run(host="0.0.0.0", port=5000, debug=True)
