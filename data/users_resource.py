import json
from flask import jsonify
from flask_restful import reqparse, abort, Resource
from data import db_session
from data.users import Users
from data.chats import Chats
from data.messages import Messages

post_parser = reqparse.RequestParser()
post_parser.add_argument("name", required=True)
post_parser.add_argument("messages", required=True)
post_parser.add_argument("users", required=True)

put_parser = reqparse.RequestParser()
put_parser.add_argument("name")
put_parser.add_argument("message")
put_parser.add_argument("user")


def abort_if_user_not_found(user_id):
    db_sess = db_session.create_session()
    if not db_sess.get(Users, user_id):
        abort(404, message=f"User {user_id} not found")


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        db_sess = db_session.create_session()
        user = db_sess.get(Users, user_id)
        return jsonify(user.to_dict())


class UsersListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        users = db_sess.query(Users).all()
        return jsonify({"users": [item.to_dict() for item in users]})


class UsersChatsResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        db_sess = db_session.create_session()
        user_chats = db_sess.get(Users, user_id).chats

        chats = []

        for chat_id in user_chats["chats"]:
            chat_dict = db_sess.get(Chats, chat_id).to_dict()
            users = chat_dict["users"]["users"]
            chat_dict["name"] = (db_sess.query(Users)
                                        .filter(Users.id.in_(users), Users.id != user_id)
                                        .first().name)

            chat_messages = (db_sess.query(Messages)
                                    .filter(Messages.chat_id == chat_id)
                                    .all())
            chat_dict["lastMessage"] = chat_messages[-1].data if len(chat_messages) > 0 else ""
            chats.append(chat_dict)
        return jsonify({"chats": [chat for chat in chats]})
