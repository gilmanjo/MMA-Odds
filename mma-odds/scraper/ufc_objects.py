from enum import Enum


class BoutType(Enum):
	_unused = 0
	FLYWEIGHT = 1
	BANTAMWEIGHT = 2
	FEATHERWEIGHT = 3
	LIGHTWEIGHT = 4
	WELTERWEIGHT = 5
	MIDDLEWEIGHT = 6
	LIGHT_HEAVYWEIGHT = 7
	HEAVYWEIGHT = 8
	W_STRAWWEIGHT = 9
	W_BANTAMWEIGHT = 10
	W_FEATHERWEIGHT = 11
	CATCHWEIGHT = 12

class Event(object):
	"""docstring for Event"""
	def __init__(self):
		super(Event, self).__init__()
		self.name  = ""
		self.date = ""
		self.location = ""
		self.attendance = 0
		self.fights = []

class Fight(object):
	"""docstring for Fight"""
	def __init__(self):
		super(Fight, self).__init__()
		self.fighters = []
		self.winner = ""
		self.bout_type = ""
		self.method = ""
		self.end_round = 0
		self.end_time = ""
		self.num_rounds = 0
		self.referee = ""
		self.details = ""
		self.overall_rounds = []
		self.sigstrikes_rounds = []
		
class FightRound(object):
	"""docstring for FightRound"""
	def __init__(self, round_number):
		super(FightRound, self).__init__()
		self.round_number = round_number
		self.fighter_stats = {}
		
class Fighter(object):
	"""docstring for Fighter"""
	def __init__(self):
		super(Fighter, self).__init__()
		self.name = ""
		self.nickname = ""

		# Record
		self.wins = 0
		self.losses = 0
		self.draws = 0
		self.ncs = 0

		# Physical Stats
		self.height = 0
		self.weight = 0
		self.reach = 0
		self.stance = ""
		self.dob = ""

		# Performance Stats
		self.slpm = 0	# Sig Strikes Landed Per Min
		self.str_acc = 0	# Sig Strike Accuracy
		self.sapm = 0	# Sig Strikes Absorbed Per Min
		self.str_def = 0	# Sig Strike Defence
		self.td_avg = 0		# Avg Takedowns per 15 Min
		self.td_acc = 0		# Takedown Accuracy
		self.td_def = 0		# Takedown Defense
		self.sub_avg = 0	# Avg Subs Attempted Per 15 Min