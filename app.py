from flask import (
    Flask,
    abort,
    render_template,
    redirect,
    url_for,
    request,
    flash,
)
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jewelry.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── 頁面路由 ──────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/shop")
@login_required
def shop():
    return render_template("shop.html")


@app.route("/product/leaf")
def leaf():
    free_mode = request.args.get("mode") == "free"
    # 非免費模式才需要登入
    if not free_mode and not current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("leaf.html", free_mode=free_mode)


@app.route("/product/avocado")
@login_required
def avocado():
    if not current_user.is_paid:
        return redirect(url_for("shop"))  # 沒付款踢回商品頁
    return render_template("avocado.html")


@app.route("/product/starfish")
@login_required
def starfish():
    if not current_user.is_paid:
        return redirect(url_for("shop"))
    return render_template("starfish.html")


# ── 會員 ──────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    email = request.form["email"]
    password = generate_password_hash(request.form["password"])
    if User.query.filter_by(email=email).first():
        flash("此 Email 已被註冊")
        return redirect(url_for("index"))
    user = User(username=username, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    flash("註冊成功，請登入")
    return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        return redirect(url_for("shop"))
    flash("帳號或密碼錯誤")
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# ── 模擬付款 ──────────────────────────────────────────
@app.route("/mock_pay", methods=["POST"])
@login_required
def mock_pay():
    current_user.is_paid = True
    db.session.commit()
    return {"ok": True}


# ── 初始化資料庫 ──────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
