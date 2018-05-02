import datetime
from dateutil.relativedelta import relativedelta
from enum import Enum
import graphviz
import matplotlib.pyplot as plt
import numpy as np
import os
os.environ["PATH"] += os.pathsep + "C:/Program Files (x86)/Graphviz2.38/bin/"
import pickle
import re
from sklearn import metrics, model_selection, neighbors, preprocessing
from sklearn import svm, tree
import sys
sys.path.append("../scraper/")
import ufc_objects as ufc


# Constants
TRAINING_TO_TEST_SET_RATIO = 0.8
EVENT_FOLDER = "..//scraper//saved_events//"
FIGHTER_FOLDER = "..//scraper//saved_fighters//"


class Stance(Enum):
	_unused = 0
	ORTHODOX = 1
	SOUTHPAW = 2
	OTHER = 3

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

def get_event_list():
	# unpickle events from directory
	events = []
	print("Getting events...")
	for filename in os.listdir(EVENT_FOLDER):
		if filename.endswith(".pickle"):
			with open(EVENT_FOLDER + filename, "rb") as f:
				event = pickle.load(f)
				events.append(event)

	return events

def sort_events(events_list):
	# Sorts the events by chronological order
	for x, event in enumerate(events_list):
		event.date = datetime.datetime.strptime(event.date, "%B %d, %Y")
		events_list[x] = event

	events_list.sort(key=lambda x: x.date)
	return events_list

def get_fighter_list():
	# unpickle fighters from directory
	fighters = []
	print("Getting fighters...")
	for filename in os.listdir(FIGHTER_FOLDER):
		if filename.endswith(".pickle"):
			with open(FIGHTER_FOLDER + filename, "rb") as f:
				fighter = pickle.load(f)
				fighters.append(fighter)

	return fighters

def revert_records(events_list, fighter_list):
	"""Rolls back fighter match records
	"""
	print("Reverting fighters' records for training...")
	for event in events_list:

		for fight in event.fights:
			
			if fight.winner == "" and "Decision" in fight.method:
				#draw
				for x, fighter in enumerate(fighter_list):

					if fighter.name == fight.fighters[0]:
						fighter.draws = int(fighter.draws) - 1
						fighter_list[x] = fighter

					elif fighter.name == fight.fighters[1]:
						fighter.draws = int(fighter.draws) - 1
						fighter_list[x] = fighter

			elif fight.winner == "":
				#nc
				for x, fighter in enumerate(fighter_list):

					if fighter.name == fight.fighters[0]:
						if isinstance(fighter.ncs, list):
							fighter.ncs = int(fighter.ncs[0]) - 1
						else:
							fighter.ncs = int(fighter.ncs) - 1
						fighter_list[x] = fighter

					elif fighter.name == fight.fighters[1]:
						if isinstance(fighter.ncs, list):
							fighter.ncs = int(fighter.ncs[0]) - 1
						else:
							fighter.ncs = int(fighter.ncs) - 1
						fighter_list[x] = fighter

			else:
				# normal fight result
				for x, fighter in enumerate(fighter_list):

					if fighter.name == fight.winner:
						fighter.wins = int(fighter.wins) - 1
						fighter_list[x] = fighter

					elif fighter.name == fight.fighters[0] \
						or fighter.name == fight.fighters[1]:
						fighter.losses = int(fighter.losses) - 1
						fighter_list[x] = fighter

	# Revert performance stats
	for x, fighter in enumerate(fighter_list):
		fighter.slpm = 0
		fighter.str_acc = 0
		fighter.sapm = 0
		fighter.str_def = 0
		fighter.td_avg = 0
		fighter.td_acc = 0
		fighter.td_def = 0
		fighter.sub_avg = 0

		# new attributes that I forgot to add to the Fighter class
		fighter.fight_time = 0
		fighter.sig_strikes = 0
		fighter.sig_strikes_att = 0
		fighter.sig_strikes_taken = 0
		fighter.sig_strikes_def = 0
		fighter.td_att = 0
		fighter.td_landed = 0
		fighter.td_taken = 0
		fighter.td_def = 0
		fighter.sub_att = 0

		# fix categorical data lol
		if fighter.stance == "Orthodox":
			fighter.stance = 1
		elif fighter.stance == "Southpaw":
			fighter.stance = 2
		else:
			fighter.stance = 0

		fighter_list[x] = fighter

	return fighter_list

