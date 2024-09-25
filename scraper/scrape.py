from bs4 import BeautifulSoup, Comment
import time
import requests
import os
import pandas as pd
import re

BASE_URL = "https://www.baseball-reference.com"

#SEA_URL = "https://www.baseball-reference.com/boxes/SEA/SEA202403280.shtml"
#sea_response = requests.get(SEA_URL).text
#sea_soup = BeautifulSoup(sea_response, 'html.parser')

def isComment(elem):
    return isinstance(elem, Comment)

def scrape_game(url, full_route):
    event_list = []
    game_response = requests.get(url).text
    game_soup = BeautifulSoup(game_response, 'html.parser')

    pbp = game_soup.find_all(string=lambda string:isinstance(string, Comment))
    for comment in pbp:
        if "div_play_by_play" in comment:
            x = 0
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
                        #print("Total pitches: {}; Balls: {}; Strikes: {}; Mix: {}".format(total_pitches, balls, strikes, pitch_assortment))
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
                    
                    # # outcome_tag.string format one of- <Strikeout Swinging;;Flyball: RF/CF/LF;;Single to X;;Walk; <First initial>.&nbsp;<last name> to XB/??;;
                    # # Groundout: 3B-2B/Forceout at XB; <First initial>.&nbsp;<last name> to XB>;;Walk, Wild Pitch; J.&nbsp;Mateo to 3B;;
                    # # Flyball: RF/Sacrifice Fly (Deep RF); J.&nbsp;Mateo Scores;Foul Popfly: 3B (3B into Foul Terr.)>

                    # print("inning = {}".format(inning.text))
                    # print("SCORE:: batting: {}; fielding: {}".format(score_for, score_against))
                    # print("Inning outs: {}".format(inning_outs))
                    # if runner_first:
                    #     print("Runner on first base")
                    # if runner_second:
                    #     print("Runner on second base")
                    # if runner_third:
                    #     print("Runner on third base")
                    # print("Total pitches: {}; Balls: {}; Strikes: {}".format(total_pitches, balls, strikes))
                    # print("Runs from play: {}".format(str(runs_from_play)))
                    # print("Outs from play: {}".format(str(outs_from_play)))
                    # print("batter = {}".format(batter))
                    # print("pitcher = {}".format(pitcher))
                    # print("outcome = {}".format(outcome_tag.text))
                    event_data = {'inning_half': inning.text, 'score_for': score_for, 'score_against': score_against, 
                                  'inning_outs': inning_outs, 'runner_first': runner_first,'runner_second': runner_second,
                                  'runner_third': runner_third, 'total_pitches': total_pitches, 'balls': balls, 
                                  'strikes': strikes, 'pitch_assortment': pitch_assortment, 'runs_from_play': runs_from_play, 
                                  'outs_from_play': outs_from_play, 'batter': batter, 'pitcher': pitcher, 'outcome': outcome_tag.text}
                    event_list.append(event_data)
                    
                    # print(x)
                    # x = x + 1
                if "<tr class=\"ingame_substitution" in line:
                    #print("substitution:")
                    substitution_soup = BeautifulSoup(line, 'html.parser')
                    replacement_action = substitution_soup.find('td', {"data-stat": "inning_summary_3"}).find('div')
                    #print(replacement_action.text)
                    # Need to fix tilde and enye chars
                    # <Replacement player> <replacement action> for <Replaced Player> <position> batting <batting order>
                    
                    replacement_data = {'replacement': replacement_action.text}
                    event_list.append(replacement_data)
                if "Challenge" in line:
                    challenge_soup = BeautifulSoup(line, 'html.parser')
                    challege_action = challenge_soup.find('span', {"class": "ingame_substitution"})
                    #print(challege_action.text)
                    # <Play> Challenged by <TEAM 3 char> manager (<manager name>): Original call <result>
                    
                    challenge_data = {'challenge': challege_action.text}
                    event_list.append(challenge_data)
    if len(event_list) > 0:
        # Ultimate goal for DF structure
        # df = pd.DataFrame(columns=['...','Substitution_Position','Substitution_Pitcher','Challenge_Overturned','Challenge_Upheld'])

        df = pd.DataFrame(event_list, columns=['inning_half','score_for','score_against','inning_outs','runner_first','runner_second','runner_third',
                                  'total_pitches','balls','strikes','pitch_assortment','runs_from_play','outs_from_play','batter','pitcher',
                                  'outcome','substitution','challenge'])

        df.to_parquet(full_route, engine='fastparquet')


year = 2020
query_url = "https://www.baseball-reference.com/leagues/majors/{}-schedule.shtml".format(year)
year_response = requests.get(query_url).text
year_soup = BeautifulSoup(year_response, 'html.parser')

section_wrapper_tags = year_soup.find_all("div", class_="section_wrapper") #{"class": "section_wrapper"})
regular_season_games = section_wrapper_tags[0].find_all("p", class_="game")
post_season_games = section_wrapper_tags[1].find_all("p", class_="game")
print("Length {} Postseason {}".format(len(regular_season_games), len(post_season_games)))

time.sleep(3)

# for game in games_tag:
#     try:
#         suffix = game.em.a["href"]
#         if "/previews/" in suffix:
#             # Future game
#             # https://www.baseball-reference.com/previews/2024/CHN202409290.shtml
#             continue
#         uri = BASE_URL + suffix
#         filename = "{}.parquet".format(uri.split('/')[5].split('.')[0])
#         dir = "{}/{}/{}".format('data', year, filename[3:11])
#         full_route = "{}/{}".format(dir, filename)
#         if not os.path.exists(dir):
#             os.makedirs(dir)
#         if os.path.isfile(full_route):
#             # Game already saved
#             continue
#         scrape_game(uri, full_route)
#         time.sleep(3)
#     except AttributeError:
#         time.sleep(3)
#         continue
# print("Total games: {}".format(len(games_tag)))

for game in regular_season_games:
    try:
        suffix = game.em.a["href"]
        if "/previews/" in suffix:
            # Future game
            # https://www.baseball-reference.com/previews/2024/CHN202409290.shtml
            continue
        uri = BASE_URL + suffix
        filename = "{}.parquet".format(uri.split('/')[5].split('.')[0])
        dir = "{}/{}/{}/{}".format('data', year, 'season', filename[3:11])
        full_route = "{}/{}".format(dir, filename)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if os.path.isfile(full_route):
            # Game already saved
            continue
        scrape_game(uri, full_route)
        time.sleep(3)
    except AttributeError:
        time.sleep(3)
        continue
print("Total regular season games: {}".format(len(regular_season_games)))

for game in post_season_games:
    try:
        suffix = game.em.a["href"]
        if "/previews/" in suffix:
            # Future game
            # https://www.baseball-reference.com/previews/2024/CHN202409290.shtml
            continue
        uri = BASE_URL + suffix
        filename = "{}.parquet".format(uri.split('/')[5].split('.')[0])
        dir = "{}/{}/{}/{}".format('data', year, 'postseason', filename[3:11])
        full_route = "{}/{}".format(dir, filename)
        if not os.path.exists(dir):
            os.makedirs(dir)
        if os.path.isfile(full_route):
            # Game already saved
            continue
        scrape_game(uri, full_route)
        time.sleep(3)
    except AttributeError:
        time.sleep(3)
        continue
print("Total post season games: {}".format(len(post_season_games)))
