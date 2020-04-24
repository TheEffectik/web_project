from django.shortcuts import redirect
from flask import Flask, make_response, request, session, render_template, abort, jsonify, url_for, send_from_directory, \
    flash
import os
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
from data import news_api, user_api
import random




db_session.global_init("db/users.sqlite")
app = Flask(__name__)

app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=365)

login_manager = LoginManager()
login_manager.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = NewsForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        news = News()
        news.title = form.title.data
        news.content = form.content.data
        current_user.news.append(news)
        session.merge(current_user)
        session.commit()
        return redirect('/')
    session = db_session.create_session()
    news = session.query(News)[::-1]

    return render_template('index.html', news=news, title='МаринОЧКА', form=form)


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
def login_2(mail):
    a = ''
    for i in range(5):
        a += str(random.randint(0, 9))
    print(a)
    form = psw()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('login_2.html', title='Авторизация', form=form)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
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
        if session.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такое имя уже занято")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)



@app.route('/user/<nickname>', methods=['GET', 'POST'])
@login_required
def user(nickname):

    session = db_session.create_session()
    news = session.query(News)[::-1]
    return render_template('news.html', title=nickname, news=news)

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


'''def main():
    app.register_blueprint(user_api.blueprint)
    app.register_blueprint(news_api.blueprint)
    app.run()'''


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)