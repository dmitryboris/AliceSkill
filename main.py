from flask import Flask, request
import logging
import json
from random import sample, choice, shuffle
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
            'text': ''
        }
    }
    handle_dialog(response, request.json)
    logging.info(f'Response: {response!r}')
    return json.dumps(response)


def handle_dialog(res, req):
    db_sess = db_session.create_session()
    user_id = req['session']['user']['user_id']
    user = db_sess.query(User).filter(User.yandex_id == user_id).first()
    if user:
        game = db_sess.query(Game).filter(Game.user_id == user.id).all()[-1]
        if game.end:
            game = None
    else:
        game = None

    # если сессия новая, то приветсвуем пользователя.
    if req['session']['new']:
        greeting(res, db_sess, user_id)
    else:
        if user and not game:
            # если сессия не новая, то знакомимся.
            acquaintance(req, res, db_sess, user)
            game = start_game(req, res, db_sess, user, game)
        if user and game:
            check_answer(req, res, db_sess, game)
            if res['response']['text'] == '' or res['response']['text'] == 'Верно. Следующий кадр.':
                continue_game(req, res, db_sess, user, game)
            else:
                end_game()

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


def acquaintance(req, res, db_sess, user):
    # если поле имени пустое, то это говорит о том,
    # что пользователь еще не представился.
    if user.name is None:
        # в последнем его сообщение ищем имя.
        first_name = get_first_name(req)
        # если не нашли, то сообщаем пользователю что не расслышали.
        if first_name is None:
            res['response']['text'] = 'Не расслышала имя. Повтори, пожалуйста!'
        # если нашли, то приветствуем пользователя.
        # и спрашиваем какой режим он хочет выбрать.
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


def start_game(req, res, db_sess, user, game):
    if req["request"]["command"] == "режим с подсказками" or \
            req["request"]["command"] == "режим без подсказок" and not game:
        game = Game()
        game.user_id = user.id
        game.answered = 0
        game.end = False
        if req["request"]["command"] == "режим с подсказками":
            game.hints = 3
        db_sess.add(game)
        db_sess.commit()
        return game


def continue_game(req, res, db_sess, user, game):
    frames_id = [frame.id for frame in db_sess.query(Frame).all()]
    previous_frames = [frame.id for frame in game.frames]
    diff = set(frames_id) - set(previous_frames)
    frame_id = choice(list(diff))
    frame = db_sess.query(Frame).filter(Frame.id == frame_id).first()
    game.frames.append(frame)
    movie = db_sess.query(Movie).filter(Movie.id == frame.film_id).first()
    movie_names = sample([movie.name for movie in db_sess.query(Movie).all()], 4)
    if movie.name not in movie_names:
        movie_names.append(movie.name)
        movie_names.pop(0)
    shuffle(movie_names)
    db_sess.commit()

    res['response']['card'] = {}
    res['response']['card']['type'] = 'BigImage'
    res['response']['card']['image_id'] = frame_id
    if not res['response']['text']:
        res['response']['text'] = 'Как называется этот фильм?'
        res['response']['card']['title'] = 'Как называется этот фильм?'
    else:
        res['response']['card']['title'] = res['response']['text'] + ' Что это за фильм?'
    res['response']['buttons'] = [
        {"title": name,
         "hide": True}
        for name in movie_names]


def check_answer(req, res, db_sess, game):
    if game.frames:
        previous_frame = game.frames[-1]
        movie = db_sess.query(Movie).filter(Movie.id == previous_frame.film_id).first()
        if req["request"]["original_utterance"] == movie.name:
            res['response']['text'] = 'Верно. Следующий кадр.'
            game.answered += 1
        else:
            res['response']['text'] = 'Неверно. Похоже ты проиграл.'
            game.end = True

        if game.answered == 5:
            game.end = True
            game.user.rating += game.answered + 3
            res['response']['text'] = 'Мои поздравления. Это победа'
        db_sess.commit()


def end_game():
    pass


if __name__ == '__main__':
    db_session.global_init("db/alice.db")
    app.run()
