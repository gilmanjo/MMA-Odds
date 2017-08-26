import numpy as np
import sklearn as sk
import ufc_objects as ufc


def single_kelly(moneyline_odds, p):
	"""Calculates Kelly Criterion for a single event

	Given the moneyline odds and probability of an outcome, the Kelly Criterion
	will return a decimal representing the percentage of one's purse that
	should be wagered on the event.  A negative decimal implies that nothing
	should be wagered on the event.
	
	Args:
		moneyline_odds - integer representing moneyline odds for an outcome
		p - the probability of the outcome

	Returns:
		kelly criterion as a decimal

	Raises:
		TypeError - if moneyline_odds or p aren't an integer or float, 
					respectively
		ValueError - if p isn't a float between 0 and 1
	"""
	try:
	
		if p < 0 or p > 1:
			raise ValueError

		# First convert odds to decimal odds
		decimal_odds = 0

		if moneyline_odds > 0:
			decimal_odds = moneyline_odds/100 + 1

		elif moneyline_odds < 0:
			decimal_odds = 100/abs(moneyline_odds) + 1

		else:
			return  p - (1-p)	# even moneyline

		# Then return KC
		return ((decimal_odds-1)*p - (p-1))/(decimal_odds-1)

	except TypeError as e:
		print(e)

	except ValueError:
		print("P must be between 0 and 1.")

def main():
	pass

if __name__ == '__main__':
	main()