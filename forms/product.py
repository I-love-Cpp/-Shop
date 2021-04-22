from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, FileField, SubmitField
from wtforms.fields.html5 import IntegerField

#Описание полей формы создания товара

class CreateForm(FlaskForm):
    img = FileField('image')
    price = IntegerField('price')
    desc = StringField('desc')
    in_stock = BooleanField('in_stock')
    submit = SubmitField('Add product')

