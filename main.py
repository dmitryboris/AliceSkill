from flask import Flask, request
import logging
import json
import random
from data import db_session
from data.user import User
from data.game import Game
from data.movie import Movie
from data.frame import Frame

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

logging.basicConfig(filename='logs/logging.log')


@app.route('/post', methods=['POST'])
def main():
    logging.info(f'Request: {request.json!r}')
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False,
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    db_sess = db_session.create_session()
    user_id = req['session']['user']['user_id']
    user = db_sess.query(User).filter(User.yandex_id == user_id).first()

    # если сессия новая, то приветсвуем пользователя.
    if req['session']['new']:
        greeting(res, db_sess, user_id)
    else:
        # если сессия не новая, то знакомимся.
        acquaintance(req, res, db_sess, user_id)
        start_game(req, res, db_sess, user_id)
        continue_game(req, res, db_sess, user_id)

    return res


def get_first_name(req):
    # перебираем сущности
    for entity in req['request']['nlu']['entities']:
        # находим сущность с типом 'YANDEX.FIO'
        if entity['type'] == 'YANDEX.FIO':
            # Если есть сущность с ключом 'first_name',
            # то возвращаем ее значение.
            # Во всех остальных случаях возвращаем None.
            return entity['value'].get('first_name', None)


def new_user(db_sess, user_id):
    user = User()
    user.yandex_id = user_id
    user.name = None
    db_sess.add(user)
    db_sess.commit()


def greeting(res, db_sess, user_id):
    user = db_sess.query(User).filter(User.yandex_id == user_id).first()

    if not user:
        res['response']['text'] = 'Привет! Назови свое имя!'
        # создаем в БД нового пользователя
        new_user(db_sess, user_id)
        return

    elif user and not user.name:
        res['response']['text'] = 'Привет! Мы не познакомились в прошлый раз. Назови свое имя'

    if user and user.name:
        res['response']['text'] = f'Привет, {user.name}! Какой режим хочешь выбрать?'
        # получаем варианты buttons
        res['response']['buttons'] = [
            {"title": "Режим с подсказками",
             "hide": True},
            {"title": "Режим без подсказок",
             "hide": True}
        ]


def acquaintance(req, res, db_sess, user_id):
    user = db_sess.query(User).filter(User.yandex_id == user_id).first()

    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if user.name is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # И спрашиваем какой режим он хочет выбрать.
        else:
            user.name = first_name.title()
            db_sess.commit()
            res['response']['text'] = 'Приятно познакомиться, ' \
                                      + first_name.title() \
                                      + '. Я - бот "Угадай кино по картинке". Какой режим хочешь выбрать?'
            # получаем варианты buttons
            res['response']['buttons'] = [
                {"title": "Режим с подсказками",
                 "hide": True},
                {"title": "Режим без подсказок",
                 "hide": True}
            ]


def start_game(req, res, db_sess, user_id):
    if req["request"]["command"] == "режим с подсказками" or req["request"]["command"] == "режим без подсказок":
        user = db_sess.query(User).filter(User.yandex_id == user_id).first()
        game = Game()
        game.user_id = user.id
        if req["request"]["command"] == "режим с подсказками":
            game.hints = 3
        db_sess.add(game)
        db_sess.commit()


def continue_game(req, res, db_sess, user_id):
    user = db_sess.query(User).filter(User.yandex_id == user_id).first()
    game = db_sess.query(Game).filter(Game.user_id == user.id).first()
    if game:
        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['title'] = 'Как называется этот фильм'
        frames_id = [frame.id for frame in db_sess.query(Frame).all()]
        res['response']['card']['image_id'] = random.choice(frames_id)
        res['response']['text'] = 'Как называется этот фильм'
        res['response']['buttons'] = [
            {"title": "xи",
             "hide": True},
            {"title": "xк",
             "hide": True}
        ]


if __name__ == '__main__':
    db_session.global_init("db/alice.db")
    app.run()
