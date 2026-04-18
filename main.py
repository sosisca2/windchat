import json

from waitress import serve

from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_restful import Api

from forms.register import RegisterForm
from forms.login import LoginForm
from forms.add_chat import AddChatForm

from data import db_session
from data.users import Users
from data.chats import Chats
from data.messages import Messages

from data.chats_resource import *
from data.messages_resource import *
from data.users_resource import *

import config

app = Flask(__name__)
app.config["SECRET_KEY"] = "2sda091h23j09asd12kn"

api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(Users, user_id)


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    if not current_user.is_authenticated:
        return redirect("/register")

    db_sess = db_session.create_session()
    user_chats = db_sess.query(Users).filter(Users.id == current_user.id).first().chats

    chats = []
    for chat_id in user_chats["chats"]:
        chat = db_sess.query(Chats).filter(Chats.id == chat_id).first()

        users = chat.users["users"]
        chats.append({
            "id": chat.id,
            "name": db_sess.query(Users).filter(Users.id.in_(users), Users.id != current_user.id).first().name,
            "users": users,
            "messages": sorted(db_sess.query(Messages).filter(Messages.chat_id == chat.id).all(),
                               key=lambda msg: msg.time)
        })

    return render_template("index.html", title=config.APP_NAME, chats=chats)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()

        user = db_sess.query(Users).filter(Users.user_name == form.user_name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        else:
            return render_template("login.html", title=f"{config.APP_NAME} | Вход",
                                   form=form, message="Тег пользователя или пароль не верны")
    return render_template("login.html", title=f"{config.APP_NAME} | Вход", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.submit.data:
        if form.password != form.password_again:
            return render_template("register.html", title=f"{config.APP_NAME} | Регистрация",
                                   form=form, message=f"Пароли не совпадают")

        db_sess = db_session.create_session()

        if db_sess.query(Users).filter(Users.user_name == form.user_name.data).first():
            return render_template("register.html", title=f"{config.APP_NAME} | Регистрация", form=form,
                                   message=f"Пользователь \"{form.user_name.data}\" уже существует")

        new_user = Users(
            user_name=form.user_name.data,
            surname=form.surname.data,
            name=form.name.data,
            email=form.email.data
        )
        new_user.set_password(form.password.data)

        db_sess.add(new_user)
        db_sess.commit()
        # login_user(new_user, form.remember_me.data)
        return redirect("/login")
    return render_template("register.html", title=f"{config.APP_NAME} | Регистрация", form=form)


@app.route("/add-chat", methods=["GET", "POST"])
def add_chat():
    form = AddChatForm()
    db_sess = db_session.create_session()

    if form.validate_on_submit():
        user = db_sess.query(Users).filter(Users.user_name == form.user_name.data).first()

        if not user:
            return render_template("add-chat.html", title=config.APP_NAME + " | Добавление чата",
                                   form=form, message=f"Пользователь: \"{form.user_name.data}\" не найден.")

        chat = Chats(
            users={"users": [user.id, current_user.id]}
        )
        db_sess.add(chat)

        # db_sess.query(Chats).filter(Chats.id == chat.id).update({Chats.users, json.dumps({
        #     "users": db_sess.get(Chats, chat.id).users["users"] + cur
        # })})

        db_sess.query(Users).filter(Users.id == current_user.id).update({Users.chats: {
            "chats": db_sess.get(Users, current_user.id).chats["chats"] + [chat.id]
        }})

        db_sess.query(Users).filter(Users.id == user.id).update({Users.chats: {
            "chats": db_sess.get(Users, user.id).chats["chats"] + [chat.id]
        }})

        db_sess.commit()
        return redirect("/")
    return render_template("add-chat.html", title=config.APP_NAME + "| Добавление чата", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@app.route("/admin-panel/<login>/<password>", methods=["GET", "POST"])
def admin_panel(login: str, password: str):
    with open(config.ADMINS_FILE) as f:
        admins = json.load(f)["admins"]

    if login not in admins.keys() or admins[login]["password"] != password:
        return "Invalid login or password"

    data = {}
    db_sess = db_session.create_session()

    data["register_users"] = db_sess.query(Users).count()
    data["chats_created"] = db_sess.query(Chats).count()

    data["users_list"] = db_sess.query(Users).all()
    data["chats_list"] = db_sess.query(Chats).all()

    return render_template("admin-panel.html", title=config.APP_NAME + " | Панель администратора",
                           user=admins[login], data=data)

# import datetime

# datetime.datetime.date().strftime("%d/%m/%Y, %H:%M:%S")

def format_app_info(version_path: str = None) -> str:
    return f"Setup {config.APP_NAME} (version: {config.VERSION}" +\
           f"{"-" + version_path if version_path else ""})"


def main():
    print(format_app_info("0.1"))
    db_session.global_init(config.DB_PATH)

    api.add_resource(ChatsListResource, '/api/chats')
    api.add_resource(ChatsResource, '/api/chats/<int:chat_id>')
    api.add_resource(MessagesChatResource, '/api/chats/messages/<int:chat_id>')

    api.add_resource(MessagesListResource, '/api/messages')
    api.add_resource(MessagesResource, '/api/messages/<int:msg_id>')
    api.add_resource(MessagesNewResource, '/api/messages/new/<int:chat_id>')

    api.add_resource(UsersListResource, '/api/users')
    api.add_resource(UsersResource, '/api/users/<int:user_id>')
    api.add_resource(UsersChatsResource, '/api/users/chats/<int:user_id>')

    # app.run(debug=True)
    serve(app, host="0.0.0.0", port="5000")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e.__class__}", e.__traceback__.tb_frame)
        print(e)