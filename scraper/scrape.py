from bs4 import BeautifulSoup, Comment
import time
import requests
import os
import pandas as pd
import re

BASE_URL = "https://www.baseball-reference.com"
QUERY_YEAR_URL = "https://www.baseball-reference.com/leagues/majors/2023-schedule.shtml"
MANUAL_TEST_URL = "https://www.baseball-reference.com/boxes/SFN/SFN202305090.shtml"

year_response = requests.get(QUERY_YEAR_URL).text

#SEA_URL = "https://www.baseball-reference.com/boxes/SEA/SEA202403280.shtml"
#sea_response = requests.get(SEA_URL).text
#sea_soup = BeautifulSoup(sea_response, 'html.parser')

def isComment(elem):
    return isinstance(elem, Comment)

def scrape_game(url):
    event_list = []
    game_response = requests.get(url).text
    game_soup = BeautifulSoup(game_response, 'html.parser')

    pbp = game_soup.find_all(string=lambda string:isinstance(string, Comment))
    for comment in pbp:
        if "div_play_by_play" in comment:
            x = 0
            for line in comment.string.splitlines():
                # if "pbp_summary_top" in line:
                    # I don't think there's anything valuable we don't already have here
                    # print("Top Summary:")
                    # print(line)
                    # <Top/Bottom> of the <inning>, <Team full name> Batting, <Ahead/Behind> <batters team perspective score x-x>, 
                    # <Team full name>' <Pitcher name> facing <next three batter positions, x-y-z>
                    # print(x)
                    # x = x + 1
                # I don't think there's anything valuable we don't already have here
                # if "pbp_summary_bottom" in line:
                #     print("Bottom Summary:")
                #     print(line)
                #     # <X> runs, <X> hits, <X> errors, <X> LOB. <Team name> <Score> <Team name> <Score>.
                #     print(x)
                #     x = x + 1
                if "event_" in line:
                    #print("event:")
                    event_soup = BeautifulSoup(line, 'html.parser')
                    inning = event_soup.find('th', {"data-stat": "inning"})
                    score_tag = event_soup.find('td', {"data-stat": "score_batting_team"})
                    score_for = int(score_tag.text[0])
                    score_against = int(score_tag.text[2])
                    outs_tag = event_soup.find('td', {"data-stat": "outs"})
                    inning_outs = int(outs_tag.text)
                    runners_tag = event_soup.find('td', {"data-stat": "runners_on_bases_pbp"})
                    runner_first = True if '1' == runners_tag.text[0] else False
                    runner_second = True if '2' == runners_tag.text[1] else False
                    runner_third = True if '3' == runners_tag.text[2] else False
                    pitches_tag = event_soup.find('td', {"data-stat": "pitches_pbp"})
                    if pitches_tag:
                        total_pitches = int(pitches_tag.text[0])
                        balls = int(pitches_tag.text[3])
                        strikes = int(pitches_tag.text[5])
                    else:
                        total_pitches = 0
                        balls = 0
                        strikes = 0
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
                    event_data = {'inning_half': inning.text, 'score_for': score_for, 'score_against': score_against, 'inning_outs': inning_outs, 
                                'runner_first': runner_first,'runner_second': runner_second,'runner_third': runner_third, 
                                'total_pitches': total_pitches, 'balls': balls, 'strikes': strikes, 'runs_from_play': runs_from_play, 
                                'outs_from_play': outs_from_play, 'batter': batter, 'pitcher': pitcher, 'outcome': outcome_tag.text}
                    event_list.append(event_data)
                    
                    print(x)
                    x = x + 1
                if "<tr class=\"ingame_substitution" in line:
                    #print("substitution:")
                    substitution_soup = BeautifulSoup(line, 'html.parser')
                    replacement_action = substitution_soup.find('td', {"data-stat": "inning_summary_3"}).find('div')
                    #print(replacement_action.text)
                    # Need to fix tilde and enye chars
                    # <Replacement player> <replacement action> for <Replaced Player> <position> batting <batting order>
                    
                    replacement_data = {'replacement': replacement_action.text}
                    event_list.append(replacement_data)
                    # print(x)
                    # x = x + 1
                if "Challenge" in line:
                    #print("challenge:")
                    challenge_soup = BeautifulSoup(line, 'html.parser')
                    challege_action = challenge_soup.find('span', {"class": "ingame_substitution"})
                    #print(challege_action.text)
                    # <Play> Challenged by <TEAM 3 char> manager (<manager name>): Original call <result>
                    
                    challenge_data = {'challenge': challege_action.text}
                    event_list.append(challenge_data)
                    # print(x)
                    # x = x + 1
    if len(event_list) > 0:
        #print("event list is this big: {}".format(len(event_list)))

        # Ultimate goal for DF structure
        # df = pd.DataFrame(columns=['...','Substitution_Position','Substitution_Pitcher','Challenge_Overturned','Challenge_Upheld'])

        #TODO wipe out event_list with temp code to prevent too much run on test
        #event_list = []
        df = pd.DataFrame(event_list, columns=['inning_half','score_for','score_against','inning_outs','runner_first','runner_second','runner_third',
                                  'total_pitches','balls','strikes','runs_from_play','outs_from_play','batter','pitcher',
                                  'outcome','substitution','challenge'])
        #print("df is this big: {}".format(len(df)))
        # TODO need dynamic filename
        filename = "{}.parquet".format(url.split('/')[5].split('.')[0])
        dir = "{}/{}".format('data', filename[3:11])
        if not os.path.exists(dir):
            os.makedirs(dir)
    
        full_route = "{}/{}".format(dir, filename)
        #print(full_route)
        df.to_parquet(full_route, engine='fastparquet')




year_soup = BeautifulSoup(year_response, 'html.parser')
test_games = year_soup.find_all("p", class_="game")

# This extracts SEA home game URLS
sea_games = 0
# for game in test_games:
#     time.sleep(3)
#     try:
#         suffix = game.em.a["href"]
#         if "/previews/" in suffix:
#             # Future game
#             # https://www.baseball-reference.com/previews/2024/CHN202409290.shtml
#             continue
#         # if "/SEA/" not in suffix:
#         #     continue
#         #sea_games = sea_games + 1
#         #print(BASE_URL + suffix)
#         scrape_game(BASE_URL + suffix)
#     except AttributeError:
#         # No link to boxscore exists (future game?)
#         continue
# print("Total games: {}, Sea games: {}".format(len(test_games), sea_games))

scrape_game(MANUAL_TEST_URL)

# # Scorebox Test
#scorebox = sea_soup.find("div", {"class": "scorebox_meta"})
# try:
#     print(scorebox.prettify())
# except AttributeError:
#     print("attribute error")

# table = sea_soup.findAll('table')[0].findAll('tr')
# for row in table:
#     try:
#         print(row.prettify())
#     except AttributeError:
#         continue
