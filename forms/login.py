
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField,
                     SubmitField, BooleanField)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    user_name = StringField("Тег пользователя", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])

    remember_me = BooleanField("Запомнить меня")

    submit = SubmitField("Войти")
