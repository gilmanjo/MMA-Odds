from bs4 import BeautifulSoup
import calendar
from datetime import date
import os
import pickle
import re
import requests
from string import ascii_lowercase
import ufc_objects as ufc


# Constants
ALL_EVENTS_PAGE = "http://www.fightmetric.com/statistics/events/completed?page=all"
ALL_FIGHTERS_PAGE = "http://www.fightmetric.com/statistics/fighters?char=a&page=all"
START_EVENT = "UFC Fight Night: Volkov vs. Struve"
STOP_EVENT = "UFC 26: Ultimate Field Of Dreams"
EVENT_FOLDER = ".//saved_events//"
FIGHTER_FOLDER = ".//saved_fighters//"


def main():
	# get our delicious soup
	soup = BeautifulSoup(requests.get(ALL_EVENTS_PAGE).text, "lxml")

	# scrape all UFC events up to STOP_EVENT
	ufc_events = []
	for row in soup.find_all("a", "b-link b-link_style_black"):

		event_name = row.get_text("|", strip=True)
		strip_event_name = "".join(ch for ch in event_name if ch.isalnum())
		if event_name == STOP_EVENT:
			break

		elif event_name == START_EVENT:
			continue

		# check if data already exists
		elif not os.path.exists(EVENT_FOLDER + strip_event_name + ".pickle"):

			event_soup = BeautifulSoup(requests.get(row["href"]).text, "lxml")
			new_event = scrape_event(event_soup)
			with open(EVENT_FOLDER + strip_event_name + ".pickle", "wb") as f:
				pickle.dump(new_event, f, pickle.HIGHEST_PROTOCOL)
			ufc_events.append(new_event)

	# now let's get our fighter data

	# scrape all UFC fighters in company history
	ufc_fighters = []
	for letter in ascii_lowercase[4:]:

		# update list page URL to next letter in alphabet
		fighters_url = ALL_FIGHTERS_PAGE.replace(
			"char=a", "char={}".format(letter))
		soup = BeautifulSoup(requests.get(fighters_url).text, "lxml")
		
		for row in soup.find_all("tr", "b-statistics__table-row")[1:]:

			# get the fighter's URL
			link = row.find("td").find("a")
			if link is not None:
				link = link["href"]

				# scrape fighter
				fighter_soup = BeautifulSoup(requests.get(link).text, "lxml")
				new_fighter = scrape_fighter(fighter_soup)
				ufc_fighters.append(new_fighter)

				# save to file
				if new_fighter is not None:

					with open(FIGHTER_FOLDER + new_fighter.name + 
							".pickle", "wb") as f:
						pickle.dump(new_fighter, f, pickle.HIGHEST_PROTOCOL)

def scrape_event(event_soup):
	# Scrapes an entire UFC event, given a soup of the event page
	new_event = ufc.Event()
	new_event.name = event_soup.find(
		"h2", "b-content__title").get_text("|", strip=True)
	print("\n\nScraping {}...".format(new_event.name))

	# event details
	event_details = []
	for detail in event_soup.find_all("li", "b-list__box-list-item"):
		event_details.append(str(detail.get_text("|", strip=True)).split("|"))

	if len(event_details[2]) == 2:
		new_event.attendance = event_details[2][1]

	new_event.date = event_details[0][1]
	new_event.location = event_details[1][1]
	
	# obtain links to fight pages
	fight_links = []
	for fight in event_soup.find_all("tr", "b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click"):
		fight_links.append(fight["data-link"])

	# scrape fights
	for i, fight_link in enumerate(fight_links):
		print("Scraping fight #{}...".format(i+1))
		fight_soup = BeautifulSoup(requests.get(fight_link).text, "lxml")
		new_event.fights.append(scrape_fight(fight_soup))

	return new_event

def scrape_fight(fight_soup):
	# Scrapes fight data into a Fight object and returns it
	new_fight = ufc.Fight()

	# get fighter names and winner
	for fighter in fight_soup.find_all("div", "b-fight-details__person"):
		if fighter.find("i").get_text("|", strip=True) == "W":
			new_fight.winner = fighter.find("h3").get_text("|", strip=True)

		new_fight.fighters.append(fighter.find("h3").get_text("|", strip=True))

	# bout type
	fight_details = fight_soup.find("div", "b-fight-details__fight")
	new_fight.bout_type = fight_details.find(
		"i", "b-fight-details__fight-title").get_text("|", strip=True)

	# fight details
	for detail in fight_details.find_all("p", "b-fight-details__text"):
		line = str(detail.get_text("|", strip=True)).split("|")

		if line[0] == "Method:":
			new_fight.method = line[1]
			new_fight.end_round = int(line[3])
			new_fight.end_time = line[5]
			new_fight.num_rounds = line[7][0]

			if len(line) == 10:
				new_fight.referee = line[9]

		elif line[0] == "Details:" and len(line) > 1:
			new_fight.details = ", ".join(line[1:])

	# round data
	round_soups = fight_soup.find_all(
		"section", "b-fight-details__section js-fight-section")
	new_fight.overall_rounds = scrape_rounds("Overall", round_soups[2])
	new_fight.sigstrikes_rounds = scrape_rounds("SigStrikes", round_soups[4])

	return new_fight

