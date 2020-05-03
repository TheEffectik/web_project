import flask
from django.shortcuts import redirect
from flask import Flask, make_response, request, session, render_template, abort, jsonify, url_for, send_from_directory, \
    flash
import os
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
from datetime import datetime
from mediawiki import MediaWiki
from flask_login import LoginManager, login_user, current_user, login_required, logout_user
from data import db_session
from data.users import User
from data.new_from import NewsForm
import datetime
from werkzeug.utils import redirect
from loginform import LoginForm, psw
from registerform import RegisterForm
from data.news import News
from flask_restful import reqparse, abort, Api, Resource
from flask_socketio import SocketIO
from data import news_api, user_api
import random
from PIL import Image
from werkzeug.utils import secure_filename


db_session.global_init("db/users.sqlite")
app = Flask(__name__)

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)

login_manager = LoginManager()
login_manager.init_app(app)
social_networks = ['https://vk.com']


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    global visits_count
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        news.count = form.count.data
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(session.query(News)[-1].id + 1)) + filename[-4:])
            news.filename = '/static/img/' + str(session.query(News)[-1].id + 1) + str(filename[-4:])
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    session = db_session.create_session()
    news = session.query(News)[::-1]
    visits_count = int(request.cookies.get("index", 0))
    if visits_count:
        res = make_response(render_template('index.html', news=news, title='Маринчка', form=form))
        res.set_cookie("index", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response(render_template('about_us.html', news=news, title='Маринчка', form=form))
        res.set_cookie("index", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 365 * 2)
    return res

@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/login_2', methods=['GET', 'POST'])
def login_2():
    a = ''
    for i in range(5):
        a += str(random.randint(0, 9))
    print(a)
    form = psw()
    if form.validate_on_submit():
        if str(request.form['psw']) == a:
            session = db_session.create_session()
            print(user)
            session.add(user)
            session.commit()
        else:
            return render_template('login_2.html', title='Авторизация', form=form, message='Неверный код')
    return render_template('login_2.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    global social_networks
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой адрес почты уже занят")
        if form.about.data[:14] not in social_networks:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Вроде нет такой соц сети")
        if session.query(User).filter(User.about == form.about.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                    message="Аккаунт с данной соц сетью существует")
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такое имя уже занято")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login_2')
    return render_template('register.html', title='Регистрация', form=form)



@login_required
@app.route('/user/<nickname>', methods=['GET', 'POST'])
def user(nickname):
    if request.method == 'GET':
        session = db_session.create_session()
        news = session.query(News)[::-1]
        return render_template('user.html', title=nickname, news=news)
    elif request.method == 'POST':
        print('sdsdsd')
        vk(request.form['about'])

def vk(message):
    print('bruh')
    vk_session = vk_api.VkApi(
        token='46ee90b460cc009558a9acd1e04ca649ce10b2ec550e9c52418d47beca68909c49bd72fefffd2d9daf5fd')

    longpoll = VkBotLongPoll(vk_session, 193282564)
    vk = vk_session.get_api()
    vk.messages.send(user_id=226460410,
                    message=f"{message}",
                    random_id=random.randint(0, 2 ** 64))


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == "GET":
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          (News.user == current_user) |
                                          (current_user.id == 1)).first()
        if news:
            form.title.data = news.title
            form.content.data = news.content
            form.count.data = news.count
            form.count.filename = news.filename
        else:
            abort(404)
    if form.validate_on_submit():
        session = db_session.create_session()
        news = session.query(News).filter(News.id == id,
                                          (News.user == current_user) |
                                          (current_user.id == 1)).first()
        if news:
            news.title = form.title.data
            news.content = form.content.data
            form.count = form.count.data
            form.filename = form.filename.data
            session.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)

@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    session = db_session.create_session()
    news = session.query(News).filter(News.id == id,
                                      (News.user == current_user) |
                                      (current_user.id == 1)).first()
    if news:
        session.delete(news)
        session.commit()
    else:
        abort(404)
    return redirect('/')

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')