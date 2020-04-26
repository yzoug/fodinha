from app import app
from uuid import uuid4
from app.api import api_bp
from flask import Flask, render_template, json, request, session, abort, Response
from fodinha import Lobby, TurnType
from markupsafe import escape

lobbies = []

@api_bp.route("/lobby/add", methods=["POST"])
def add_lobby():
    if len(lobbies) > 3:
        # for now only allowing three simultaneous lobbies
        abort(403)

    lobby_id = len(lobbies)
    req_nb_players = request.form.get('nb_players')
    try:
        nb_players = int(escape(req_nb_players))
    except ValueError:
        print('[E] can\'t convert to int: {}'.format(req_nb_players))
        abort(400)

    lobbies.append(Lobby(lobby_id, nb_players))
    print('[I] new lobby created: {} players, of ID {}'.format(nb_players, lobby_id))

    return Response(status=200)

@api_bp.route("/lobby/<req_lobby_id>/delete", methods=["POST"])
def del_lobby():
    """Deletes the lobby the player is registered in, if and only if he's the creator"""
    try:
        lobby_id = int(escape(req_lobby_id))
    except ValueError:
        print('[E: del_lobby] Value Error, can\'t convert lobby id {}'.format(req_lobby_id))
        abort(400)

    if session['lobby_id'] != lobby_id:
        print('[E: del_lobby] trying to delete lobby {} while being in lobby {}'.format(lobby_id, session['lobby_id']))
        abort(403)

    if not session['is_creator']:
        print('[E: del_lobby] trying to delete lobby {} while not being its creator'.format(lobby_id))
        abort(403)

    lobbies.pop(lobby_id)

    return Response(status=200)


# c'est là que je crée la session
# à part ce endpoint, je me base sur la session de l'utilisateur
# pour déterminer le lobby_id et le player_number
@api_bp.route("/lobby/<req_lobby_id>/register", methods=["POST"])
def register_player(req_lobby_id):
    # if trying to join a new lobby, clear session
    session.clear()

    name = escape(request.form.get('name'))
    if name is None:
        print('[E: register_player] No data is posted')
        abort(400)

    try:
        lobby_id = int(escape(req_lobby_id))
    except ValueError:
        print('[E: register_player] Value Error, can\'t convert lobby id {}'.format(req_lobby_id))
        abort(400)

    try:
        player_id = lobbies[lobby_id].register_player(name)
    except RuntimeError:
        print('[E: register_player] Runtime Error, can\'t register player to lobby {}'.format(lobby_id))
        abort(403)

    session['name'] = name
    session['lobby_id'] = lobby_id
    session['player_id'] = player_id
    session['is_creator'] = False
    print('[I] added player {} of ID {} to lobby n°{}'.format(name, player_id, lobby_id))

    if player_id == lobbies[lobby_id].number_of_players - 1:
        print('[I] all players have joined lobby {}, starting game'.format(lobby_id))
        lobbies[lobby_id].start_game()
    elif player_id == 0:
        session['is_creator'] = True

    return Response(status=200)

@api_bp.route('/lobby/status', methods=["GET"])
def get_status():
    """Returns the status of the current game"""
    if session['name'] == None or session['lobby_id'] == None or session['player_id'] == None:
        print('[E: list_players] corrupted session')
        abort(500)

    return lobbies[session['lobby_id']].status()


@api_bp.route('/players/list', methods=["GET"])
def list_players():
    if session['name'] == None or session['lobby_id'] == None or session['player_id'] == None:
        print('[E: list_players] corrupted session')
        abort(500)

    return lobbies[session['lobby_id']].get_players()

@api_bp.route('/players/cards', methods=["GET"])
def get_cards():
    """Get cards of a player"""
    if session['name'] == None or session['lobby_id'] == None or session['player_id'] == None:
        print('[E: list_players] corrupted session')
        abort(500)

    return lobbies[session['lobby_id']].get_cards(session['player_id'])


# for testing purposes
# only accessible for debug page
game = Lobby(1, 3)
# these all need to go in the api
game.register_player('pitoco')
game.register_player('formigas')
game.register_player('dog')
game.start_game()


@api_bp.route('/debug', methods = ['GET', 'POST'])
def debug():
    user = {'username': 'bruno'}
    if request.method == 'POST':
        data = request.form
        print("Received data: {}".format(data))
        if game.current_turn_type == TurnType.GUESS or game.current_turn_type == TurnType.FINAL_GUESS:
            game.guess(int(data.get('player_id')),int(data.get('choice')))
        elif game.current_turn_type == TurnType.PLAY or game.current_turn_type == TurnType.FINAL_PLAY:
            game.play(int(data.get('player_id')),int(data.get('choice')))
    game_status = str(game.status())
    return render_template('debug.html', title='Fodinha', user=user, game_status = game_status, current_player = user)

