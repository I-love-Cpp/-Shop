import os

from flask import Flask, request, redirect, abort
from flask import render_template
from flask_login import LoginManager, logout_user, login_required, login_user, \
    current_user
from werkzeug.utils import secure_filename

from data import db_session
from data.order import Order
from data.products import Product
from data.users import User
from forms.product import CreateForm
from forms.user import RegisterForm, LoginForm

# Путь к файлу, куда будут загружаться изображения пользователей
UPLOAD_FOLDER = r"Магазин-Shop-(Marce-One)/static/uploads/"

# Параметры запуска
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

db_session.global_init("db/Shop.db")

login_manager = LoginManager()
login_manager.init_app(app)


# Загрузка пользователя
@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


# Удаляем продукт
@app.route('/product_delete/<id>')
def delete(id):
    db_sess = db_session.create_session()
    # Находим что нужно удалить
    prds = db_sess.query(Product).filter(Product.id == id,
                                         Product.user_id == current_user.id
                                         ).first()
    # Если найдено, удаляем. Иначе нет
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
        # Получаем название файла, загруженным пользователем
        file = request.files['fl']
        filename = secure_filename(file.filename)
        # Если файл был загружен, сохраняем его, иначе ставим стандартное изображение
        if filename:
            file.save(
                os.path.join(app.config['UPLOAD_FOLDER'].strip(), filename))
            product.img = "static/uploads/" + filename
        else:
            product.img = "static/uploads/" + 'none_image.png'
        # Загружаем данные из формы
        product.price = form.price.data
        product.desc = form.desc.data
        product.in_stock = form.in_stock.data
        product.user_id = current_user.id
        # Загружаем данные в базу данных
        current_user.product.append(product)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect("/")
    return render_template('product.html', title='Добавление товара',
                           form=form)


@app.route('/edit_product/<id>', methods=['GET', 'POST'])
def edit(id):
    form = CreateForm()
    # Если форма только запустилась, то отдаём даные, иначе меняем их
    if request.method == 'GET':
        # Забираем объект из базы данных
        db_sess = db_session.create_session()
        prds = db_sess.query(Product).filter(Product.id == id,
                                             Product.user_id == current_user.id
                                             ).first()
        # Если он есть, загружаем его данные в форму, иначе выдаём ошибку 404
        if prds:
            form.price.data = prds.price
            form.desc.data = prds.desc
            form.in_stock.data = prds.in_stock
        else:
            abort(404)
    # Если форма заполнена и отправилась выполняем это условие
    elif form.validate_on_submit:
        # Забираем старый продукт из бд
        db_sess = db_session.create_session()
        product = db_sess.query(Product).filter(Product.id == id,
                                                Product.user_id == current_user.id
                                                ).first()
        # Если он есть меняем его данные, иначе 404
        if product:
            # Доста  м имя файла который загрузил пользователь
            file = request.files['fl']
            filename = secure_filename(file.filename)
            # Если фавйл загружен, сохраняем его, иначе оставляем старый
            if filename:
                file.save(
                    os.path.join(app.config['UPLOAD_FOLDER'].strip(), filename))
                product.img = "static/uploads/" + filename
            # Меняем остальные данный
            product.price = form.price.data
            product.desc = form.desc.data
            product.in_stock = form.in_stock.data
            product.user_id = current_user.id
            # Сохраняем в бд
            db_sess.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('product.html', title='Добавление товара',
                           form=form)


@app.route('/', methods=['GET', 'POST'])
def default():
    # Забираем запрос из поисковой строки
    req = ''
    if request.method == 'POST':
        req = ''.join(request.form['req'].split()).lower()
    # Список для продуктов, которые будут выведены
    products = []
    # Список для строчных индексов, которые будут использоваться для обработки html формой
    str_indexes = []
    db_session.global_init("db/Shop.db")
    db_sess = db_session.create_session()
    for prd in db_sess.query(Product).all():
        # Если описание товара удовлетворяет запросу, добавляем его в список
        if req in ''.join(prd.desc.split()).lower():
            products.append(prd)
            str_indexes.append(str(prd.id))
    return render_template('index.html', prds=products, size=len(products),
                           str_indexes=str_indexes, add_find=True,
                           head='Товары по заданным категориям', sum=0)


