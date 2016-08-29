from __future__ import print_function
import sys
import requests
from bs4 import BeautifulSoup
from xml.dom import minidom

BASE_URL = "http://espnfc.us"
SUMMARY_URL = BASE_URL + "/scores/xhr?=1"
getQuery = lambda matchId: "http://query.yahooapis.com/v1/public/" + \
            "yql?q=select%20*%20from%20xml%20where%20url%3D%22http%3A%2F%2Fwww.espnfc.com%2Fgamepackage10%2Fdata%2Fgamecast%3FgameId%3D" + \
            matchId + \
            "%26langId%3D0%26snap%3D0%22"

nots = {}

def get_match_goaldata(matchId,send_notif):
    lst = queryXMLParsedResults(getQuery(matchId),matchId,send_notif)
    return lst
def get_matches_summary():
    """
    returns a dictionary of match-items with league name as key
    the match-items themselves are dictionaries with match-id as key

    returns None on error

    """

    # TODO: clean-up
    try:
        summary = (requests.get("http://www.espnfc.us/scores?xhr=1", timeout = 5)).json()
    except Exception as err:
        print ('get_matches_summary: Exception: ', err, file=sys.stderr)
        return None

    soup = BeautifulSoup(summary['content']['html'], "lxml").findAll("div", id="score-leagues")
    dictOfLeagues = {}
    for leagues in soup:
        leauge = leagues.findAll("div",{"class":"score-league"})
        #extracting leauges
        for match in leauge:
            nameOfLeague = match.find("h4")
            dictOfMatches = {}
            x = match.findAll("div",{"class":"score-group"})
            #extracting all matches in the current league
            for y in x:
                x = y.find("p")
                datas = y.findAll("div",{"class":"score-box"})
                if datas:
                    for data in datas:
                        team_names = data.findAll("div",{"class":"team-name"})
                        scores = data.findAll("div",{"class":"team-scores"})
                        score = scores[0].findAll("span")

                        score_summary = team_names[0].get_text().strip()
                        if score[0].get_text().strip():
                            score_summary += " : " +  score[0].get_text().strip()

                        score_summary += " v "
                        score_summary += team_names[1].get_text().strip()
                        if score[1].get_text().strip():
                            score_summary += " : " +  score[1].get_text().strip()

                        idy = data.find("div",{"class":"score full"})
                        live = data.find("div",{"class":"game-info"})
                        status = ""
                        if live:
                            spans = live.findAll("span")
                            for span in spans:
                                status += span.get_text().strip() + " "
                        link = data.find("a",{"class":"primary-link"})
                        extra_info = data.find('div',{"class":"extra-game-info"})
                        info = ""
                        if extra_info:
                            spans = extra_info.findAll('span')
                            for span in spans:
                                info +=  span.get_text().strip() + " "


                        dictOfMatches[idy['data-gameid']] = {
                            'id':            idy['data-gameid'],
                            'score_summary': score_summary,
                            'url':           link['href'],
                            'status':        status,
                            'extra_info':    info,
                            'leauge':        nameOfLeague.get_text().strip()
                        }

            dictOfLeagues[nameOfLeague.get_text().strip()] = dictOfMatches

    return dictOfLeagues

def queryXMLParsedResults(query,matchId,send_notif):
    global nots
    print (query)
    print ('Prev nots:'+str(nots))
    summary = (requests.get(query, timeout=5))
    data = summary.content
    xmldoc = minidom.parseString (data)
    teams = xmldoc.getElementsByTagName("teams")[0]

    gameInfo = xmldoc.getElementsByTagName("gameInfo")[0]
    lst = []
    shots = xmldoc.getElementsByTagName("shots")

    for play in shots[0].childNodes:
        for data in play.childNodes:
            if data.nodeName == 'result':
                
                lst.append(data.childNodes[0].nodeValue)
    if len(lst) > 0:
        header = teams.getElementsByTagName("home")[0].childNodes[0].nodeValue+" "\
                 +gameInfo.getElementsByTagName("homeScore")[0].childNodes[0].nodeValue+ " - "\
                 +gameInfo.getElementsByTagName("awayScore")[0].childNodes[0].nodeValue+" "\
                 +teams.getElementsByTagName("away")[0].childNodes[0].nodeValue
        print(lst[-1])
        if send_notif and nots.get(matchId,None)!=lst[-1]:
            import subprocess as s
            s.call(['notify-send','-c','critical',header,lst[-1]])
            print ('Send not: '+lst[-1])
            nots[matchId] = lst[-1]
    return lst
