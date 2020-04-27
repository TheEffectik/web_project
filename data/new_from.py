from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Что хотите продать')
    content = TextAreaField("Описание", validators=[DataRequired()])
    count = StringField('Цена')
    submit = SubmitField('Применить')
