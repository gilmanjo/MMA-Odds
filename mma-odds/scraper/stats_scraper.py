from bs4 import BeautifulSoup
import os
import pickle
import requests
import ufc_objects as ufc


# Constants
ALL_EVENTS_PAGE = "http://www.fightmetric.com/statistics/events/completed?page=all"
STOP_EVENT = "UFC 20: Battle for the Gold"
EVENT_FOLDER = ".//saved_events//"


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

		# check if data already exists
		elif not os.path.exists(EVENT_FOLDER + strip_event_name + ".pickle"):

			event_soup = BeautifulSoup(requests.get(row["href"]).text, "lxml")
			new_event = scrape_event(event_soup)
			with open(EVENT_FOLDER + strip_event_name + ".pickle", "wb") as f:
				pickle.dump(new_event, f, pickle.HIGHEST_PROTOCOL)
			ufc_events.append(new_event)

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
			new_fight.referee = line[9]

		elif line[0] == "Details:":
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

if __name__ == '__main__':
	main()