@app.route('/add_order', methods=["GET", "POST"])
def add_order():
    db_session.global_init("db/Shop.db")
    db_sess = db_session.create_session()
    for elem in current_user.basket.split('||'):
        if elem != '':
            order = Order()
            order.from_user = current_user.id
            order.product = elem
            prd = db_sess.query(Product).filter(Product.id == elem).first()
            order.to_user = prd.user_id
            db_sess.add(order)
    current_user.basket = ""
    db_sess.merge(current_user)
    db_sess.commit()
    return redirect('/user_basket')


# То, что заказал пользователь
@app.route('/user_orders', methods=["GET", "POST"])
def user_orders():
    db_session.global_init("db/Shop.db")
    db_sess = db_session.create_session()
    orders = []
    for elem in db_sess.query(Order).filter(Order.from_user == current_user.id):
        product = db_sess.query(Product).filter(
            Product.id == elem.product).first()
        fr = db_sess.query(User).filter(User.id == elem.to_user).first()
        if product:
            orders.append([fr, product, elem.id])
    return render_template('orders.html', orders=orders)


@app.route('/user_sells', methods=["GET", "POST"])
def user_sells():
    db_session.global_init("db/Shop.db")
    db_sess = db_session.create_session()
    orders = []
    for elem in db_sess.query(Order).filter(Order.to_user == current_user.id):
        product = db_sess.query(Product).filter(
            Product.id == elem.product).first()
        fr = db_sess.query(User).filter(User.id == elem.from_user).first()
        if product:
            orders.append([fr, product, elem.id])
    return render_template('sells.html', orders=orders)


# обработка удаление заказа или запроса на покупку
@app.route('/delp/<id>', methods=['GET', 'POST'])
def delp(id):
    # устанавливаем соединение с базой данных
    db_session.global_init('db/Shop.db')
    db_sess = db_session.create_session()
    # ищем товар для удаления
    to_del = db_sess.query(Order).filter(Order.id == id).first()
    db_sess.delete(to_del)
    db_sess.commit()
    return redirect('/user_orders')


# корзина пользователя
@app.route('/user_basket', methods=['GET', 'POST'])
def user_basket():
    # Список для товаров которые есть в еорзине
    need_find = []
    # Получаем id товаров, которые есть в корзине
    if current_user.basket:
        need_find = current_user.basket.split('||')
    # Список для продуктов, которые будут выведены
    products = []
    # Список для строчных индексов, которые будут использоваться для обработки html формой
    str_indexes = []
    # Сумма стоимости всех товаров
    sum = 0
    db_session.global_init("db/Sho"
                           "p.db")
    db_sess = db_session.create_session()
    for prd in db_sess.query(Product).all():
        # Если id товара есть в корзине, добавляем его
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
    # Добавляем в строку товаров новый id
    if current_user.basket:
        current_user.basket += '||' + id
    else:
        current_user.basket = id
    # Меняем данные в бд
    db_sess.merge(current_user)
    db_sess.commit()
    print(current_user.basket)
    return redirect('/')


@app.route('/dlbasket/<id>', methods=['GET', 'POST'])
def dlbasket(id):
    db_sess = db_session.create_session()
    # Новая корзины
    new_basket = []
    # Разбиваем строку старой корзины и пробегаемся по всем эллементам.
    # Не добавляем товар, который нужно убрать из корзины
    for elem in current_user.basket.split('||'):
        if elem != str(id):
            new_basket.append(elem)
    # Изменяем строку корзину в бд
    current_user.basket = '||'.join(new_basket)
    db_sess.merge(current_user)
    db_sess.commit()
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    # Если нажата кнопка "Выйти из аккаунта", выходим
    logout_user()
    return redirect("/")


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    # Загружаем форму
    form = RegisterForm()
    if form.validate_on_submit():
        # Если нажата кнопка отправки, загружаем данние в бд

        # Загрузка всех данных
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        # Создайм объект класса User с данными, полуенными из формы
        user = User(
            name=form.name.data,
            email=form.email.data,
            surname=form.surname.data,
            age=form.age.data,
            address=form.age.data,
        )
        user.set_password(form.password.data)
        # Добавляем данные в бд
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Загружаем форму логина
    form = LoginForm()
    # Если нажата кнопка отправить
    if form.validate_on_submit():
        # Проверяем корректность данных
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
    app.run(host='127.0.0.1', port=8080, debug=True)
