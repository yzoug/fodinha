from app import app
from uuid import uuid4
from app.api import api_bp
from flask import Flask, render_template, json, request, session, abort
from fodinha import Lobby, TurnType

lobbies = []

@api_bp.route("/lobby/add", methods=["POST"])
def add_lobby():
    if len(lobbies) > 3:
        # for now only allowing three simultaneous lobbies
        abort(403)

    lobby_id = len(lobbies)
    req_nb_players = request.form.get('nb_players')
    try:
        nb_players = int(req_nb_players))
    except ValueError:
        print('[E] can\'t convert to int: {}'.format(req_nb_players))
        abort(400)

    lobbies.append(Lobby(lobby_id, nb_players))
    print('[I] new lobby created: {} players, of ID {}'.format(nb_players, lobby_id))
    resp = {'lobby_id': lobby_id}

    return resp

# c'est là que je crée la session
# à part ce endpoint, je me base sur la session de l'utilisateur
# pour déterminer le lobby_id et le player_number
@api_bp.route("/<lobby_id>/register", methods=["POST"])
def register_player(lobby_id):
    name = str(request.form.get('name'))
    try:
        player_id = lobbies[lobby_id].register_player(name)
    except:
        #TODO



#@api_bp.route("/lobby/del", methods=["POST", "GET"])
#def del_lobby():
#    if request.method == "POST":
#        req_data = request.get_json()
#
#        lobby_to_delete_index = req_data['lobby_id']
#
#    print('Lobby to delete :', lobby_to_delete_index)
#    # # lobby indexes start at 1
#    # real_index = str(int(lobby_to_delete_index) + 1)
#
#    for lobby in lobbies:
#        if lobby.lobby_id == lobby_to_delete_index:
#            lobbies.pop(lobbies.index(lobby))
#
#    print('lobbies :')
#    for lobby in lobbies:
#        print('lobby' + lobby.lobby_id)
#
#    return 'success'


@api_bp.route('/players/list', methods=["GET"])
def list_players():
    # Api returns lobby info
    myPlayers = ['djed','zoug', 'max','ididd','djdj']
    return json.dumps(myPlayers)

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

