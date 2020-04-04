#!/usr/bin/env python
import enum
import random

# TODO
# problèmes suivants relevés:
#

class Color(enum.IntEnum):
    """Represent a card color

    Manilla: colors are ranked from weakest to strongest
    """
    DIAMONDS = 1
    SPADES = 2
    HEARTS = 3
    CLUBS = 4


class TurnType(enum.Enum):
    """Represent a type of turn, either 'guess' or 'play'"""
    GUESS = enum.auto()
    PLAY = enum.auto()
    FINAL_GUESS = enum.auto()
    FINAL_PLAY = enum.auto()
    GAME_OVER = enum.auto()


class Card:
    """Represent a card: a value, color, owner_id

    Values:
    As = 1
    Jack = 11
    Queen = 12
    King = 13

    In Fodinha (ignoring the manilla) the strongest card is 2
    then it goes As, K, J, Q (careful, J stronger than Q), etc
    The real_value attribute reflects this:
    3 => 1
    4 => 2
    ...
    10 => 8
    J (=11) => 10
    Q (=12) => 9
    K (=13) => 11
    A (=1) => 12
    2 => 13
    """

    def __init__(self, v, c):
        # sanity checks
        if v not in range(1, 14):
            raise ValueError('Given value not in the [1;13] interval:', v)
        if not isinstance(c, Color):
            raise TypeError('Given color is not of type Color:', c)

        self.value = v
        self.color = c
        self.owner_id = None

        # set the real_value attribute, useful for comparing values
        if v > 2 and v <= 10:
            self.real_value = v - 2
        elif v == 11:
            self.real_value = 10
        elif v == 12:
            self.real_value = 9
        elif v == 13:
            self.real_value = 11
        else:
            self.real_value = v + 11

    def __str__(self):
        """Return value, color"""
        return ";".join([str(self.value), str(self.color)])


class Player:
    """Represent a player and his current cards"""

    def __init__(self, player_id, name):
        # attributes forever
        self.name = name
        self.player_id = player_id
        # TODO for now 5 cards per player at the beginning
        self.number_of_lives = 5

        # attributes for current gameturn
        self.cards = []

    def draw_card(self, card):
        """Adds a card to the current hand"""
        card.owner_id = self.player_id
        self.cards.append(card)

    def play_card(self, card_index):
        """Pops a chosen card from current hand and returns it"""
        return self.cards.pop(card_index)

    def is_alive(self):
        return self.number_of_lives > 0

    def is_dead(self):
        return self.number_of_lives == 0

    def lose_life(self, life_loss):
        self.number_of_lives -= life_loss
        if self.number_of_lives < 0:
            self.number_of_lives = 0

    def has_cards(self):
        return len(self.cards) > 0

    def throw_remaining_cards(self):
        self.cards = []

    def __str__(self):
        """Return id, name, number of lives, current cards"""
        return "; ".join([str(self.player_id), self.name, str(self.number_of_lives), str([str(card) for card in self.cards])])


