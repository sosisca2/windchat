
from flask_wtf import FlaskForm
from wtforms import (StringField, EmailField, PasswordField,
                     SubmitField, BooleanField)
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    user_name = StringField("Тег пользователя", validators=[DataRequired()])
    name = StringField("Ваше имя", validators=[DataRequired()])
    surname = StringField("Ваша фамилия", description="По желанию")
    email = EmailField("Ваша почта", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])

    remember_me = BooleanField("Запомнить меня")

    submit = SubmitField("Зарегистрироваться")
