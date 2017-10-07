import requests
import re
import json
import logging
import time
from enum import Enum

class Battlemap(object):

    def get_cookies(self):
        """ opens a fake browser to get the cookies needed """
        from robobrowser import RoboBrowser
        browser = RoboBrowser(user_agent='Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1b3) Gecko/20090305 Firefox/3.1b3 GTB5', parser='html.parser')
        browser.open('https://battlemap.deltatgame.com/home#')
        link = browser.find('a')
        browser.follow_link(link)
        form=browser.get_form(0)

        with open('credentials.json') as credentialfile:
            credentials = json.load(credentialfile)
            form['Email'] = credentials['email']
            browser.submit_form(form)
            form=browser.get_form(0)
            form['Passwd'] = credentials['password']
            browser.submit_form(form)
            browser.open('https://battlemap.deltatgame.com/home')

        self.laravel_token = browser.session.cookies.get('laravel_session')
        self.xsrf = browser.session.cookies.get('XSRF-TOKEN')
        self.cookietimeout = time.time() + 60*60*1.95

    def __init__ (self):
        self.session = requests.Session()
        headers = {
            'authority' : 'battlemap.deltatgame.com',
            'method':'GET',
            'scheme':'https',
            'accept':'*/*',
            'accept-encoding':'gzip, deflate, br',
            'accept-language':'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
            'cookie':'',
            'referer':'https://battlemap.deltatgame.com/home',
            'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
            'x-requested-with':'XMLHttpRequest'
        }
        self.session.headers.update(headers)
        self.cookietimeout = 0

        self.factions = {
            0:{
                'Faction name' : 'Nyoko Labs',
                'Color name'   : 'yellow',
                'Color code'   : '#ffa200'
            },
            1:{
                'Faction name' : 'Cosmostellar',
                'Color name'   : 'green',
                'Color code'   : '#22f233'
            },
            2:{
                'Faction name' : 'Gene X',
                'Color name'   : 'blue',
                'Color code'   : '#005eff'
            },
            3:{
                'Faction name' : 'Humanoid',
                'Color name'   : 'red',
                'Color code'   : '#f70b10'
            },
            4:{
                'Faction name' : 'Neutral',
                'Color name'   : 'white',
                'Color code'   : '#ffffff'
            }
        }


    def fetch(self, url , maptype):
        # get new cookies if needed
        if self.cookietimeout < time.time():
            logging.info("cookies too old, trying to get new ones")
            self.get_cookies()

        retrys = 3
        while retrys > 0:
            try:
                if maptype == 'warmap':
                    self.session.headers.update({'referer': 'https://battlemap.deltatgame.com/warmap'})
                elif maptype == 'regular':
                    self.session.headers.update({'referer': 'https://battlemap.deltatgame.com/home'})

                cookie_header = '_ga=GA1.2.220295278.1504376854; _gid=GA1.2.631065873.1504376854; XSRF-TOKEN=' + self.xsrf + '; laravel_session=' + self.laravel_token

                request = self.session.get(url, headers= {'cookie': cookie_header})
                logging.info("request answer: " + str(request.content) )

                if 'set-cookie' in request.headers.keys():
                    self.xsrf = re.findall(r'XSRF-TOKEN=(\S*);', request.headers['set-cookie'])[0]
                    self.laravel_token = re.findall(r'laravel_session=(\S*);',request.headers['set-cookie'])[0]
                    self.cookietimeout = time.time() + 60*60* 1.95

                return request.json()

            except ValueError:
                retrys -= 1
                time.sleep(2)
                logging.warning("fetching request failed with ValueError")
            except KeyError:
                retrys -= 1
                time.sleep(2)
                logging.warning("KeyError")
        logging.warning("fetch failed completly\n" + url + "\n" + str(self.session.headers))
        return None


    '''all-maps'''
    def fetch_basedata(self, baseID):
        url ='https://battlemap.deltatgame.com/base/' + str(baseID)
        return self.fetch(url,'')

    def get_attacks(self):
        url='https://battlemap.deltatgame.com/dominance_attack_details'
        return self.fetch(url,'')

    def get_profile(self):
        url='https://battlemap.deltatgame.com/profile'
        return self.fetch(url,'')

    def get_clan(self,clanid):
        url='https://battlemap.deltatgame.com/clan_members/'+str(clanid)
        return self.fetch(url,'')
    
    '''battlemap'''
    def fetch_battledata(self, baseID):
        url = 'https://battlemap.deltatgame.com/own_faction_cluster/' + str(baseID)
        return self.fetch(url,'warmap')

    def fetch_bases(self,lat1,lon1,lat2,lon2,zoomlevel):
        url='https://battlemap.deltatgame.com/base_data/LatLng('+lat1+', '+lon1+')/LatLng('+lat2+', '+lon2+')/LatLng('+lat1+', '+lon2+')/LatLng('+lat2+', '+lon1+')/'+str(zoomlevel)
        return self.fetch(url,'warmap')

    def fetch_bases_faction(self,lat1,lon1,lat2,lon2,faction,zoomlevel):
        url='https://battlemap.deltatgame.com/base_data_faction/'+str(faction)+'/LatLng('+lat1+', '+lon1+')/LatLng('+lat2+', '+lon2+')/LatLng('+lat1+', '+lon2+')/LatLng('+lat2+', '+lon1+')/'+str(zoomlevel)
        return self.fetch(url,'warmap')

    '''Regular Map'''
    def fetch_neutral_cores(self,lat1,lon1,lat2,lon2):
        url='https://battlemap.deltatgame.com/core_data_neutral/LatLng('+lat1+', '+lon1+')/LatLng('+lat2+', '+lon2+')/LatLng('+lat1+', '+lon2+')/LatLng('+lat2+', '+lon1+')'
        return self.fetch(url,'regular')
        
    def fetch_cores(self,lat1,lon1,lat2,lon2):
        url='https://battlemap.deltatgame.com/filter_data/LatLng('+lat1+', '+lon1+')/LatLng('+lat2+', '+lon2+')/LatLng('+lat1+', '+lon2+')/LatLng('+lat2+', '+lon1+')?minLevel=0&maxLevel=5&type=core'
        return self.fetch(url,'regular')

    def fetch_core_data(self,coreID):
        url = 'https://battlemap.deltatgame.com/core/' + str(coreÌD)
        return self.fetch(url,'regular')

    def get_overview(self):
        url='https://battlemap.deltatgame.com/web_view/get_data'
        return self.fetch(url,'regular')

    def get_attack_details(self):
        url='https://battlemap.deltatgame.com/dominance_attack_details'
        return self.fetch(url,'regular')

    def search(self,term):
        url='https://battlemap.deltatgame.com/leaflet-search-for?term='+term
        return self.fetch(url,'regular')

    def get_profile(self,playerid):
        url='https://battlemap.deltatgame.com/public_profile/'+str(playerid)
        return self.fetch(url,'regular')

    def get_player_skilltree(self,playerid):
        url='https://battlemap.deltatgame.com/skilltree_public/'+str(playerid)
        return self.fetch(url,'regular')

    def get_chat_tagged_messages(self):
        url='https://battlemap.deltatgame.com/chat_tagged_messages'
        return self.fetch(url,'regular')

    ''' Faction conversion '''
    def get_factionname(self,enum):
        return self.factions[enum]['Faction name']

    def get_factioncolor(self,enum):
        return self.factions[enum]['Color code']
