from bs4 import BeautifulSoup
import pickle
import requests
import ufc_objects as ufc


def main():
	# TODO: Get the URLs for *all* of the fights
	test_url = requests.get("http://www.fightmetric.com/fight-details/5be97c1fa222093d")
	soup = BeautifulSoup(test_url.text, "lxml")

	# name of event
	print(soup.h2.get_text("|", strip=True))
	test_fight = scrape_fight(soup)

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