def create_vectors(events_list, fighter_list, scale=True):
	"""Generate our training set for our algorithm
	"""
	events_list
	new_vectors = []
	vector_labels = []

	# syntax for our feature vector
	#
	# [f1_wins, f1_losses, f1_draws, f1_height, f1_weight, f1_reach,
	# f1_stance, f1_age, f1_slpm, f1_str_acc, f1_sapm, f1_str_def, f1_td_avg,
	# f1_td_acc, f1_td_def, f1_sub_avg, f2_wins, f2_losses, f2_draws, 
	# f2_height, f2_weight, f2_reach, f2_stance, f2_age, f2_slpm, f2_str_acc,
	# f2_sapm, f2_str_def, f2_td_avg, f2_td_acc, f2_td_def, f2_sub_avg]

	print("Generating vectors...")

	for event in events_list:

		for fight in event.fights:

			new_vector_f1 = []
			new_vector_f2 = []

			for x, fighter in enumerate(fighter_list):

				if fighter.name == fight.fighters[0]:

					# some fighters didn't have a dob, so skip 'em
					if not isinstance(fighter.dob, datetime.date):
						continue


					# fill vector with all those juicy features
					new_vector_f1 = [fighter.wins, fighter.losses,
						int(fighter.draws), fighter.height, 
						int(fighter.weight),
						int(re.search(r"\d+", str(fighter.reach)).group()), 
						fighter.stance, 
						relativedelta(event.date.date() - fighter.dob).years,
						fighter.slpm, fighter.str_acc, fighter.sapm,
						fighter.str_def, fighter.td_avg, fighter.td_acc,
						fighter.td_def, fighter.sub_avg]
					fighter_list[x] = update_fighter_stats(fighter, fight)

				elif fighter.name == fight.fighters[1]:

					if not isinstance(fighter.dob, datetime.date):
						continue

					new_vector_f2 = [fighter.wins, fighter.losses,
						int(fighter.draws), fighter.height, 
						int(fighter.weight),
						int(re.search(r"\d+", str(fighter.reach)).group()), 
						fighter.stance, 
						relativedelta(event.date.date() - fighter.dob).years,
						fighter.slpm, fighter.str_acc, fighter.sapm,
						fighter.str_def, fighter.td_avg, fighter.td_acc,
						fighter.td_def, fighter.sub_avg]
					fighter_list[x] = update_fighter_stats(fighter, fight)

			# if there wasn't a fighter match or it was a NC, then skip fight
			if len(new_vector_f1) == 0 or len(new_vector_f2) == 0 \
				or (fight.winner == "" and "Decision" not in fight.method):
				break

			new_vectors.append(new_vector_f1 + new_vector_f2)
			
			# duplicate fight vector so fight billing is invariant (i.e.
			# it doesn't matter if a fighter is billed first or second)
			dup_vector = new_vector_f2 + new_vector_f1
			new_vectors.append(dup_vector)

			if fight.winner == "":
				vector_labels.append(2)
				vector_labels.append(2)

			elif fight.winner == fight.fighters[0]:
				vector_labels.append(0)
				vector_labels.append(1)

			else:
				vector_labels.append(1)
				vector_labels.append(0)

	if scale:
		return scale_vectors(new_vectors), vector_labels
	else:
		return new_vectors, vector_labels

