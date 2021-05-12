from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FileField, SubmitField
from wtforms.fields.html5 import IntegerField

#Описание полей формы создания товара

class CreateForm(FlaskForm):
    img = FileField('Изображение')
    price = IntegerField('Цена')
    desc = StringField('Описание')
    in_stock = BooleanField('На складе')
    submit = SubmitField('Добавить товар')

