import json
import time
import threading

from waitress import serve

from flask import (Flask, render_template, redirect,
                   request, Response, request_finished, jsonify)
from flask_login import LoginManager, login_user, logout_user, current_user
from flask_restful import Api

from forms.register import RegisterForm
from forms.login import LoginForm
from forms.add_chat import AddChatForm

from data import db_session
from data.users import Users
from data.chats import Chats
from data.messages import Messages

from data.chats_resource import ChatsListResource, ChatsResource
from data.messages_resource import (MessagesChatResource, MessagesListResource,
                                    MessagesResource, MessagesNewResource)
from data.users_resource import UsersChatsResource, UsersListResource, UsersResource

import config

app = Flask(__name__)
app.config["SECRET_KEY"] = "2sda091h23j09asd12kna13nfk23jaf1alfs9067asf"
app.config["CACHE_TYPE"] = "Redis"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300
app.config["CACHE_THRESHOLD"] = 10000

api = Api(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(Users, user_id)
    db_sess.close()
    return user


@app.route("/", methods=["GET", "POST"])
@app.route("/index", methods=["GET", "POST"])
def index():
    if not current_user.is_authenticated:
        return redirect("/register")

    try:
        db_sess = db_session.create_session()
        user_chats = db_sess.query(Users).filter(Users.id == current_user.id).first().chats

        chats = []
        for chat_id in user_chats["chats"]:
            chat = db_sess.get(Chats, chat_id)

            chat_users = chat.users["users"]
            chats.append({
                "id": chat.id,
                "name": db_sess.query(Users).filter(Users.id.in_(chat_users), Users.id != current_user.id).first().name,
                "users": chat_users,
                "messages": sorted(db_sess.query(Messages).filter(Messages.chat_id == chat.id).all(),
                                   key=lambda msg: msg.time)
            })
    finally:
        db_sess.close()

    return render_template("index.html", title=config.APP_NAME, chats=chats)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()

        user = db_sess.query(Users).filter(Users.user_name == form.user_name.data).first()
        db_sess.close()
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
        if form.password.data != form.password_again.data:
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

        login_user(new_user, remember=form.remember_me.data)

        db_sess.close()

        return redirect("/")
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

        if user.id == current_user.id:
            return render_template("add-chat.html", title=config.APP_NAME + " | Добавление чата",
                                   form=form, message=f"Вы не можете создать чат с самим собой")

        chat_users = {"users": sorted([user.id, current_user.id])}

        if db_sess.query(Chats).filter(Chats.users == chat_users).all():
            return render_template("add-chat.html", title=config.APP_NAME + " | Добавление чата",
                                   form=form, message=f"У вас уже есть чат с пользователем: \"{form.user_name.data}\"")

        chat = Chats(
            users=chat_users
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
        db_sess.close()
        return redirect("/")

    db_sess.close()
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

    db_sess.close()

    return render_template("admin-panel.html", title=config.APP_NAME + " | Панель администратора",
                           user=admins[login], data=data)


# def send_update_to_all_clients(data):
#     with sse_lock:
#         clients_to_notify = list(sse_clients)

#     for client_id in clients_to_notify:
#         try:
            


def get_current_db_data():
    db_sess = db_session.create_session()
    try:
        chats = db_sess.query(Chats).all()
        users = db_sess.query(Users).all()
        messages = db_sess.query(Messages).all()

        response = {
            "chats": {chat.id: chat.to_dict() for chat in chats},
            "users": {user.id: user.to_dict() for user in users},
            "messages": {
                msg.id: msg.to_dict(only=("id", "chat_id", "owner", "data", "time"))
                for msg in messages
            }
        }
        return response
    finally:
        db_sess.close()


@app.route("/event-stream")
def data_stream():
    if "apikey" not in request.args.keys():
        return jsonify({"message": "Incorrect url params"})

    api_key = request.args["apikey"]

    if api_key != config.APP_API_KEY:
        return jsonify({"message": "Invalid api key"})

    def generate():
        # global new_db_data
        try:
            while True:
                yield f"data: {json.dumps(get_current_db_data())}\n\n"
                time.sleep(5)
            # if new_db_data == {}:
            #     initial_data = get_current_db_data()
            #     print("Load init")
            #     new_db_data = initial_data
            #     yield f"data: {json.dumps(initial_data)}\n\n"

            # while True:
            #     for new_chat in _new_db_chats.values():
            #         new_db_data["chats"][new_chat["id"]] = new_chat
            #     for new_msg in _new_db_messages.values():
            #         new_db_data["messages"][new_msg["id"]] = new_msg
            #     _new_db_chats.clear()
            #     _new_db_messages.clear()

            #     yield f"data: {json.dumps(new_db_data)}\n\n"
            #     time.sleep(5)
        except Exception as e:
            print("Error in SSE stream:", e)

    return Response(generate(), mimetype="text/event-stream")


def format_app_info(version_path: str = None) -> str:
    suffix = f"{'-' + version_path if version_path else ''})"
    return f"Setup {config.APP_NAME} (version: {config.VERSION}{suffix}"


def main():
    print(format_app_info("02 event-stream"))
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
    serve(app, host="0.0.0.0", port="5000", threads=100)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e.__class__}", e.__traceback__.tb_frame)
        print(e)
