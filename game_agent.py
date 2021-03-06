"""This file contains all the classes you must complete for this project.

You can use the test cases in agent_test.py to help during development, and
augment the test suite with your own test cases to further test your code.

You must test your agent's strength against a set of agents with known
relative strength using tournament.py and include the results in your report.
"""
import random
import itertools
from operator import itemgetter
from functools import wraps, partial


NO_MOVES = (-1, -1)


def add_timeout(f):
    """Decorator for adding timeout exception."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.time_left() < self.TIMER_THRESHOLD:
            raise Timeout()
        return f(*args, **kwargs)
    return wrapper


def add_loser_winner_scores(heuristic):
    """Decorator defining scores for both winning and losing outcomes for a heuristic."""
    @wraps(heuristic)
    def wrapper(game, player, **kwargs):
        if game.is_loser(player):
            return float("-inf")
        if game.is_winner(player):
            return float("inf")
        return heuristic(game, player, **kwargs)
    return wrapper


class Timeout(Exception):
    """Subclass base exception for code clarity."""
    pass


@add_loser_winner_scores
def moves_heuristic(game, player, w_own=1, w_opp=-1):
    """Weighted sum of the number of moves available to the two
     players.

     The default (`w_own`=1, `w_opp`=-1) results in the `improved_score()`
     heuristic.

    Parameters
    ----------
    game : `isolation.Board`
    player : object
        A player instance in the current game
    w_own, w_opp: float
        Weights for own moves and opponent moves, respectively

    Returns
    -------
    float
        The heuristic value of the current game state to the specified player.
    """
    own_moves = len(game.get_legal_moves(player))
    opp_moves = len(game.get_legal_moves(game.get_opponent(player)))
    return float(w_own*own_moves + w_opp*opp_moves)


aggressive_move_heuristic = partial(moves_heuristic, w_own=1, w_opp=-2.5)
relaxed_move_heuristic = partial(moves_heuristic, w_own=1, w_opp=-0.5)


@add_loser_winner_scores
def center_distance_heuristic(game, player, w_own=1, w_opp=1, normalize=False):
    """Weighted sum of the distances of the player's positions to the center,
    optionally normalized by the maximum possible distance.


    Parameters
    ----------
    game : `isolation.Board`
    player : object
        A player instance in the current game
    w_own, w_opp: float
        Weights for own distance and opponent distance, respectively
    normalize: bool
        If true, center distances are normalized by the maximum possible distance.

    Returns
    -------
    float
        The heuristic value of the current game state to the specified player.
    """
    h, w = game.height, game.width
    center_y, center_x = ((h-1)/2, (w-1)/2)
    own_y, own_x = game.get_player_location(player)
    opp_y, opp_x  = game.get_player_location(game.get_opponent(player))
    opp_dist = ((opp_x - center_x)**2 + (opp_y - center_y)**2)**0.5
    own_dist = ((own_x - center_x)**2 + (own_y - center_y)**2)**0.5

    # normalize
    if normalize:
        max_dist = ((center_x)**2 + (center_y)**2)**0.5
        own_dist /= max_dist
        opp_dist /= max_dist

    return float(w_own*own_dist + w_opp*opp_dist)


aggressive_distance_heuristic = partial(center_distance_heuristic,
                                        w_own=-1.5, w_opp=3)
relaxed_distance_heuristic = partial(center_distance_heuristic,
                                     w_own=-1.5, w_opp=0.75)
aggressive_distance_heuristic_norm = partial(center_distance_heuristic,
                                             w_own=-1.5, w_opp=3, normalize=True)
relaxed_distance_heuristic_norm = partial(center_distance_heuristic,
                                          w_own=-1.5, w_opp=0.75, normalize=True)


def relaxed_move_relaxed_distance(game, player):
    return (relaxed_move_heuristic(game, player)
            + relaxed_distance_heuristic(game, player))


def relaxed_move_aggressive_distance(game, player):
    return (relaxed_move_heuristic(game, player)
            + aggressive_distance_heuristic(game, player))


def relaxed_move_relaxed_distance_norm(game, player):
    return (relaxed_move_heuristic(game, player)
            + aggressive_distance_heuristic_norm(game, player))


def relaxed_move_aggressive_distance_norm(game, player):
    return (relaxed_move_heuristic(game, player)
            + relaxed_distance_heuristic_norm(game, player))


def custom_score(game, player):
    """Calculate the heuristic value of a game state from the point of view
    of the given player.

    Note: this function should be called from within a Player instance as
    `self.score()` -- you should not need to call this function directly.

    Parameters
    ----------
    game : `isolation.Board`
        An instance of `isolation.Board` encoding the current state of the
        game (e.g., player locations and blocked cells).

    player : object
        A player instance in the current game (i.e., an object corresponding to
        one of the player objects `game.__player_1__` or `game.__player_2__`.)

    Returns
    -------
    float
        The heuristic value of the current game state to the specified player.
    """
    return relaxed_move_aggressive_distance_norm(game, player)



class CustomPlayer:
    """Game-playing agent that chooses a move using your evaluation function
    and a depth-limited minimax algorithm with alpha-beta pruning. You must
    finish and test this player to make sure it properly uses minimax and
    alpha-beta to return a good move before the search time limit expires.

    Parameters
    ----------
    search_depth : int (optional)
        A strictly positive integer (i.e., 1, 2, 3,...) for the number of
        layers in the game tree to explore for fixed-depth search. (i.e., a
        depth of one (1) would only explore the immediate sucessors of the
        current state.)

    score_fn : callable (optional)
        A function to use for heuristic evaluation of game states.

    iterative : boolean (optional)
        Flag indicating whether to perform fixed-depth search (False) or
        iterative deepening search (True).

    method : {'minimax', 'alphabeta'} (optional)
        The name of the search method to use in get_move().

    timeout : float (optional)
        Time remaining (in milliseconds) when search is aborted. Should be a
        positive value large enough to allow the function to return before the
        timer expires.
    """

    def __init__(self, search_depth=3, score_fn=custom_score,
                 iterative=True, method='minimax', timeout=20.):
        self.search_depth = search_depth
        self.iterative = iterative
        self.score = score_fn
        self.method = method
        self.time_left = None
        self.TIMER_THRESHOLD = timeout

    def get_move(self, game, legal_moves, time_left):
        """Search for the best move from the available legal moves and return a
        result before the time limit expires.

        This function must perform iterative deepening if self.iterative=True,
        and it must use the search method (minimax or alphabeta) corresponding
        to the self.method value.

        **********************************************************************
        NOTE: If time_left < 0 when this function returns, the agent will
              forfeit the game due to timeout. You must return _before_ the
              timer reaches 0.
        **********************************************************************

        Parameters
        ----------
        game : `isolation.Board`
            An instance of `isolation.Board` encoding the current state of the
            game (e.g., player locations and blocked cells).

        legal_moves : list<(int, int)>
            A list containing legal moves. Moves are encoded as tuples of pairs
            of ints defining the next (row, col) for the agent to occupy.

        time_left : callable
            A function that returns the number of milliseconds left in the
            current turn. Returning with any less than 0 ms remaining forfeits
            the game.

        Returns
        -------
        (int, int)
            Board coordinates corresponding to a legal move; may return
            (-1, -1) if there are no available legal moves.
        """

        self.time_left = time_left

        # Perform any required initializations, including selecting an initial
        # move from the game board (i.e., an opening book), or returning
        # immediately if there are no legal moves

        if not legal_moves:
            return NO_MOVES

        if self.method == 'minimax':
            search_method = self.minimax
        elif self.method == 'alphabeta':
            search_method = self.alphabeta

        move = None
        try:
            if self.iterative:
                # TODO: stop iterative deepening when terminal state is reached
               for depth in itertools.count():
                   _, move = search_method(game, depth)

            else:
                # perform depth limited search
                _, move = search_method(game, self.search_depth)

        except Timeout:
            # Handle any actions required at timeout, if necessary
            pass

        # Return the best move from the last completed search iteration
        return move

    @add_timeout
    def get_score(self, move, game, depth, maximizing_player, alpha=None, beta=None):
        """Return the score obtained after a specified move.

        If `alpha` and `beta` are specified, alphabeta search will be used,
        and minimax search otherwise.
        """
        new_board = game.forecast_move(move)
        if alpha is not None and beta is not None:
            score, _ = self.alphabeta(new_board, depth-1, alpha, beta,
                                      maximizing_player)
        else:
            score, _ = self.minimax(new_board, depth-1, maximizing_player)

        return score

    @add_timeout
    def minimax(self, game, depth, maximizing_player=True):
        """Implement the minimax search algorithm as described in the lectures.

        Parameters
        ----------
        game : isolation.Board
            An instance of the Isolation game `Board` class representing the
            current game state

        depth : int
            Depth is an integer representing the maximum number of plies to
            search in the game tree before aborting

        maximizing_player : bool
            Flag indicating whether the current search depth corresponds to a
            maximizing layer (True) or a minimizing layer (False)

        Returns
        -------
        float
            The score for the current search branch

        tuple(int, int)
            The best move for the current branch; (-1, -1) for no legal moves

        Notes
        -----
            (1) You MUST use the `self.score()` method for board evaluation
                to pass the project unit tests; you cannot call any other
                evaluation function directly.
        """

        # get legal moves
        moves = game.get_legal_moves()
        # terminal test
        if not moves:
            return game.utility(self), NO_MOVES
        # cutoff test
        if depth == 0:
            return self.score(game, self), NO_MOVES

        if maximizing_player:
            moves_with_scores = [(self.get_score(m, game, depth, maximizing_player=False), m)
                                 for m in moves]
            score, next_move = max(moves_with_scores, key=itemgetter(0))
        else:
            moves_with_scores = [(self.get_score(m, game, depth, maximizing_player=True), m)
                                 for m in moves]
            score, next_move = min(moves_with_scores, key=itemgetter(0))

        return score, next_move

    @add_timeout
    def alphabeta(self, game, depth, alpha=float("-inf"), beta=float("inf"),
                  maximizing_player=True):
        """Implement minimax search with alpha-beta pruning as described in the
        lectures.

        Parameters
        ----------
        game : isolation.Board
            An instance of the Isolation game `Board` class representing the
            current game state

        depth : int
            Depth is an integer representing the maximum number of plies to
            search in the game tree before aborting

        alpha : float
            Alpha limits the lower bound of search on minimizing layers

        beta : float
            Beta limits the upper bound of search on maximizing layers

        maximizing_player : bool
            Flag indicating whether the current search depth corresponds to a
            maximizing layer (True) or a minimizing layer (False)

        Returns
        -------
        float
            The score for the current search branch

        tuple(int, int)
            The best move for the current branch; (-1, -1) for no legal moves

        Notes
        -----
            (1) You MUST use the `self.score()` method for board evaluation
                to pass the project unit tests; you cannot call any other
                evaluation function directly.
        """

        # get legal moves
        moves = game.get_legal_moves()

        # terminal test
        if not moves:
            return game.utility(self), NO_MOVES
        # cutoff test
        if depth == 0:
            return self.score(game, self), NO_MOVES

        if maximizing_player:
            moves_with_scores = []
            for next_move in moves:
                score = self.get_score(next_move, game, depth, maximizing_player=False,
                                       alpha=alpha, beta=beta)

                if score >= beta: return score, next_move

                alpha = max(alpha, score)
                moves_with_scores.append((score, next_move))
            score, next_move = max(moves_with_scores, key=itemgetter(0))
        else:
            moves_with_scores = []
            for next_move in moves:
                score = self.get_score(next_move, game, depth, maximizing_player=True,
                                       alpha=alpha, beta=beta)

                if score <= alpha: return score, next_move

                beta = min(beta, score)
                moves_with_scores.append((score, next_move))
            score, next_move = min(moves_with_scores, key=itemgetter(0))

        return score, next_move