class Lobby:
    """Represent a table and a running game.

    Should be able to:
    * launch a game -> fn __init__(number_of_players)
    * return a complete game status -> fn status()
    * register a player -> fn register(player)
    * draw a card for a player -> fn draw(player)

    Vocabulary: X turns per gameturn, Y gameturns per game, at least
    one card is lost by at least one player per gameturn
    """

    def __init__(self, lobby_id, number_of_players):
        """Create a new game instance"""
        # attributes for keeping track of the current game
        # in Fodinha the dealer starts
        self.players = []
        self.number_of_players = number_of_players
        self.lobby_id = lobby_id

        # these values are set in the prepare_gameturn f'n
        # here, we set the default that will result in the dealer in position 0
        self.current_dealer_id = -1
        self.current_player_id = None

        # 0: game not started, n: currently in nth gameturn
        self.gameturn_number = 0

        # attributes for keeping track of the current gameturn
        self.current_beforemanilla = None
        self.current_number_of_turns = None
        self.current_turn_number = None
        self.current_turn_type = None
        self.current_win_value = 1
        self.current_guesses = []
        self.current_wins = []
        self.current_played_cards = []

        # full deck: will be created at beginning of each gameturn
        self.deck = []
        # when all players join, a gameturn must be prepared and the game can start

    def generate_new_deck(self):
        """Generate a new full deck"""
        deck = []
        for value in range(1, 14):
            deck.append(Card(value, Color.HEARTS))
            deck.append(Card(value, Color.SPADES))
            deck.append(Card(value, Color.DIAMONDS))
            deck.append(Card(value, Color.CLUBS))

        return deck

    def set_next_dealer_id(self):
        """Set the dealer and player IDs for the current gameturn"""
        # find and set current dealer id
        next_dealer_id = (self.current_dealer_id + 1) % self.number_of_players
        self.current_dealer_id = next_dealer_id

        # we call the f'n again in the case of a dead dealer
        if self.players[next_dealer_id].is_dead():
            return self.set_next_dealer_id()
        # else the dealer is alive
        # the dealer is always the next player
        # (f'n is only called when preparing a gameturn)
        else:
            self.current_player_id = self.current_dealer_id

    def set_next_player_id(self):
        """Set the player ID for the current turn"""
        # this is almost the same f'n as above
        # keep in mind in here you can't trust the number of lives (has not been updated yet)
        # find and set current player id
        next_player_id = (self.current_player_id + 1) % self.number_of_players
        self.current_player_id = next_player_id

        # we call the f'n again in case of a player with no cards
        # (dead or just has no cards in the current turn)
        if not self.players[next_player_id].has_cards():
            return self.set_next_player_id()

    def next_player_is_dealer(self):
        """Check if the next player is the dealer"""
        next_player_id = (self.current_player_id + 1) % self.number_of_players
        return next_player_id == self.current_dealer_id

    def get_alive_player_id(self, given_id):
        """For a current_guesses position, return corresponding player ID"""
        # we need the given_id to be the corresponding alive player
        alive_player_id = 0

        # for all players
        for i in range(self.number_of_players):
            if self.players[i].is_alive():
                # check if this is the player we want
                if alive_player_id == given_id:
                    print("RETURNED ALIVE ID {}".format(i))
                    return i
                # update alive_player_id for all alive players
                print("SKIPPED ONE: ALIVE_PLAYER_ID {}".format(alive_player_id))
                alive_player_id += 1

    def count_alive_players(self):
        """Returns the number of currently alive players"""
        result = 0
        for p in self.players:
            if p.is_alive():
                result += 1
        return result

    def count_having_cards_players(self):
        """Returns the number of currently holding cards players"""
        result = 0
        for p in self.players:
            if p.has_cards():
                result += 1
        return result


    def register_player(self, name):
        """Create a new player without assigning him cards"""
        current_id = len(self.players)
        # if all players already joined
        if current_id == self.number_of_players:
            raise RuntimeError('A player is trying to join a full lobby. His name: ', name)
        # else append a new Player instance to the list of players
        # the name argument is the chosen username
        else:
            assert current_id >= 0 and current_id < self.number_of_players
            self.players.append(Player(current_id, name))

    def set_current_number_of_turns(self):
        """Calculate the number of turns for this gameturn and set attributes"""
        # in all cases this is the start of a new gameturn
        self.current_turn_number = 0

        # now we find how many turns this gameturn gon be
        number_of_cards_per_player = [player.number_of_lives for player in self.players]
        max_lives = max(number_of_cards_per_player)
        if number_of_cards_per_player.count(max_lives) > 1:
            self.current_number_of_turns = max_lives
        else:
            # if the player with most lives is alone, the second player 
            # with most lives determines the number of turns
            number_of_cards_per_player.remove(max_lives)
            self.current_number_of_turns = max(number_of_cards_per_player)

        # create the current_wins array
        # if 3 players are still alive, length 3
        # a given win index is for the given player
        # (even though dead players shouldn't win)
        self.current_wins = [0 for _ in range(self.number_of_players)]

    def close_turn(self):
        """Close a current turn"""
        # first off update the attributes
        self.current_turn_number += 1

        # find who won this turn and update the current_wins list
        self.update_current_wins()

        # empty the played_cards array
        self.current_played_cards = []

        # if this was the final turn, close the gameturn
        # this is where the life loss happen
        if self.current_turn_number == self.current_number_of_turns:
            return self.close_gameturn()

        # otherwise we continue on to a play turn
        # it's again the dealer's turn to play
        # only if he still has cards, otherwise next player
        self.rewind_player_id()

    def rewind_player_id(self):
        """Set current_player_id from dealer ID, checking if he has cards"""
        self.current_player_id = self.current_dealer_id
        # if the dealer has no cards, it's to the next player with cards
        if not self.players[self.current_player_id].has_cards():
            # i hate to do this in python but can't see another way
            i = 0
            next_player_id = self.current_player_id
            while i < self.number_of_players:
                next_player_id = (next_player_id + 1) % self.number_of_players
                if self.players[next_player_id].has_cards():
                    self.current_player_id = next_player_id
                    return
                i += 1

            print("SHOULD NEVER REACH HERE")
            raise RuntimeError("No players left with cards, should have called close_gameturn")

    def update_current_wins(self):
        """Update the current_wins array at the end of a turn"""
        # set the value of the current manilla
        if self.current_beforemanilla.real_value == 13:
            manilla_value = 1
        else:
            manilla_value = self.current_beforemanilla.real_value + 1

        # set a list of the values currently played
        played_cards_real_values = [c.real_value for c in self.current_played_cards]
        # this variable is the index in the current_wins array
        winner_owner = None

        # is there more than one manilla in this turn
        if played_cards_real_values.count(manilla_value) > 1:
            # if so highest color wins
            for i, c in enumerate(self.current_played_cards):
                if c.real_value == manilla_value:
                    if winner_owner == None or c.color > self.current_played_cards[winner_owner].color:
                        winner_owner = c.owner_id
            assert winner_owner is not None
        # is there only one manilla
        elif played_cards_real_values.count(manilla_value) == 1:
            # if so it wins
            manilla_index = played_cards_real_values.index(manilla_value)
            winner_owner = self.current_played_cards[manilla_index].owner_id
        else:
            # no manilla
            winning_card = 0
            # we sort the played cards
            card_rvalues_sorted = sorted(played_cards_real_values)[::-1]
            # we discard all cards that appear more than one time
            for r in card_rvalues_sorted:
                if card_rvalues_sorted.count(r) == 1:
                    winning_card = r
                    break
            # if winning_card == 0, it means all cards canceled out
            # so whoever wins next round wins 2 points
            # 3 if it happens again and so on
            if winning_card != 0:
                card_index = played_cards_real_values.index(winning_card)
                winner_owner = self.current_played_cards[card_index].owner_id
            else:
                self.current_win_value += 1
                return

        # in all cases the winner's win is taken into account
        self.current_wins[winner_owner] += self.current_win_value
        # if the win value is not at one, it has been applied hence reset it
        if self.current_win_value != 1:
            self.current_win_value = 1
        print("DEBUG UPDATE_CURRENT_WINS")
        print(str(self.current_wins))
        print(str(self.current_guesses))


    def prepare_gameturn(self):
        """Shuffle deck, draw all cards for beginning of gameturn"""
        # shuffle deck at the beginning of gameturn
        self.shuffle_deck()

        # draw the current 'beforemanilla' card and set attributes
        self.draw_beforemanilla()

        # set attributes for the gameturn
        self.gameturn_number += 1
        self.set_current_number_of_turns()
        self.set_next_dealer_id()

        # be careful when handling the content of current_guesses
        # a guess at position 1 could be for player in position 3
        # if players 1 and 2 are dead
        # it is created by appending an empty array
        self.current_guesses = []

        # draw the current number of cards per player
        for player in self.players:
            # if a player still has cards from previous gameturn
            # discard them
            player.throw_remaining_cards()
            for _ in range(player.number_of_lives):
                self.draw(player)

        # we then set the first turn type for this gameturn
        # this is either guess or final_guess
        # TODO LES FINAL_GUESS C UN BORDEL
        if self.count_alive_players() == 2:
            self.current_turn_type = TurnType.FINAL_GUESS
        else:
            self.current_turn_type = TurnType.GUESS

    def close_gameturn(self):
        """Close a gameturn, applies life losses"""
        # calculate life loss between given guesses and actual wins
        print("CLOSING GAMETURN")
        # first, find the corresponding true id of the player
        # current_dealer_id started, so his guesses/wins are the first
        # etc for all alive players
        alive_player_ids = []
        current_player_id = self.current_dealer_id
        for _ in range(self.number_of_players):
            if self.players[current_player_id].is_alive():
                alive_player_ids.append(current_player_id)
            current_player_id = (current_player_id + 1) % self.number_of_players

        print("ALIVE_PLAYER_IDS")
        print(alive_player_ids)

        # zip the true ids of the players with their corresponding wins and guesses
        for i, g in zip(alive_player_ids, self.current_guesses):
            w = self.current_wins[i]
            life_loss = abs(g-w)
            # if they didn't guess what they won they lose life
            if life_loss != 0:
                self.players[i].lose_life(life_loss)

        # if this is the end of the game we stop here
        # even if no final_guess/final_play necessary
        if self.count_alive_players() <= 1 or self.current_turn_type == TurnType.FINAL_PLAY:
            self.current_turn_type = TurnType.GAME_OVER
        # else we prepare the next gameturn
        else:
            self.prepare_gameturn()

    def guess(self, player_id, given_guess):
        """Assign a guess to a player, if it's his turn"""
        # sanity checks
        # is this a guess turn
        if self.current_turn_type != TurnType.GUESS and self.current_turn_type != TurnType.FINAL_GUESS:
            raise RuntimeError(\
    'Supplied a play for a guess turn: player ID is ', player_id, ' turn type is ', self.current_turn_type)
        # is this player the current player
        elif player_id != self.current_player_id:
            raise RuntimeError(\
    "It is not this player's turn! Player ID: ", player_id, " current player ", self.current_player_id)
        # is he alive
        elif self.players[player_id].is_dead():
            raise RuntimeError(\
    "It is not this player's turn! Player ID: ", player_id, " current player ", self.current_player_id)
        # if not, this is a valid guess

        # now check if it's the final guess:
        if len(self.current_guesses) == self.count_alive_players() - 1:
            # you can't guess something that would not fuck anyone
            # TODO be careful to catch TypeError in the flask app
            guessed_total = sum(self.current_guesses) + given_guess
            if guessed_total == self.current_number_of_turns:
                raise ValueError(\
    "Thi guess is forbidden in the 'pé' position. Player ID: ", player_id, " given guess: ", given_guess)
            else:
                # the guess will be added just below, here we set the turntype to play or final_play
                if self.current_turn_type == TurnType.GUESS:
                    self.current_turn_type = TurnType.PLAY
                else:
                    self.current_turn_type = TurnType.FINAL_PLAY

        # we add the given guess and set next player
        # this is for a normal guess or a valid last guess
        self.current_guesses.append(given_guess)
        self.set_next_player_id()

    def play(self, player_id, played_card_index):
        """Play a player's card, if it's his turn"""
        # is this a play turn
        if self.current_turn_type != TurnType.PLAY and self.current_turn_type != TurnType.FINAL_PLAY:
            raise RuntimeError(\
                "Supplied a guess for a play turn: player ID is {}, turn type {}"\
                .format(player_id, self.current_turn_type))
        # is this player the current player
        elif player_id != self.current_player_id:
            raise RuntimeError(\
                "It is not this player's turn! Player ID: {} current {})"\
                .format(player_id, self.current_player_id))
        # is he alive
        elif self.players[player_id].is_dead():
            raise RuntimeError(\
                "This player is dead! Player ID: {} (current player {})"\
                .format(player_id, self.current_player_id))
        # does he have cards
        elif not self.players[player_id].has_cards():
            raise RuntimeError(\
                "This player has no cards! Being his turn should never happen. Player ID: {} (current player {})"\
                .format(player_id, self.current_player_id))


        # get the played card or raise ValueError from the IndexError (catched in Flask)
        try:
            played_card = self.players[player_id].play_card(played_card_index)
        except IndexError as error:
            raise ValueError(\
                "Incorrect card index specified! Index: {}, Player ID: {}"\
                .format(played_card_index, self.current_player_id))\
                from error
        # else this is a valid play
        # set the played card
        print('PLAYING CARD {}\n'.format(played_card))
        self.current_played_cards.append(played_card)

        # now check if this was the final play for this turn
        # i.e. next player is dealer or no one else has cards
        # if someone has 4 cards for a turn number of 2, should stop after second turn
        # if no one has cards, close the turn
        if self.count_having_cards_players() == 0:
            return self.close_turn()
        # if the only one with cards is the person that just played
        elif self.count_having_cards_players() == 1 and self.players[self.current_player_id].has_cards():
            return self.close_turn()
        # or else if the next player is the dealer
        elif self.next_player_is_dealer():
            return self.close_turn()
        # else set the next player
        else:
            self.set_next_player_id()

    def draw(self, player):
        """Return a random card from the current shuffled deck"""
        drawn_card = self.deck.pop()
        player.draw_card(drawn_card)

    def shuffle_deck(self):
        """Generate a new full deck and shuffles it"""
        self.deck = self.generate_new_deck()
        random.shuffle(self.deck)

    def draw_beforemanilla(self):
        """Set the current_beforemanilla card"""
        self.current_beforemanilla = self.deck.pop()

    def start_game(self):
        """Start the game, set all necessary attributes"""

        # is the game ready
        if self.number_of_players != len(self.players):
            raise RuntimeError('Not all players have joined. Current player count:', len(self.players))

        # the game can start!
        self.prepare_gameturn()

    def status(self):
        """Return detailed status of game

        The returned JSON is in the following format:
        {
            gameturn: current_gameturn_number
            current_beforemanilla: the drawn card that sets the manilla (the one above)
            players: [ "id,name,number_of_lives,current_number_of_cards", ...]
            current_player_id: the player we are waiting on (either to play or guess)
            current_dealer_id: dealer, this is the id first guessing or playing
            current_turn_type: either 'guess' (1) or 'play' (2), (3,4 if this is the final turn)
            current_guesses: if applicable, '1,0,0,1,0...' the guesses of each player
            current_played_cards: if applicable, ['1,1,12', '7,4,9', ...] (see Card class)
        }
        """
        return {
                'gameturn_number': self.gameturn_number,
                'current_beforemanilla': str(self.current_beforemanilla),
                'players': [str(player) for player in self.players],
                'current_player_id': self.current_player_id,
                'current_dealer_id': self.current_dealer_id,
                'current_number_of_turns': self.current_number_of_turns,
                'current_turn_number': self.current_turn_number,
                'current_turn_type': self.current_turn_type,
                'current_guesses': str(self.current_guesses),
                'current_wins': str(self.current_wins),
                'current_played_cards': [str(card) for card in self.current_played_cards],
                }


if __name__ == "__main__":
    # mock game for testing
    newgame = Lobby(1, 3)
    newgame.register_player('pitoco')
    newgame.register_player('dog')
    newgame.register_player('as formigas la fora')
    newgame.start_game()
    while True:
        current_player = newgame.players[newgame.current_player_id]
        print("\n", newgame.status(), "\n")
        print("\nCurrent player:")
        print(str(current_player))
        if newgame.current_turn_type == TurnType.GUESS or newgame.current_turn_type == TurnType.FINAL_GUESS:
            newgame.guess(current_player.player_id, int(input('Guess: ')))
        elif newgame.current_turn_type == TurnType.PLAY or newgame.current_turn_type == TurnType.FINAL_PLAY:
            newgame.play(current_player.player_id, int(input('Play: ')))
        else:
            print("Current turn type: {}".format(newgame.current_turn_type))
            print()
            print(newgame.status())
            break

