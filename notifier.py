import datetime
import os
import sys
import traceback
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

NHL = True
ECHL = True

private_file.close()


class ECHLGame:
    def __init__(self, home, away, home_score, away_score, started, final):
        self.home = Team(home, home_score, 'echl')
        self.away = Team(away, away_score, 'echl')
        self.started = started
        self.final = final

    def time_delay(self):
        if self.started == 1 and self.final == 0:
            return MIN_DELAY
        if self.started == 0:
            return MAX_DELAY
        # This means the game is over and we should get rid of it
        return False


class NHLGame:
    def __init__(self, home, away, home_score, away_score, game_date):
        self.home = Team(home, home_score)
        self.away = Team(away, away_score)
        self.game_date = game_date
        self.game_status = None

    def time_delay(self):
        if self.game_status == 'Live':
            return MIN_DELAY
        now = datetime.datetime.now(datetime.timezone.utc)
        time_delta = (self.game_date - now).total_seconds()
        if time_delta < 0 and self.game_status == 'Preview':
            return MIN_DELAY
        if time_delta > 0:
            return min(MAX_DELAY, time_delta)
        # This means the game is over and we should get rid of it
        return False


class Team:
    def __init__(self, team_name, team_score, league="nhl"):
        self.team_name = team_name
        self.league = league
        if len(team_name) <= 3:
            self.team_abbr = team_name
        else:
            self.team_abbr = NHLTeams.team_dict[team_name]
        self.team_abbr_lower = self.team_abbr.lower()
        self.__last_score = team_score
        self.last_score = team_score
        self.__in_power_play = False
        self.in_power_play = False
        self.team = None
        self.__power_play_count = None
        self.power_play_count = None

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

    @property
    def power_play_count(self):
        return self.__power_play_count

    @power_play_count.setter
    def power_play_count(self, value):
        if value is not None:
            value = int(value)
        if self.__power_play_count is None:
            self.__power_play_count = value
        else:
            if value > self.__power_play_count:
                self.notify_of_power_play()
                self.__power_play_count = value

    def notify_of_score(self):
        print(self.last_score)
        print('SCORE', self.team_abbr)
        print(vars(self))
        preamble = ""
        if self.league != 'nhl':
            preamble = self.league+"_"
        notification = ('https://maker.ifttt.com/trigger/'
                        '{preamble}{team}_score/with/key/{ifttt}'.format(team=self.team_abbr_lower,
                                                                         ifttt=IFTTT_KEY,
                                                                         preamble=preamble))
        print('Sending', notification)
        with urllib.request.urlopen(notification) as notify:
            raw_response = notify.read()

    def notify_of_power_play(self):
        print('PP', self.team_abbr)
        preamble = ""
        if self.league != 'nhl':
            preamble = self.league + "_"
        notification = ('https://maker.ifttt.com/trigger/'
                        '{preamble}{team}_power_play/with/key/{ifttt}'.format(team=self.team_abbr_lower,
                                                                              ifttt=IFTTT_KEY,
                                                                              preamble=preamble))
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


nhl_games = dict()
echl_games = dict()


def check_nhl():
    try:
        delay = MAX_DELAY
        with urllib.request.urlopen('https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.linescore') as response:
            raw_json = response.read().decode('utf8')
            # with open(os.path.join(os.path.dirname(__file__), 'raw_data', str(time.time()) + '.json'), 'w') as json_file:
            #     json_file.write(raw_json)
            #     json_file.close()

        json_data = json.loads(raw_json)
        for game in json_data['dates'][0]['games']:
            game_pk = game['gamePk']
            game_date = dateutil.parser.parse(game['gameDate'])
            if game_pk not in nhl_games:
                nhl_games[game_pk] = NHLGame(game['teams']['home']['team']['name'],
                                             game['teams']['away']['team']['name'],
                                             game['teams']['home']['score'],
                                             game['teams']['away']['score'],
                                             game_date)
            nhl_games[game_pk].game_status = game['status']['abstractGameState']
            nhl_games[game_pk].home.last_score = game['teams']['home']['score']
            nhl_games[game_pk].away.last_score = game['teams']['away']['score']
            nhl_games[game_pk].home.in_power_play = game['linescore']['teams']['home']['powerPlay']
            nhl_games[game_pk].away.in_power_play = game['linescore']['teams']['away']['powerPlay']
            # print(game['teams']['away']['team']['name'], game['teams']['away']['score'])
            # print(game['teams']['home']['team']['name'], game['teams']['home']['score'])

        for k in list(nhl_games.keys()):
            d = nhl_games[k].time_delay()
            if not d:
                del nhl_games[k]
            else:
                delay = min(d, delay)
        return delay
    except Exception as e:
        # If anything goes wrong with the load then retry in MIN_DELAY sec
        print('Exception', e)
        traceback.print_exc()
        return MIN_DELAY


def check_echl():
    try:
        delay = MAX_DELAY
        preamble = 'angular.callbacks._1i'
        today = '{dt.year}-{dt.month}-{dt.day}'.format(dt=datetime.datetime.now())
        echl_url = 'https://lscluster.hockeytech.com/feed/index.php?feed=statviewfeed&view=schedule_day&date={today}&site_id=1&key=e18cfddba0db3b21&client_code=echl&league_id=1&season_id=46&team=-1&lang=en&forceDate=false&callback=angular.callbacks._1i'.format(today=today)
        with urllib.request.urlopen(echl_url) as response:
            raw_json = response.read().decode('utf8')
            raw_json = raw_json[len(preamble)+1:-1]
            # with open(os.path.join(os.path.dirname(__file__), 'raw_data', str(time.time()) + '.json'), 'w') as json_file:
            #     json_file.write(raw_json)
            #     json_file.close()

        json_data = json.loads(raw_json)
        for game in json_data:
            game_pk = game['id']
            if game_pk not in echl_games:
                echl_games[game_pk] = ECHLGame(game['homeTeam']['info']['abbreviation'],
                                               game['visitingTeam']['info']['abbreviation'],
                                               int(game['homeTeam']['stats']['goals']),
                                               int(game['visitingTeam']['stats']['goals']),
                                               int(game['started']),
                                               int(game['final']))
            echl_games[game_pk].home.last_score = int(game['homeTeam']['stats']['goals'])
            echl_games[game_pk].away.last_score = int(game['visitingTeam']['stats']['goals'])
            echl_games[game_pk].home.power_play_count = int(game['homeTeam']['stats']['powerPlayOpportunities'])
            echl_games[game_pk].away.power_play_count = int(game['visitingTeam']['stats']['powerPlayOpportunities'])
            echl_games[game_pk].started = int(game['started'])
            echl_games[game_pk].final = int(game['final'])

        for k in list(echl_games.keys()):
            d = echl_games[k].time_delay()
            if not d:
                del echl_games[k]
            else:
                delay = min(d, delay)
        return delay
    except Exception as e:
        # If anything goes wrong with the load then retry in MIN_DELAY sec
        print('Exception', e)
        traceback.print_exc()
        return MIN_DELAY


# check_echl()

while True:
    delay_for_repeat = MAX_DELAY
    # NHL
    if NHL:
        delay_for_repeat = min(delay_for_repeat, check_nhl())
    if ECHL:
        delay_for_repeat = min(delay_for_repeat, check_echl())
    sys.stdout.flush()
    time.sleep(delay_for_repeat)




