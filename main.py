import os

from flask import Flask, request, redirect, abort
from flask import render_template
from flask_login import LoginManager, logout_user, login_required, login_user, \
    current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.products import Product
from data.users import User
from forms.product import CreateForm
from forms.user import RegisterForm, LoginForm

UPLOAD_FOLDER = r"d:/Sources/Магазин-Shop-(Marce-One)/static/uploads/"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

db_session.global_init("db/Shop.db")

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/product_delete/<id>')
def delete(id):
    db_sess = db_session.create_session()
    prds = db_sess.query(Product).filter(Product.id == id,
                                         Product.user_id == current_user.id
                                         ).first()
    if prds:
        db_sess.delete(prds)
        db_sess.commit()
    else:
        abort(404)
    return redirect('/')


# обработка формы добавления продукта
@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form = CreateForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        product = Product()

        file = request.files['fl']
        filename = secure_filename(file.filename)
        if filename:
            file.save(
                os.path.join(app.config['UPLOAD_FOLDER'].strip(), filename))
            product.img = "static/uploads/" + filename
        else:
            product.img = "static/uploads/" + 'none_image.png'
        product.price = form.price.data
        product.desc = form.desc.data
        product.in_stock = form.in_stock.data
        product.user_id = current_user.id
        current_user.product.append(product)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect("/")
    return render_template('product.html', title='Добавление товара',
                           form=form)


@app.route('/edit_product/<id>', methods=['GET', 'POST'])
def edit(id):
    form = CreateForm()
    if request.method == 'GET':
        db_sess = db_session.create_session()
        prds = db_sess.query(Product).filter(Product.id == id,
                                             Product.user_id == current_user.id
                                             ).first()
        if prds:
            form.price.data = prds.price
            form.desc.data = prds.desc
            form.in_stock.data = prds.in_stock
        else:
            abort(404)
    elif form.validate_on_submit:
        db_sess = db_session.create_session()
        product = db_sess.query(Product).filter(Product.id == id,
                                                Product.user_id == current_user.id
                                                ).first()
        if product:
            file = request.files['fl']
            filename = secure_filename(file.filename)
            if filename:
                file.save(
                    os.path.join(app.config['UPLOAD_FOLDER'].strip(), filename))
                product.img = "static/uploads/" + filename
            product.price = form.price.data
            product.desc = form.desc.data
            product.in_stock = form.in_stock.data
            product.user_id = current_user.id
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('product.html', title='Добавление товара',
                           form=form)


@app.route('/', methods=['GET', 'POST'])
def default():
    req = ''
    if request.method == 'POST':
        req = request.form['req'].lower()
    products = []
    str_indexes = []
    db_session.global_init("db/Shop.db")
    db_sess = db_session.create_session()
    for prd in db_sess.query(Product).all():
        if req in prd.desc.lower():
            products.append(prd)
            str_indexes.append(str(prd.id))
    return render_template('index.html', prds=products, size=len(products),
                           str_indexes=str_indexes, add_find=True,
                           head='Товары по заданным категориям', sum=0)


# корзина пользователя
@app.route('/user_basket', methods=['GET', 'POST'])
def user_basket():
    need_find = current_user.basket.split('||')
    products = []
    str_indexes = []
    sum = 0
    db_session.global_init("db/Shop.db")
    db_sess = db_session.create_session()
    for prd in db_sess.query(Product).all():
        if str(prd.id) in need_find:
            products.append(prd)
            str_indexes.append(str(prd.id))
            sum += prd.price
    return render_template('index.html', prds=products, size=len(products),
                           str_indexes=str_indexes, add_find=False,
                           head_name=True, head='Товары из вашей корзины',
                           sum=sum)


# добавление в корзину
@app.route('/basket/<id>', methods=['GET', 'POST'])
def basket(id):
    db_sess = db_session.create_session()
    if current_user.basket:
        current_user.basket += '||' + id
    else:
        current_user.basket = id
    db_sess.merge(current_user)
    db_sess.commit()
    print(current_user.basket)
    return redirect('/')


@app.route('/dlbasket/<id>', methods=['GET', 'POST'])
def dlbasket(id):
    db_sess = db_session.create_session()
    new_basket = []
    for elem in current_user.basket.split('||'):
        if elem != str(id):
            new_basket.append(elem)
    current_user.basket = '||'.join(new_basket)
    db_sess.merge(current_user)
    db_sess.commit()
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data,
            age=form.age.data,
            address=form.age.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


if __name__ == "__main__":
    app.run(host="127.0.0.3", port=8080, debug=True)
