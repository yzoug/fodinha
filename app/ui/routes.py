from app import app
from app.ui import bp
from flask import render_template

@bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@bp.route('/lobby', methods=['GET'])
def lobby():
    return render_template('lobby.html')

@bp.route("/lobby/add", methods=["POST"])
def add_lobby():
    if len(lobbies) > 3:
        # for now only allowing three simultaneous lobbies
        flash('Já foram criados 3 jogos')
        return redirect(url_for('ui.index'))

    lobby_id = len(lobbies)
    req_nb_players = request.form.get('nb_players')
    try:
        nb_players = int(escape(req_nb_players))
    except ValueError:
        print('[E] can\'t convert to int: {}'.format(req_nb_players))
        abort(400)

    lobbies.append(Lobby(lobby_id, nb_players))
    print('[I] new lobby created: {} players, of ID {}'.format(nb_players, lobby_id))

    return redirect(url_for('ui.lobby'))

@bp.route("/lobby/join", methods=["POST"])
def join_lobby():
    req_name = request.form.get('name')
    req_nb_players = request.form.get('nb_players')

