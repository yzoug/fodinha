from app import db
from datetime import datetime

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("player.id"))
    value = db.Column(db.Integer)
    real_value = db.Column(db.Integer)
    color = db.Column(db.Integer)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    number_of_lives = db.Column(db.Integer)
    lobby_id = db.Column(db.Integer, db.ForeignKey("lobby.id"))
    cards = db.relationship("Card", backref="owner_id")
    current_guess = db.Column(db.Integer)
    current_wins = db.Column(db.Integer)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Lobby(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    gameturn = db.Column(db.Integer, default=0)
    turn = db.Column(db.Integer)
    players = db.relationship("Player", backref="lobby")
    current_dealer_id = db.Column(db.Integer, db.ForeignKey("player.player_id"))
    current_player_id = db.Column(db.Integer, db.ForeignKey("player.player_id"))
    beforemanilla = db.Column(db.Integer, db.ForeignKey('card.id'))
    number_of_turns = db.Column(db.Integer)
    turn_type = db.Column(db.Integer)
    current_win_value = db.Column(db.Integer, default=1)
    played_cards = db.relationship("Card", backref="lobby_id")