def scrape_rounds(round_type, round_soup):
	# Scrapes all the round data for a fight and returns a list of rounds
	rounds = []
	round_data = str(round_soup.get_text("|", strip=True)).split("|")

	if round_type == "Overall":
		headers = ["KD", "Sig. Str.", "Sig. Str. %", "Total Str.",
				"TD", "TD %", "Sub. Att.", "Pass", "Rev."]

		# iterate through rounds
		for i in range(11, len(round_data), 21):
			new_round = ufc.FightRound(round_data[i][6])
			new_round.fighter_stats[round_data[i+1]] = {}
			new_round.fighter_stats[round_data[i+2]] = {}

			# iterate through columns
			for j in range(3, 20, 2):
				new_round.fighter_stats[round_data[i+1]][headers[int((j-3)/2)]] \
					= round_data[i+j]
				new_round.fighter_stats[round_data[i+2]][headers[int((j-3)/2)]] \
					= round_data[i+j+1]

			rounds.append(new_round)

	elif round_type == "SigStrikes":
		headers = ["Sig. Str.", "Sig. Str. %", "Head", "Body",
				"Leg", "Distance", "Clinch", "Ground"]

		# iterate through rounds
		for i in range(10, len(round_data), 19):
			new_round = ufc.FightRound(round_data[i][6])
			new_round.fighter_stats[round_data[i+1]] = {}
			new_round.fighter_stats[round_data[i+2]] = {}

			# iterate through columns
			for j in range(3, 18, 2):
				new_round.fighter_stats[round_data[i+1]][headers[int((j-3)/2)]] \
					= round_data[i+j]
				new_round.fighter_stats[round_data[i+2]][headers[int((j-3)/2)]] \
					= round_data[i+j+1]

			rounds.append(new_round)

	return rounds

def scrape_fighter(fighter_soup):
	# Scrapes fighter's stats, provided the profile is complete
	fighter_name = fighter_soup.find("span", "b-content__title-highlight"
									).get_text("|", strip=True)

	if os.path.exists(FIGHTER_FOLDER + fighter_name + ".pickle"):
		return None

	stats_list = fighter_soup.find_all("li", 
		"b-list__box-list-item b-list__box-list-item_type_block")

	# clean up ripped data
	for x in range(len(stats_list)):
		stats_list[x] = stats_list[x].get_text("|", strip=True).split("|")

	# We don't want the fighter if the reach is unknown
	if stats_list[2][1] == "--":
		print("Skipping {}...".format(fighter_name))
		return None

	# Otherwise, let's scrape all the data
	print("Ripping data for {}...".format(fighter_name))
	new_fighter = ufc.Fighter()

	new_fighter.name = fighter_name

	# record
	record_string = fighter_soup.find("span", "b-content__title-record"
									).get_text("|", strip=True).split()
	record = record_string[1].split("-")
	new_fighter.wins = record[0]
	new_fighter.losses = record[1]
	new_fighter.draws = record[2]

	# if the fighter has no contests
	if len(record_string) > 2:
		new_fighter.ncs = re.findall("\d+", record_string[2])

	# height
	if stats_list[0][1].find("'") != -1:
		height =  [re.findall("\d+", s) for s in stats_list[0][1].split()]
		new_fighter.height = int(height[0][0])*12 + int(height[1][0])

	# weight
	if stats_list[1][1].find("lbs") != -1:
		new_fighter.weight = stats_list[1][1][:stats_list[1][1].find("lbs")]

	if stats_list[2][1].find("\"") != -1:
		new_fighter.reach = int(stats_list[2][1][:2])

	# stance
	if len(stats_list[3]) == 2:
		new_fighter.stance = stats_list[3][1]

	else:
		new_fighter.stance = "Unknown"

	# dob/age
	if stats_list[4][1] != "--":
		new_fighter.dob = date(int(stats_list[4][1][8:12]), 
							list(calendar.month_abbr).index(
								stats_list[4][1][0:3]),
							int(stats_list[4][1][4:6]))

	# career stats
	new_fighter.slpm = stats_list[5][1]
	new_fighter.str_acc = re.findall("\d+", stats_list[6][1])
	new_fighter.sapm = stats_list[7][1]
	new_fighter.str_def = re.findall("\d+", stats_list[8][1])
	new_fighter.td_avg = stats_list[10][1]
	new_fighter.td_acc = re.findall("\d+", stats_list[11][1])
	new_fighter.td_def = re.findall("\d+", stats_list[12][1])
	new_fighter.sub_avg = stats_list[13][1]

	return new_fighter

if __name__ == '__main__':
	main()