def update_fighter_stats(fighter, fight):
	# updates a fighters stats

	# first update record stats
	if fight.winner == "":
		fighter.draws = int(fighter.draws) + 1

	elif fight.winner == fighter.name:
		fighter.wins = int(fighter.wins) + 1

	else:
		fighter.losses = int(fighter.losses) + 1

	# add in data from fight rounds
	for fight_round in fight.overall_rounds:

		# add round time
		if int(fight_round.round_number) == int(fight.end_round):
			fighter.fight_time += _time_to_minutes(fight.end_time)

		else:
			fighter.fight_time += 5

		# check both fighter stats for off and def stats
		for key in fight_round.fighter_stats:

			if key == fighter.name:
				# offensive stats
				fighter.sig_strikes += int(
					fight_round.fighter_stats[key]["Sig. Str."].split()[0])
				fighter.sig_strikes_att += int(
					fight_round.fighter_stats[key]["Sig. Str."].split()[2])
				fighter.td_landed += int(
					fight_round.fighter_stats[key]["TD"].split()[0])
				fighter.td_att += int(
					fight_round.fighter_stats[key]["TD"].split()[2])
				fighter.sub_att += int(
					fight_round.fighter_stats[key]["Sub. Att."])

			else:
				# defensive stats (by adding what the other fighter
				# did offensively)
				fighter.sig_strikes_taken += int(
					fight_round.fighter_stats[key]["Sig. Str."].split()[0])
				fighter.sig_strikes_def += int(
					fight_round.fighter_stats[key]["Sig. Str."].split()[2])
				fighter.td_taken += int(
					fight_round.fighter_stats[key]["TD"].split()[0])
				fighter.td_def += int(
					fight_round.fighter_stats[key]["TD"].split()[2])

		# update advanced stats
		fighter.slpm = _divide_catch(fighter.sig_strikes, fighter.fight_time)
		fighter.str_acc = _divide_catch(fighter.sig_strikes, 
									fighter.sig_strikes_att)
		fighter.sapm = _divide_catch(fighter.sig_strikes_taken, 
									fighter.fight_time)
		fighter.str_def = _divide_catch(fighter.sig_strikes_def,
			fighter.sig_strikes_taken + fighter.sig_strikes_def)
		fighter.td_avg = _divide_catch(fighter.td_landed, 
									fighter.fight_time * 15)
		fighter.td_acc = _divide_catch(fighter.td_att, fighter.td_landed)
		fighter.td_def = _divide_catch(fighter.td_def,
			fighter.td_def + fighter.td_taken)
		fighter.sub_avg = _divide_catch(fighter.sub_att, 
									fighter.fight_time * 15)

	return fighter

def scale_vectors(vector_list):
	# scales values in vector list to unit scale for use with
	# scale-variant algorithms
	print("Scaling vectors...")

	# convert categorical features into one-hot-encoded values
	encoder = preprocessing.OneHotEncoder(categorical_features=[6, 22])
	encoder.fit_transform(vector_list).toarray()

	# scale data to distribution with zero mean and unit variance
	scaler = preprocessing.StandardScaler().fit(vector_list)
	scaler.transform(vector_list)
	return vector_list, scaler

def svm_analysis(X_train, y_train, X_test, y_test, grid=False):
	# Perform analysis using Support Vector Machine
	print("Performing Support Vector Machine analysis...")

	# SVM makes predictions!
	if not grid:
		clf = svm.SVC(C=100, gamma=0.0001)
		clf.fit(X_train, y_train)
		score = clf.score(X_test.astype("float64"), y_test.astype("float64"))
		print(score)
		return score

	else:
		tuned_params = [{"C":[5, 10, 100], "kernel":["rbf"],
			"gamma":[0.0001]}]
		clf = model_selection.GridSearchCV(svm.SVC(), tuned_params,
			scoring="accuracy")
		clf.fit(X_train, y_train)

		print(clf.best_params_)
		y_pred = clf.predict(X_test)
		print(metrics.classification_report(y_test, y_pred))

