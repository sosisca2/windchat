
from flask import jsonify
from flask_restful import reqparse, abort, Resource
from data import db_session
from data.chats import Chats

post_parser = reqparse.RequestParser()
post_parser.add_argument("name", required=True)
post_parser.add_argument("messages", required=True)
post_parser.add_argument("users", required=True)

put_parser = reqparse.RequestParser()
put_parser.add_argument("name")
put_parser.add_argument("message")
put_parser.add_argument("user")


class ChatsResource(Resource):
    def get(self, chat_id):
        db_sess = db_session.create_session()
        chat = db_sess.get(Chats, chat_id)
        db_sess.close()
        return jsonify(chat.to_dict())

    def put(self, chat_id):
        args = put_parser.parse_args()

        db_sess = db_session.create_session()
        db_sess.query(Chats).filter(chat_id).update({
            Chats.name: args[0] if args[0] else Chats.name,
            Chats.messages: args[1] if args[1] else Chats.messages,
            Chats.users: args[2] if args[2] else Chats.users,
        })
        db_sess.commit()

        return jsonify({"updated_chat": chat_id})


class ChatsListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        chats = db_sess.query(Chats).all()
        db_sess.close()
        return jsonify({"chats": [item.to_dict() for item in chats]})

    def post(self):
        args = post_parser.parse_args()
        db_sess = db_session.create_session()
        chat = Chats(
            name=args["name"],
            messages=args["messages"],
            users=args["users"]
        )
        db_sess.add(chat)
        db_sess.commit()

        return jsonify({"id": chat.id})
