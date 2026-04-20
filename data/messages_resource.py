
from flask import jsonify, abort
from flask_restful import reqparse, Resource
from data import db_session
from data.messages import Messages

from datetime import datetime

list_parser = reqparse.RequestParser()
list_parser.add_argument("chat_id", required=True)
list_parser.add_argument("owner", required=True)
list_parser.add_argument("data", required=True)


def abort_if_msg_not_found(msg_id):
    db_sess = db_session.create_session()
    if not db_sess.get(Messages, msg_id):
        abort(404, message=f"Msg {msg_id} not found")


class MessagesResource(Resource):
    def get(self, msg_id):
        db_sess = db_session.create_session()
        msg = db_sess.get(Messages, msg_id)
        return jsonify(msg.to_dict())


class MessagesNewResource(Resource):
    def get(self, chat_id):
        db_sess = db_session.create_session()
        msgs = db_sess.query(Messages).filter(Messages.is_new, Messages.chat_id == chat_id).all()
        return jsonify({"messages": [msg.to_dict() for msg in msgs]})

    def post(self, chat_id):
        db_sess = db_session.create_session()
        db_sess.query(Messages).filter(Messages.chat_id == chat_id).update({Messages.is_new: 0})
        db_sess.commit()
        return jsonify({"answer:": "The status of the messages has been changed"})


class MessagesChatResource(Resource):
    def get(self, chat_id):
        db_sess = db_session.create_session()
        msgs = sorted(db_sess.query(Messages).filter(Messages.chat_id == chat_id).all(),
                      key=lambda msg: msg.time)
        return jsonify({"messages": [msg.to_dict() for msg in msgs]})


class MessagesListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        messages = db_sess.query(Messages).all()
        return jsonify({"messages": [item.to_dict() for item in messages]})

    def post(self):
        args = list_parser.parse_args()
        db_sess = db_session.create_session()

        msg = Messages(
            chat_id=args["chat_id"],
            owner=args["owner"],
            data=args["data"],
            time=datetime.now()
        )

        db_sess.add(msg)
        db_sess.commit()

        return jsonify({"newMessage": msg.to_dict(only=("id", "chat_id", "owner", "data", "time"))})
