import datetime
import os
import sys
import urllib.request
import json
import time
import dateutil.parser

# You need a file named private_key in order for this to work
try:
    private_file = open('private_key')
except FileNotFoundError:
    print('You must put your IFTTT private webhook key in a file named private_key')
    exit()

IFTTT_KEY = private_file.readline().strip()
MAX_DELAY = 600
MIN_DELAY = 20

private_file.close()


class Game:
    def __init__(self, home, away, home_score, away_score, game_date):
        self.home = Team(home, home_score)
        self.away = Team(away, away_score)
        self.game_date = game_date
        self.game_status = None

    def time_delay(self):
        if self.game_status == 'Live':
            return MIN_DELAY
        now = datetime.datetime.now(datetime.timezone.utc)
        time_delta = (game_date - now).total_seconds()
        if time_delta < 0 and self.game_status == 'Preview':
            return MIN_DELAY
        if time_delta > 0:
            return min(MAX_DELAY, time_delta)
        # This means the game is over and we should get rid of it
        return False


class Team:
    def __init__(self, team_name, team_score):
        self.team_name = team_name
        self.team_abbr = NHLTeams.team_dict[team_name]
        self.team_abbr_lower = self.team_abbr.lower()
        self.__last_score = team_score
        self.last_score = team_score
        self.__in_power_play = False
        self.in_power_play = False
        self.team = None

    @property
    def last_score(self):
        return self.__last_score

    @last_score.setter
    def last_score(self, value):
        if value != self.__last_score:
            self.notify_of_score()
            self.__last_score = value

    @property
    def in_power_play(self):
        return self.__in_power_play

    @in_power_play.setter
    def in_power_play(self, value):
        if value != self.__in_power_play:
            if value:
                self.notify_of_power_play()
            self.__in_power_play = value

    def notify_of_score(self):
        print('SCORE', self.team_abbr)
        notification = 'https://maker.ifttt.com/trigger/{team}_score/with/key/{ifttt}'.format(team=self.team_abbr_lower,
                                                                                              ifttt=IFTTT_KEY)
        print('Sending', notification)
        with urllib.request.urlopen(notification) as notify:
            raw_response = notify.read()

    def notify_of_power_play(self):
        print('PP', self.team_abbr)
        notification = 'https://maker.ifttt.com/trigger/{team}_power_play/with/key/{ifttt}'.format(team=self.team_abbr_lower,
                                                                                                   ifttt=IFTTT_KEY)
        print('Sending', notification)
        with urllib.request.urlopen(notification) as notify:
            raw_response = notify.read()


class NHLTeams:
    team_dict = {"Anaheim Ducks": "ANA",
                 "Arizona Coyotes": "ARI",
                 "Boston Bruins": "BOS",
                 "Buffalo Sabres": "BUF",
                 "Carolina Hurricanes": "CAR",
                 "Columbus Blue Jackets": "CBJ",
                 "Calgary Flames": "CGY",
                 "Chicago Blackhawks": "CHI",
                 "Colorado Avalanche": "COL",
                 "Dallas Stars": "DAL",
                 "Detroit Red Wings": "DET",
                 "Edmonton Oilers": "EDM",
                 "Florida Panthers": "FLA",
                 "Los Angeles Kings": "LAK",
                 "Minnesota Wild": "MIN",
                 "Montreal Canadiens": "MTL",
                 "New Jersey Devils": "NJD",
                 "Nashville Predators": "NSH",
                 "New York Islanders": "NYI",
                 "New York Rangers": "NYR",
                 "Ottawa Senators": "OTT",
                 "Philadelphia Flyers": "PHI",
                 "Pittsburgh Penguins": "PIT",
                 "San Jose Sharks": "SJS",
                 "St. Louis Blues": "STL",
                 "Tampa Bay Lightning": "TBL",
                 "Toronto Maple Leafs": "TOR",
                 "Vancouver Canucks": "VAN",
                 "Vegas Golden Knights": "VGK",
                 "Winnipeg Jets": "WPG",
                 "Washington Capitals": "WSH"
                 }


games = dict()

while True:
    try:
        with urllib.request.urlopen('https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.linescore') as response:
            raw_json = response.read().decode('utf8')
            # with open(os.path.join(os.path.dirname(__file__), 'raw_data', str(time.time()) + '.json'), 'w') as json_file:
            #     json_file.write(raw_json)
            #     json_file.close()

        json_data = json.loads(raw_json)
        live_game = False
        for game in json_data['dates'][0]['games']:
            game_pk = game['gamePk']
            game_date = dateutil.parser.parse(game['gameDate'])
            if game_pk not in games:
                games[game_pk] = Game(game['teams']['home']['team']['name'],
                                      game['teams']['away']['team']['name'],
                                      game['teams']['home']['score'],
                                      game['teams']['away']['score'],
                                      game_date)
            games[game_pk].game_status = game['status']['abstractGameState']
            games[game_pk].home.last_score = game['teams']['home']['score']
            games[game_pk].away.last_score = game['teams']['away']['score']
            games[game_pk].home.in_power_play = game['linescore']['teams']['home']['powerPlay']
            games[game_pk].away.in_power_play = game['linescore']['teams']['away']['powerPlay']
            # print(game['teams']['away']['team']['name'], game['teams']['away']['score'])
            # print(game['teams']['home']['team']['name'], game['teams']['home']['score'])
        delay_for_repeat = MAX_DELAY
        for k in games.keys():
            d = games[k].time_delay()
            if not d:
                del games[k]
            else:
                delay_for_repeat = min(d, delay_for_repeat)
        print('Sleeping for', delay_for_repeat)
        sys.stdout.flush()
        time.sleep(delay_for_repeat)
    except Exception as e:
        # If anything goes wrong with the load then retry in MIN_DELAY sec
        print('Exception', e)
        time.sleep(MIN_DELAY)



