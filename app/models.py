from app import db
from datetime import datetime

played_cards_in_lobbies = db.Table('played_cards_in_lobbies',
        db.Model.metadata,
        db.Column('card_id', db.Integer, db.ForeignKey('card.id')),
        db.Column('lobby_id', db.Integer, db.ForeignKey('lobby.id'))
    )

class Card(db.Model):
    # id
    id = db.Column(db.Integer, primary_key=True)

    # data
    value = db.Column(db.Integer, nullable=False)
    real_value = db.Column(db.Integer, nullable=False)
    color = db.Column(db.Integer, nullable=False)
    image_name = db.Column(db.String(50), nullable=False)

    # foreign keys
    # many to one
    owner = db.relationship("Player", back_populates="cards")
    owner_id = db.Column(db.Integer, db.ForeignKey("player.id"))

class Player(db.Model):
    # id
    id = db.Column(db.Integer, primary_key=True)

    # data
    name = db.Column(db.String(50), nullable=False)
    number_of_lives = db.Column(db.Integer, nullable=False)
    current_guess = db.Column(db.Integer)
    current_wins = db.Column(db.Integer)
    is_playing = db.Column(db.Boolean)
    is_dealer = db.Column(db.Boolean)

    # foreign keys
    # many to one
    lobby = db.relationship("Lobby", back_populates="players")
    lobby_id = db.Column(db.Integer, db.ForeignKey("lobby.id"))
    # one to many
    cards = db.relationship("Card", back_populates="owner")

class Lobby(db.Model):
    # id
    id = db.Column(db.Integer, primary_key=True)

    # data
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    gameturn = db.Column(db.Integer, default=0)
    turn = db.Column(db.Integer)
    number_of_turns = db.Column(db.Integer)
    turn_type = db.Column(db.Integer)
    current_win_value = db.Column(db.Integer, default=1)

    # foreign keys
    # one to many
    players = db.relationship("Player", back_populates="lobby")
    # many to one
    beforemanilla = db.Column(db.Integer, db.ForeignKey("card.id"))
    before_manilla = db.relationship("Card")
    before_manilla_id = db.Column(db.Integer, db.ForeignKey("lobby.id"))
    # many to many
    played_cards = db.relationship("Card", secondary=played_cards_in_lobbies)

