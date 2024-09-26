from bs4 import BeautifulSoup, Comment
import time
import requests
import os
import pandas as pd

BASE_URL = "https://www.baseball-reference.com"
REG_SEASON = "season"
POSTSEASON = "postseason"

def isComment(elem):
    return isinstance(elem, Comment)

def scrape_game(url, full_route):
    event_list = []
    game_response = requests.get(url).text
    game_soup = BeautifulSoup(game_response, 'html.parser')

    pbp = game_soup.find_all(string=lambda string:isinstance(string, Comment))
    for comment in pbp:
        if "div_play_by_play" in comment:
            for line in comment.string.splitlines():
                if "event_" in line:
                    #print("event:")
                    event_soup = BeautifulSoup(line, 'html.parser')
                    inning = event_soup.find('th', {"data-stat": "inning"})
                    score_tag = event_soup.find('td', {"data-stat": "score_batting_team"})
                    score_for = int(score_tag.text.split('-')[0])
                    score_against = int(score_tag.text.split('-')[1])
                    outs_tag = event_soup.find('td', {"data-stat": "outs"})
                    inning_outs = int(outs_tag.text)
                    runners_tag = event_soup.find('td', {"data-stat": "runners_on_bases_pbp"})
                    runner_first = True if '1' == runners_tag.text[0] else False
                    runner_second = True if '2' == runners_tag.text[1] else False
                    runner_third = True if '3' == runners_tag.text[2] else False
                    pitches_tag = event_soup.find('td', {"data-stat": "pitches_pbp"})
                    if pitches_tag.text != "":
                        if pitches_tag.text.split(',')[0] != '':
                            total_pitches = int(pitches_tag.text.split(',')[0])
                        if pitches_tag.text.split(',')[1].split('-')[0] != '':
                            balls = int(pitches_tag.text.split(',')[1].split('-')[0] [1:])
                        else:
                            balls = 0
                        strikes = int(pitches_tag.text.split(',')[1].split('-')[1].split(')')[0])
                        pitch_assortment = pitches_tag.text.split(',')[1].split('-')[1].split(')')[1][1:]
                    else:
                        total_pitches = 0
                        balls = 0
                        strikes = 0
                        pitch_assortment = ""
                    runs_outs_results_tag = event_soup.find('td', {"data-stat": "runs_outs_result"})
                    if runs_outs_results_tag:
                        runs_from_play = runs_outs_results_tag.text.count('R') or 0
                        outs_from_play = runs_outs_results_tag.text.count('O') or 0
                    else:
                        runs_from_play = 0
                        outs_from_play = 0
                    batter_tag = event_soup.find('td', {"data-stat": "batter"})
                    batter = batter_tag.text
                    pitcher_tag = event_soup.find('td', {"data-stat": "pitcher"})
                    pitcher = pitcher_tag.text
                    outcome_tag = event_soup.find('td', {"data-stat": "play_desc"})
                    
                    # # outcome_tag.string format one of- 
                    # Strikeout Swinging
                    # Flyball: RF/CF/LF
                    # Single to X
                    # Walk; <First initial>.&nbsp;<last name> to XB/??
                    # Groundout: 3B-2B/Forceout at XB; <First initial>.&nbsp;<last name> to XB>
                    # Walk, Wild Pitch; J.&nbsp;Mateo to 3B
                    # Flyball: RF/Sacrifice Fly (Deep RF); J.&nbsp;Mateo Scores;Foul Popfly: 3B (3B into Foul Terr.)

                    event_data = {'inning_half': inning.text, 'score_for': score_for, 'score_against': score_against, 
                                  'inning_outs': inning_outs, 'runner_first': runner_first,'runner_second': runner_second,
                                  'runner_third': runner_third, 'total_pitches': total_pitches, 'balls': balls, 
                                  'strikes': strikes, 'pitch_assortment': pitch_assortment, 'runs_from_play': runs_from_play, 
                                  'outs_from_play': outs_from_play, 'batter': batter, 'pitcher': pitcher, 
                                  'outcome': outcome_tag.text}
                    event_list.append(event_data)
                if "<tr class=\"ingame_substitution" in line:
                    substitution_soup = BeautifulSoup(line, 'html.parser')
                    replacement_action = substitution_soup.find('td', {"data-stat": "inning_summary_3"}).find('div')
                    # TODO Need to fix tilde and enye chars
                    # <Replacement player> <replacement action> for <Replaced Player> <position> batting <batting order>
                    
                    replacement_data = {'replacement': replacement_action.text}
                    event_list.append(replacement_data)
                if "Challenge" in line:
                    challenge_soup = BeautifulSoup(line, 'html.parser')
                    challege_action = challenge_soup.find('span', {"class": "ingame_substitution"})
                    # <Play> Challenged by <TEAM 3 char> manager (<manager name>): Original call <result>
                    
                    challenge_data = {'challenge': challege_action.text}
                    event_list.append(challenge_data)
    if len(event_list) > 0:
        # Ultimate goal for DF structure
        # pd.DataFrame(columns=[...,'Substitution_Position','Substitution_Pitcher','Challenge_Overturned','Challenge_Upheld'])

        df = pd.DataFrame(event_list, columns=['inning_half','score_for','score_against','inning_outs','runner_first',
                                               'runner_second','runner_third','total_pitches','balls','strikes',
                                               'pitch_assortment','runs_from_play','outs_from_play','batter','pitcher',
                                               'outcome','substitution','challenge'])

        df.to_parquet(full_route, engine='fastparquet')

def extract_data(game, season):
    try:
        suffix = game.em.a["href"]
        # Ensure not future game
        if "/previews/" not in suffix:
            uri = BASE_URL + suffix
            filename = "{}.parquet".format(uri.split('/')[5].split('.')[0])
            dir = "{}/{}/{}/{}".format('data', year, season, filename[3:11])
            full_route = "{}/{}".format(dir, filename)
            # Ensure dir exists
            if not os.path.exists(dir):
                os.makedirs(dir)
            # Only scrape if file doesn't exist
            if not os.path.isfile(full_route):
                scrape_game(uri, full_route)
                time.sleep(3)  
    except AttributeError:
        print("error occurred")
        time.sleep(3)


year = 2020
query_url = "https://www.baseball-reference.com/leagues/majors/{}-schedule.shtml".format(year)
year_response = requests.get(query_url).text
year_soup = BeautifulSoup(year_response, 'html.parser')

section_wrapper_tags = year_soup.find_all("div", class_="section_wrapper") #{"class": "section_wrapper"})
regular_season_games = section_wrapper_tags[0].find_all("p", class_="game")
post_season_games = section_wrapper_tags[1].find_all("p", class_="game")
print("Length {} Postseason {}".format(len(regular_season_games), len(post_season_games)))
time.sleep(3)

for game in regular_season_games:
    extract_data(game, REG_SEASON)

for game in post_season_games:
    extract_data(game, POSTSEASON)
