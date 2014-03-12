from __future__ import division
import random
from operator import itemgetter
from collections import namedtuple

other={0:1, 1:0}
State = namedtuple('State', ['p', 'a', 'b', 'pending'])
UtilRecord = namedtuple('UtilRecord', ['util_a', 'util_b', 'action'])

def memo(f):
    """Decorator that caches the return value for each call to f(args).
    Then when called again with same args, we can just look it up."""
    cache = {}
    def _f(*args):
        try:
            return cache[args]
        except KeyError:
            cache[args] = result = f(*args)
            return result
        except TypeError:
            # some element of args can't be a dict key
            return f(args)
    return _f

class NotFinishedException(Exception):
    pass


def flush(state):
    if (state.p == 0):
        return State(state.p, state.a + state.pending, state.b, 0)
    else:
        return State(state.p, state.a, state.b + state.pending, 0)

def max_prob(state, player):
    """
       end-state utility function maximizing probability of winning;
       parameters: 
         ``player``: index of player , 0 or 1

       returns utility of given player; if the state is not end-state, it throws
    """
    state = flush(state)
    if state.a >= goal:
        return 1 if player == 0 else 0
    if state.b >= goal:
        return 1 if player == 1 else 0
    raise NotFinishedException()

def umax_diff(state, player):
    """
       end-state utility function maximizing difference of scores but only if win.
       returns:
           same as max_prob
    """
    state = flush(state)
    if state.a >= goal:
         return state.a - state.b if player == 0 else 0
    if state.b >= goal:
         return state.b - state.a if player == 1 else 0
    raise NotFinishedException()

def max_diff(state, player):
    """
       end-state utility function maximizing difference of scores 
       returns:
           same as max_prob
    """
    state = flush(state)
    if state.a >= goal:
         return state.a - state.b if player == 0 else state.b - state.a
    if state.b >= goal:
         return state.b - state.a if player == 1 else state.a - state.b
    raise NotFinishedException()

def choice(states):
    states = list(states)
    rnd = random.random()
    for state, p in states:
        rnd -= p
        if rnd <= 0: return state

def util(end_pla, end_plb):
    """
    computes utilities for two-player-game, players are described by their end-state utilities.
      
    arguments:
        end_pla, end_plb: end utility functions
    returns:
        state -> UtilRecord(utility_a, utility_b, action to achieve it)
    """
    @memo
    def util_(state):
        try:
            return UtilRecord(end_pla(state,0), end_plb(state, 1), hold)
        except NotFinishedException:

            def avg_util(player, action): 
                return sum(util_(new_state)[player] * prob for new_state, prob in action(state))

            def action_gen(state):
                for action in actions(state):
                    yield UtilRecord(avg_util(0, action), avg_util(1, action), action)

            return max(action_gen(state), key = itemgetter(state.p)) 
    return util_

def strategy_from_util(util, player):
    """
    creates strategy (state -> action) based on utility function. 
    """
    def strategy(state):
        if state.p == player:
            return util(state).action
        else:
            return util(State(other[state.p], state.b, state.a, state.pending)).action
    return strategy

def actions(state):
  """
      list all actions playable for given state
  """
  if state.pending > 0:
    return [hold, roll]
  else:
    return [roll]

def hold(state):
    """
       hold action specification. 
           returns: iterable of (new_state, probability) for every possible outcome.
    """
    a = state.a
    b = state.b
    if state.p == 0:
        a += state.pending
    else:
        b += state.pending
    return [(State(other[state.p], a, b, 0), 1)]

def roll(state):
    """
        roll action specification.
            returns: same as hold function
    """
    def _roll(state, dice):
        p, pl_a, pl_b, pending = state
        if dice == 1:
            if p == 0:
                pl_a += 1
            else:
                pl_b += 1
            return State(other[p], pl_a, pl_b, 0)
        else:
            return State(p, pl_a, pl_b, pending + dice)

    dice = 4
    for i in range(1, dice + 1):
        yield (_roll(state, i), 1/dice)

def upto(n):
    """
       factory for creating 'upto n' strategies. 
       returns:
          state -> action 
    """
    def _upto(state):
        if state.pending >= n:
            return hold
        else:
            return roll
    return _upto

goal = 40

def play_pig(str_a, str_b, init_state = State(0,0,0,0)):
    """
    plays one pig game.
    arguments:
      str_a, str_b: strategies of a type: state -> action
    returns:
      (strategy that wins, end state)
    """
    state = init_state
    while True:
        if state.a >= goal:
            return str_a, state
        if state.b >= goal:
            return str_b, state
        strategy = (str_a,str_b)[state.p]
        action = strategy(state)
        state = choice(action(state))

def tournament(str_a, str_b, util_a = max_prob, util_b = max_prob, rounds = 1000):
    """
    plays tournament of 'rounds' rounds between players represented by strategies str_a and str_b.
    It collects end-utilities based on util_a, util_b functions. Note that util_a, util_b not need
    to be same as utilities, that were used for creating strategies. Note also, that strategy can be
    created without notion of end-state utility at all.
    arguments:
      str_a, str_b are as in play_pig function
      util_a, util_b end-state utility function such as max_diff or max_prob
    returns:
      (U_a, U_b) where U_x is average end-state utility for player x, meassured by util_x
    """
    score = {}
    score[str_a], score[str_b] = 0,0
    util_a_, util_b_ = 0,0
    for i in range(rounds):
        strategy, end_state = play_pig(str_a, str_b, init_state = State(i%2,0,0,0))
        score[strategy] += 1
        util_a_ += util_a(end_state, 0)
        util_b_ += util_b(end_state, 1)
    return util_a_ / rounds, util_b_ / rounds


#print(tournament(upto(5), upto(20), util_a = max_prob, util_b = max_prob))

_util = util(max_prob, umax_diff)
max_probber = strategy_from_util(_util, 0)
max_differ = strategy_from_util(_util, 1)

print(tournament(max_probber, max_differ, util_a = max_prob, util_b = max_prob, rounds = 10000))
