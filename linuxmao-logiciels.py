#!/usr/bin/python3

import sqlite3
from urllib.parse import urlparse
import requests
import argparse
import sys
import configparser

# read configuration file
config = configparser.ConfigParser()
config.read('linuxmao-logiciels.ini')
github_user = config['github']['github_user']
github_pass = config['github']['github_pass']

# CLI arguments
parser = argparse.ArgumentParser()
parser.add_argument("--cherche", help="chercher si un logiciel est présent dans la DB locale")
parser.add_argument("--stats", help="afficher des statistiques sur la DB locale", action="store_true")
parser.add_argument("--repo", help="chercher les maj dans les repos en ligne (repo = sourceforge, github, ALL)")

if len(sys.argv)==1:
    parser.print_help(sys.stderr)
    sys.exit(1)

args = parser.parse_args()


# print a string in red or green
def print_red(texte): print("\033[91m {}\033[00m" .format(texte)) 
def print_green(texte): print("\033[92m {}\033[00m" .format(texte))

# Connect to the sqlite DB
conn = sqlite3.connect('software.db')
c = conn.cursor()

# get latest release from github
def get_github_latest():

	c.execute("SELECT name,latest,url FROM software WHERE orig='github'")

	for row in c.fetchall():
		name = row[0]
		current_release = row[1]
		# be sure that the URL is ending with a trailing slash in the DB
		if not row[2].endswith('/'):
			url = row[2]+'/'
			print_red ("Merci d'ajouter un / à la fin de l'url dans la base pour "+name)
		else:
			url = row[2]
		print (''+name+' - '+current_release+' - '+url+'')
		# parse the URL and extract the path
		o = urlparse(url)
		# generate the url to query github API and query it
		latest_url='https://api.github.com/repos'+o.path+'releases/latest'
		#print ('Latest release URL: '+latest_url)
		r = requests.get(latest_url, auth=(github_user, github_pass))
		if r.status_code not in (200, 304):
			    raise Exception("Problème de connexion à github. %s %s" % (r.status_code, r))
		else:
			# get the latest release
			latest_release = r.json()['tag_name']
			if current_release !=  latest_release: 
				message = "Nouvelle version disponible : " +latest_release+ ' / URL: '+url+'releases/'
				print_green(message)
			print ("---")


# get latest release from sourceforge
def get_sourceforge_latest():

	c.execute("SELECT name,latest,url FROM software WHERE orig='sourceforge'")

	for row in c.fetchall():
		name = row[0]
		current_release = row[1]
		url = row[2]
		print (''+name+' - '+current_release+' - '+url+'')
		latest_url='https://sourceforge.net/projects/'+name+'/best_release.json'
		#print ('Latest release URL: '+latest_url)
		r = requests.get(latest_url)
		r.json()
		# get the latest release
		latest_release = r.json()['platform_releases']['linux']['filename']
		if current_release !=  latest_release: 
			message = "Nouvelle version disponible :" +latest_release
			print_green(message)
		print ("---")

# get latest release from gitlab
def get_gitlab_latest():

	c.execute("SELECT name,latest,url FROM software WHERE orig='gitlab'")

	for row in c.fetchall():
		name = row[0]
		current_release = row[1]
		# be sure that the URL is ending with a trailing slash in the DB
		if not row[2].endswith('/'):
			url = row[2]+'/'
			print_red ("Merci d'ajouter un / à la fin de l'url dans la base pour "+name)
		else:
			url = row[2]
		print (''+name+' - '+current_release+' - '+url+'')
		# parse the URL and extract the path
		o = urlparse(url)
		# get the project ID
		id_url="http://gitlab.com/api/v4/projects/"+(o.path[1:-1]).replace('/', '%2F')
		print (id_url)
		r = requests.get(id_url)
		r.json()
		project_id = r.json()['id']
		# generate and query the project release url
		project_release = 'https://gitlab.com/api/v4/projects/'+str(project_id)+'/releases'
		print (project_release)
		r = requests.get(project_release)
		latest_release = r.json()[-1]['tag_name']
		if current_release !=  latest_release: 
			message = "Nouvelle version disponible : " +latest_release
			print_green(message)
		print ("---")
	
# Look if a software is in the DB
def get_software_in_db(str):
	
	c.execute ("SELECT name,latest,url FROM software WHERE name LIKE ?",  ('%{}%'.format(str),))

	for row in c.fetchall():
		name = row[0]
		current_release = row[1]
		url = row[2]
		print (''+name+' - '+current_release+' - '+url+'')


def get_stats_from_db():
	c.execute("SELECT COUNT(*) FROM software WHERE orig='sourceforge'")
	count_sourceforge = c.fetchone()
	print ("Entrées Sourceforge :", count_sourceforge[0])
	c.execute("SELECT COUNT(*) FROM software WHERE orig='github'")
	count_github = c.fetchone()
	print ("Entrées Github :", count_github[0])
	c.execute("SELECT COUNT(*) FROM software WHERE orig='gitlab'")
	count_gitlab = c.fetchone()
	print ("Entrées gitlab :", count_gitlab[0])
	total = count_sourceforge[0] + count_github[0] + count_gitlab[0]
	print ("Total :", total)
	

if args.cherche:
	get_software_in_db(str = args.cherche)
elif args.stats:
	get_stats_from_db()
elif args.repo == 'github':
	get_github_latest()
elif args.repo == 'sourceforge':
	get_sourceforge_latest()
elif args.repo == 'gitlab':
	get_gitlab_latest()
elif args.repo == 'ALL':
	get_github_latest()
	get_sourceforge_latest()
	get_gitlab_latest()
