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
    try:
        game = user.game[-1]
        if game.end:
            game = None
    except IndexError:
        game = None
    except AttributeError:
        game = None

    # если сессия новая, то приветсвуем пользователя.
    if req['session']['new']:
        greeting(res, db_sess, user_id, game)
    else:
        top_users(req, res, db_sess, user)
        if user and not game:
            # если сессия не новая, то знакомимся и начинаем игру.
            acquaintance(req, res, db_sess, user)
            game = start_game(req, db_sess, user, game)
        if user and game:
            old = check_old_game(req, res, db_sess, game)
            if not old:
                check_answer(req, res, db_sess, game)
                if game.end:
                    end_game(res, db_sess, game)
                else:
                    continue_game(res, db_sess, game)

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


# приветствуем пользователя
def greeting(res, db_sess, user_id, game):
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
             "hide": True},
            {"title": "Топ пользователей",
             "hide": True}
        ]

    if user and user.name and game:
        res['response']['text'] = f'Привет, {user.name}! Похоже ты не доиграл предыдущую игру. Хочешь продолжить?'
        # получаем варианты buttons
        res['response']['buttons'] = [
            {"title": "Да, хочу продолжить",
             "hide": True},
            {"title": "Нет, хочу начать новую",
             "hide": True}
        ]


# знакомство с пользователем
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
                 "hide": True},
                {"title": "Топ пользователей",
                 "hide": True}
            ]


def start_game(req, db_sess, user, game):
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


# выбираем кадр и создаем кнопки для ответа
def continue_game(res, db_sess, game):
    if res["response"]["text"].startswith("Главный"):
        frame = game.frames[-1]
    else:
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
    res['response']['card']['image_id'] = frame.id
    if not res['response']['text']:
        res['response']['text'] = 'Как называется этот фильм?'
        res['response']['card']['title'] = 'Как называется этот фильм?'
    else:
        res['response']['card']['title'] = res['response']['text'] + ' Что это за фильм?'
    res['response']['buttons'] = [
        {"title": name,
         "hide": True}
        for name in movie_names]
    if game.hints:
        res['response']['buttons'].append({"title": "Подсказка",
                                           "hide": True})


# проверка ответа
def check_answer(req, res, db_sess, game):
    if game.frames and not game.end:
        previous_frame = game.frames[-1]
        movie = db_sess.query(Movie).filter(Movie.id == previous_frame.film_id).first()
        if req["request"]["original_utterance"].lower() == movie.name.lower():
            res['response']['text'] = 'Верно. Следующий кадр.'
            game.answered += 1
        elif req["request"]["command"] == "подсказка" and game.hints:
            res["response"]["text"] = f"Главный герой этого фильма - {movie.character}."
            game.hints -= 1
        elif req["request"]["command"] == "подсказка" and not game.hints:
            res["response"]["text"] = "У тебя больше нет подсказок"
        else:
            res["response"]["text"] = "Неверно."
            game.end = True

        if game.answered == 5:
            game.end = True
        db_sess.commit()


# окончание игры
def end_game(res, db_sess, game):
    if game.answered == 5:
        res['response']['text'] = 'Мои поздравления. Это победа. Хочешь сыграть ещё?'
        game.user.rating += 3
    else:
        if res['response']['text']:
            res['response']['text'] += " Похоже ты проиграл. Ничего страшного, хочешь сыграть ещё?"
        else:
            res['response']['text'] = "Похоже ты проиграл. Ничего страшного, хочешь сыграть ещё?"
    game.user.rating += game.answered
    res['response']['buttons'] = [
        {"title": "Режим с подсказками",
         "hide": True},
        {"title": "Режим без подсказок",
         "hide": True},
        {"title": "Топ пользователей",
         "hide": True}
    ]
    db_sess.commit()


# проверка будет ли пользователь продолжать старую игру
def check_old_game(req, res, db_sess, game):
    old = None
    if req["request"]["command"] == "да хочу продолжить":
        old = True
        previous_frame = game.frames[-1]
        movie = db_sess.query(Movie).filter(Movie.id == previous_frame.film_id).first()
        movie_names = sample([movie.name for movie in db_sess.query(Movie).all()], 4)
        if movie.name not in movie_names:
            movie_names.append(movie.name)
            movie_names.pop(0)
        shuffle(movie_names)

        res['response']['card'] = {}
        res['response']['card']['type'] = 'BigImage'
        res['response']['card']['image_id'] = previous_frame.id
        res['response']['text'] = 'Это кадр из фильма, который ты в прошлый раз не назвал.' + \
                                  ' Как называется этот фильм?'
        res['response']['card']['title'] = 'Это кадр из фильма, который ты в прошлый раз не назвал.' + \
                                           ' Как называется этот фильм?'
        res['response']['buttons'] = [
            {"title": name,
             "hide": True}
            for name in movie_names]
    elif req["request"]["command"] == "нет хочу начать новую":
        old = None
        game.end = True
        db_sess.commit()
    return old


def top_users(req, res, db_sess, user):
    if req["request"]["command"] == "топ пользователей":
        top = db_sess.query(User).order_by(User.rating)[:10]
        text = 'Каждый правльный ответ даёт 1 очко, выигранная игра даёт 3. \n' + \
               'Топ пользователей:' + '\n'
        for key, i in enumerate(top):
            text += str(key + 1) + '. ' + i.__repr__() + '\n'
        text += '\n' + '\n' + 'Твоя статистика: ' + user.__repr__()

        res['response']['text'] = text
        res['response']['buttons'] = [
            {"title": "Режим с подсказками",
             "hide": True},
            {"title": "Режим без подсказок",
             "hide": True}
        ]


if __name__ == '__main__':
    db_session.global_init("db/alice.db")
    app.run()
