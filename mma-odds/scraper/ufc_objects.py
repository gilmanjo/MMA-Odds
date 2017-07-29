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
		self.height = 0
		self.weight = 0
		self.reach = 0
		self.stance = ""
		self.dob = ""