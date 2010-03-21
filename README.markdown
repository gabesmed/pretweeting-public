# Pretweeting

*Pretweeting is now open source!* All the code needed to deploy an instance of the game pretweeting is in this repository.

## Requirements

- Django 1.0+
- Python 2.4+
- MySQL
- Memcached
- Python libraries: pytz, pexpect

## Installation

To set up a local instance of pretweeting, follow the following steps.

1. Download the source code to a directory on your local machine.
2. Set up an empty MySQL database.
3. Set up a (twitter oAuth client)[http://twitter.com/oauth] and remember the
   key/secret.
4. Fill out the `pretweeting/apps/config/environment/local.py` file with 
   appropriate settings for your database and twitter access. You'll need:

       # for database access
       DATABASE_USER = '---'
       DATABASE_PASSWORD = '---'
       DATABASE_HOST = ''
       
       # for local data storage
       LOCAL_DATA_DIR = "/Users/Gabe/pretweeting_data"
       BULK_INSERT_DIR = "/Users/Gabe/pretweeting_data/bulk_insert"
       
       # for accessing the streaming API
       TWITTER_USERNAME = '---'
       TWITTER_PASSWORD = '---'
       
       # for tweeting and DMing from pretweeting account
       TWITTER_OAUTH_TOKEN = '---'
       TWITTER_DM_SCREENNAME = '---'
       
       # for twitter authorization
       CONSUMER_KEY = '---'
       CONSUMER_SECRET = '---'
   
5. Run `python manage.py syncdb` to create the database tables.
6. Run `python manage.py runserver` to start the web server. At this point you 
   should be able to navigate to localhost:8000 to see a game with empty data
   running.
7. To start the feed from twitter, you'll need to run two scripts
   continuously.
   - `pretweeting/scripts/consume.py` opens a connection to the garden hose
     and files away batches of data into a folder in your local data
     data directory.
   - `pretweeting/scripts/process.py` regularly consumes those data batch
     files and pushes them into the database.

Once you have the webserver and feed scripts running, that should be all you need! You can change parameters like how frequently prices are updated in the `pretweeting/apps/config/environment/local.py` file.

Steps for setting up a remote server are largely similar. Let me know if you have any difficulties! Happy pretweeting!