def knn_analysis(X_train, y_train, X_test, y_test, verbose=False, K=5):
	# Uses K-Nearest Neighbors to analyze fight data
	print("Performing K-NN analysis (K = {})...".format(K))

	clf = neighbors.KNeighborsClassifier(K)
	clf.fit(X_train, y_train)

	# K-NN makes predictions!
	if not verbose:
		score = clf.score(X_test.astype("float64"), y_test.astype("float64"))
		print(score)
		return score

	# if verbose, print out probabilities for each prediction
	else:

		prediction_threshhold = 0.8
		thresh_pred = []
		estimates = clf.predict(X_test), clf.predict_proba(X_test)

		for x in range(len(X_test)):
			print("Predicted: {}\tProbabilities: {}, {} \tActual: {}".\
				format(estimates[0][x], estimates[1][x][0], estimates[1][x][1],
					y_test[x]))

			# prediction accuracy with given choice threshold
			prediction = estimates[0][x]
			if estimates[1][x][prediction] >= prediction_threshhold:

				if prediction == y_test[x]:
					thresh_pred.append(1)

				else:
					thresh_pred.append(0)

		print("\nPrediction Accuracy (with threshold = {}):\t{}".format(
			prediction_threshhold, sum(thresh_pred)/len(thresh_pred)))

		return estimates

def decision_tree_analysis(X_train, y_train, X_test, y_test, visual=False,
	d=10):
	# Uses binary decision tree to analyze fight data
	print("Performing Decision Tree analysis (d = {})...".format(d))
	clf = tree.DecisionTreeClassifier(criterion="entropy", max_depth=d)
	clf.fit(X_train, y_train)

	# calculate train and test errors
	tr_acc = clf.score(X_train, y_train)
	te_acc = clf.score(X_test, y_test)

	print("\nAccuracy (d = {}):\t{}".format(
		d, clf.score(X_test, y_test)))

	# graph decision stump
	if visual:
		data = tree.export_graphviz(clf, out_file=None)
		graph = graphviz.Source(data, format="png")
		graph.render("./results/ds_{}".format(d))

def _time_to_minutes(time_string):
	# helper function converts a time string into a number of minutes
	time_elements = time_string.split(":")
	minutes = float(time_elements[0])
	seconds = float(time_elements[1])
	return minutes + seconds/60.0

def _divide_catch(x, y):
	# helper function to catch divide-by-zero errors
	try:
		return x/y
	except ZeroDivisionError:
		return 0

def main():

	# Unpickle scraped objects
	ufc_events = get_event_list()
	ufc_events = sort_events(ufc_events)
	ufc_fighters = get_fighter_list()

	# we need to revert records so that our training data only consists
	# of data that is available at the time of the fight (no future info)
	ufc_fighters = revert_records(ufc_events, ufc_fighters)
	training_set_size = round(len(ufc_events)*TRAINING_TO_TEST_SET_RATIO)

	# syntax
	# ((scaled_vectors, scaler), training_labels)
	training_set = create_vectors(
		ufc_events[:training_set_size], ufc_fighters)

	# create feature, label vectors and scaler out of data matrix
	X_train = np.array(training_set[0][0])
	y_train = np.array(training_set[1])
	scaler = training_set[0][1]

	# Generate testing set
	test_set = create_vectors(ufc_events[training_set_size:], 
		ufc_fighters, scale=False)
	X_test = np.array(test_set[0])
	y_test = np.array(test_set[1])
	scaler.transform(X_test.astype("float64"))  # apply scaler

	# perform analyses of data with machine learning techniques
	print("\n\n################\nAnalysis Results:\n################\n\n")
	svm_result = svm_analysis(X_train, y_train, X_test, y_test)

	knn_results = []
	for x in range(40,45):
		knn_results.append(knn_analysis(X_train, y_train, X_test, y_test, K=x))

	"""plt.plot(range(40,45), knn_results, "r--")
	plt.show()"""

	for x in range(1,11):
		decision_tree_analysis(X_train, y_train, X_test, y_test, visual=True,
			d=x)

if __name__ == '__main__':
	main()