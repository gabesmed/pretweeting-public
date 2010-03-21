
PROTOCOL = 'http://'
STREAM_URL = 'stream.twitter.com/gardenhose.json'
 
import time, datetime
import sys, os
from optparse import OptionParser
import urllib2, urllib
from django.core.management import setup_environ
from utils import get_settings_file

import logging

BATCHES_SUBDIR = 'batches'

# set up classes and functions

def log_msg(msg):
    print msg
    logging.debug(msg)

class TwitterOpener(urllib.FancyURLopener):
    def prompt_user_passwd(self, host, realm):
        return (settings.TWITTER_USERNAME, settings.TWITTER_PASSWORD)

def open_firehose():
    opener = TwitterOpener()
    
    try:
        data = opener.open(PROTOCOL + STREAM_URL)
    except IOError, e:
        log_msg('...error opening steam: %s' % str(e))
        return
    
    buffer_bytes = 0
    line_buffer = []
    line_count = 0
    
    t0 = time.time()
    
    while True:
        try:
            line = data.readline()
        except IOError, e:
            log_msg('...error reading stream: %s' % str(e))
            opener.close()
            return
            
        if not line:
            break
        line_buffer.append(line)
        line_count += 1
        buffer_bytes += len(line)

        if (line_count == settings.BATCH_MAX_MESSAGES or 
                (time.time() - t0) > settings.BATCH_INTERVAL):
            # write the batch
            write_batch(line_buffer)
            log_msg('%d lines (%dkb) batched in %.01fs.' % (
                    line_count, (buffer_bytes / 1024), (time.time() - t0)))
            line_count = 0
            line_buffer = []
            buffer_bytes = 0
            t0 = time.time()
    
    # write an incomplete batch if closed.
    if line_count > 0:
        write_batch(line_buffer)
        
def write_batch(line_buffer):
    file_name = '%d.txt' % int(time.time())
    file_path = os.path.join(BATCH_DIR, file_name)
    f = open(file_path, 'w')
    for line in line_buffer:
        f.write(line)
    f.close()

def main():
    log_msg('starting consume script at %s' % 
            datetime.datetime.now().replace(microsecond=0))
    try:
        while True:
            log_msg('opening %s%s...' % (PROTOCOL, STREAM_URL))
            open_firehose()
            log_msg('...connection closed.')
            time.sleep(10)
    except KeyboardInterrupt:
        log_msg('...terminated.')
        sys.exit(0)

if __name__ == '__main__':
    
    parser = OptionParser()
    parser.add_option("-s", "--settings", dest="settings",
                      help="choose which settings to use", metavar="SETTINGS")
    
    (options, args) = parser.parse_args()
    
    cwd = os.getcwd()
    sys.path.append(os.path.dirname(cwd))
    
    settings_option = options.settings or 'settings'
    settings_module = get_settings_file('../../pretweeting', settings_option)
    setup_environ(settings_module)
    from django.conf import settings

    LOG_FILENAME = os.path.join(settings.LOCAL_DATA_DIR, 'consume_log.txt')
    logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)
    
    BATCH_DIR = os.path.join(settings.LOCAL_DATA_DIR, BATCHES_SUBDIR)
    try:
        os.makedirs(BATCH_DIR)
    except OSError:
        pass
    
    main()

