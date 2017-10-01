#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# pastblast - A Python application to scrobble listened tracks to Last.fm.
# Copyright (C) 2009-2017 Jani Kesänen
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#

""" This application depends on Mutagen audio metadata handling library and
pylast last.fm API interface library. They are available at pip and
https://github.com/quodlibet/mutagen and https://github.com/pylast/pylast
"""

from __future__ import print_function
from builtins import input

__version__ = '0.6.0'
__author__ = 'Jani Kesänen'
__copyright__ = "Copyright (C) 2009-2017 Jani Kesänen"
__license__ = "gpl"

import logging
import time
import os
import os.path
import sys

# Application requires Last.fm Web Services API key for accessing their
# services. It can be obtained from http://www.last.fm/api/account
API_KEY = ""
API_SECRET = ""

class pastblast(object):

    class track_storage(object):
        """This class stores all the necessary track information to
           scrobble to last.fm.
        """
        def __init__(self):
            self.songs = []
            self.duration = 0.0


        def add_track(self, artist, title, length, album, tracknum):
            self.duration += length
            self.songs.append({ 'artist': artist, 'title': title, 'length': str(int(length)), 'flength': length, 'album': album, 'tracknum': tracknum })


        def pop_track(self):
            try:
                self.duration -= self.songs[0]['flength']
                return self.songs.pop(0)
            except IndexError:
                return


        def get_track(self, num):
            return self.songs[num]


        def __len__(self):
            return len(self.songs)


    def __init__(self, debug=False):
        """Initialize pastblast class."""
        self.ss = self.track_storage()
        self.warnings = False

        # Initialize logger
        self.log = logging.getLogger("PastBlast")
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        self.log.addHandler(self.ch)

        if debug:
            self.log.setLevel(logging.DEBUG)
            self.ch.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)
            self.ch.setLevel(logging.INFO)


    def process_mp3_file(self, filename):
        """Extract metadata information from a mp3 file and add it into
           track storage.
        """
        from mutagen.id3 import ID3NoHeaderError, ID3UnsupportedVersionError
        from mutagen.mp3 import MP3

        self.log.debug(("Processing %s" % filename))

        try:
            mp3 = MP3(filename)
        except KeyboardInterrupt:
            raise
        except Exception:
            self.log.error(("Failed to access %s" % filename))
            return False

        if mp3.tags:
            # Verify that required information is present.
            if not mp3.tags.has_key('TPE1') or not mp3.tags.has_key('TIT2'):
                self.log.error("Required information is missing. Can not queue this track.")
                return False
            if mp3.info.length < 30:
                self.log.warning("Minimum lenght of a track for submitting is 30 seconds. Skipping...")
                return True

            if mp3.tags.has_key('TALB'):
                album = mp3.tags['TALB'][0]
            else:
                album = ""
            if mp3.tags.has_key('TRCK'):
                tracknum = mp3.tags['TRCK'][0]
            else:
                tracknum = ""

            self.log.debug(("%s - %s - %s, %f" % (mp3.tags['TPE1'][0], album, mp3.tags['TIT2'][0], mp3.info.length)))

            self.ss.add_track(mp3.tags['TPE1'][0], mp3.tags['TIT2'][0], mp3.info.length, album, tracknum)
        else:
            self.log.warning(("%s is not tagged." % filename))
            return False

        return True


    def process_ogg_file(self, filename):
        from mutagen.oggvorbis import Open

        self.log.debug(("Processing %s" % filename))

        try:
            ogg = Open(filename)
        except KeyboardInterrupt:
            raise
        except Exception:
            self.log.error(("Failed to access %s" % filename))
            return False

        if ogg.tags:
            # Verify that required information is present.
            if not ogg.tags.has_key('artist') or not ogg.tags.has_key('title'):
                self.log.error("Required information is missing. Can not queue this track.")
                return False
            if ogg.info.length < 30:
                self.log.warning("Minimum lenght of a track for submitting is 30 seconds. Skipping...")
                return True

            if ogg.tags.has_key('album'):
                album = ogg.tags['album'][0]
            else:
                album = ""
            if ogg.tags.has_key('tracknumber'):
                tracknum = ogg.tags['tracknumber'][0]
            else:
                tracknum = ""

            self.log.debug(("%s - %s - %s, %f" % (ogg.tags['artist'][0], album, ogg.tags['title'][0], ogg.info.length)))

            self.ss.add_track(ogg.tags['artist'][0], ogg.tags['title'][0], ogg.info.length, album, tracknum)
        else:
            self.log.warning(("%s is not tagged." % filename))
            return False

        return True


    def process_wma_file(self, filename):
        from mutagen.asf import Open

        self.log.debug(("Processing %s" % filename))

        try:
            asf = Open(filename)
        except KeyboardInterrupt:
            raise
        except Exception:
            self.log.error(("Failed to access %s" % filename))
            return False

        if asf:
            # Verify that required information is present.
            if not asf.has_key('WM/AlbumArtist') or not asf.has_key('Title'):
                self.log.error("Required information is missing. Can not queue this track.")
                return False
            if asf.info.length < 30:
                self.log.warning("Minimum lenght of a track for submitting is 30 seconds. Skipping...")
                return True

            if asf.has_key('WM/AlbumArtist'):
                album = asf['WM/AlbumArtist'][0]
            else:
                album = ""
            if asf.has_key('WM/TrackNumber'):
                tracknum = asf['WM/TrackNumber'][0]
            else:
                tracknum = ""

            self.log.debug(("%s - %s - %s, %f" % (asf['WM/AlbumArtist'][0], album, asf['Title'][0], asf.info.length)))

            self.ss.add_track(asf['WM/AlbumArtist'][0], asf['Title'][0], asf.info.length, album, tracknum)
        else:
            self.log.warning(("%s is not tagged." % filename))
            return False

        return True


    def process_flac_file(self, filename):
        """Extract metadata information from a flac file and add it into
           track storage.
        """
        from mutagen.flac import Open

        self.log.debug(("Processing %s" % filename))

        try:
            flac = Open(filename)
        except KeyboardInterrupt:
            raise
        except Exception:
            self.log.error(("Failed to access %s" % filename))
            return False

        if flac.tags:
            # Verify that required information is present.
            if not flac.tags.has_key('ARTIST') or not flac.tags.has_key('TITLE'):
                self.log.error("Required information is missing. Can not queue this track.")
                return False
            if flac.info.length < 30:
                self.log.warning("Minimum lenght of a track for submitting is 30 seconds. Skipping...")
                return True

            if flac.tags.has_key('ALBUM'):
                album = flac.tags['ALBUM'][0]
            else:
                album = ""
            if flac.tags.has_key('TRACKNUMBER'):
                tracknum = flac.tags['TRACKNUMBER'][0]
            else:
                tracknum = ""

            self.log.debug(("%s - %s - %s, %f" % (flac.tags['ARTIST'][0], album, flac.tags['TITLE'][0], flac.info.length)))

            self.ss.add_track(flac.tags['ARTIST'][0], flac.tags['TITLE'][0], flac.info.length, album, tracknum)
        else:
            self.log.warning(("%s is not tagged." % filename))
            return False

        return True


    def process_file(self, filename):
        ok = False

        if filename.lower().endswith('.mp3'):
            ok = self.process_mp3_file(filename)
        elif filename.lower().endswith('.ogg'):
            ok = self.process_ogg_file(filename)
        elif filename.lower().endswith('.wma'):
            ok = self.process_wma_file(filename)
        elif filename.lower().endswith('.flac'):
            ok = self.process_flac_file(filename)
        else:
            return

        if not ok:
            self.warnings = True


    def scan_path(self, path, recursive=False):
        """Scan the given path for audio files."""
        if os.path.isfile(path):
            self.process_file(path)
        else:
            if recursive:
                for curpath, dirs, files in os.walk(path):
                    self.log.info(("Scanning %s" % curpath))
                    files.sort()
                    for filename in files:
                        self.process_file(os.path.join(curpath, filename))
            else:
                self.log.info(("Scanning %s" % path))
                files = os.listdir(path)
                files.sort()
                for filename in files:
                    if os.path.isfile(os.path.join(path, filename)):
                        self.process_file(os.path.join(path, filename))


    def submit_tracks(self, username = '', password = '', timeshift = 0):
        """Scrobble tracks from track storage to last.fm."""
        if self.warnings:
            ret = input("Files processed with warnings. Continue (y/N)?")
            if ret != 'y':
                return

        if not username:
            # Read username from stdin if not provided
            username = input("Username: ")

        if not password:
            # Read password from stdin if not provided
            import getpass
            hash = pylast.md5(getpass.getpass())
        else:
            hash = pylast.md5(password)

        network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET, username=username, password_hash=hash)
        sg = pylast.SessionKeyGenerator(network)

        # Ending time of listening (minus timeshift).
        now = time.time() - timeshift

        while len(self.ss):
            listened = int(now - self.ss.duration)
            s = self.ss.pop_track()
            network.scrobble(s['artist'], s['title'], listened, album=s['album'], track_number=s['tracknum'], duration=int(s['length']))


    def manual_add(self):
        """Manually enter tracks to be scrobbled. Empty artist or track ends session."""
        while True:
            artist = input("Artist: ")

            if not len(artist):
                self.log.info("Empty artist name. Stopping manual input...")
                break

            track = input("Track: ")

            if not len(track):
                self.log.info("Empty track title. Stopping manual input...")
                break

            val = input("Length: ")
            try:
                values = val.split(':')
            except:
                values = [val]

            length = 0
            try:
                for i in range(0, len(values)):
                    length += int(values[-1-i]) * pow(60, i)
            except:
                self.log.error("Track length must be entered in seconds or in hh:mm:ss notation. Stopping...")
                break

            album = input("Album: ")

            while True:
                tracknum = input("Track number: ")
                if not tracknum:
                    break

                try:
                    int(tracknum)
                    break
                except ValueError as err:
                    self.log.error("Track number must indeed be a number. Or empty.")
                    # While continues and ask again for the number

            if sys.version_info[0] == 2:
                artist = artist.decode(sys.stdin.encoding)
                track = track.decode(sys.stdin.encoding)
                album = album.decode(sys.stdin.encoding)

            self.ss.add_track(artist, track, length, album, tracknum)
            self.log.info("Track added")


    def list_tracks(self):
        """Dump queued tracks to log."""
        i = 0
        while i < len(self.ss):
            s = self.ss.get_track(i)
            i += 1
            self.log.info(("%d. %s - %s - %s" % (i, s['artist'], s['album'], s['title'])))
        self.log.info(("Total %d seconds of tracks in queue." % (self.ss.duration)))


    def num_queued(self):
        """ Return number of queued tracks."""
        return len(self.ss)


def usage(progname):
    print("""Usage: %s [OPTION]... PATH

  -d       Set output level to debug
  -m       Manually enter tracks to be scrobbled
  -r       Scan directories recursively
  -u USER  User name in last.fm
  -t TIME  Amount of time before the current time listening end
             syntax: __d__h__
             (1d20h20, 1d20h, 1h10, 2d50, 4h, 15)
""" % progname)


def version():
    print("Pastblast %s (+ pylast %s)" % (__version__, pylast.__version))
    print("Copyright (C) 2009-2017 Jani Kesänen")
    print("""License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.""")


def timestring_to_seconds(rest):
    """Convert 7d12h10 notation to number of seconds."""
    try:
        days, rest = rest.split('d')
    except ValueError:
        days = 0
    sec = int(days) * 60 * 60 * 24

    try:
        hours, rest = rest.split('h')
    except ValueError:
        hours = 0
    sec += int(hours) * 60 * 60

    if rest:
        sec += int(rest) * 60

    return sec


def main(argv):
    import getopt

    debug = False
    manual = False
    recursive = False
    timeshift = 0
    username = ''

    try:
        opts, args = getopt.getopt(argv[1:], "dmrt:u:")
    except getopt.GetoptError as err:
        # Print help information and exit.
        print("GetoptError: {0}".format(err))
        usage(argv[0])
        sys.exit(2)

    for o, a in opts:
        if o == "-d":
            debug = True
        elif o == "-m":
            manual = True
        elif o == "-r":
            recursive = True
        elif o in "-t":
            timeshift = timestring_to_seconds(a)
        elif o in "-u":
            username = a
        else:
            assert False, "unhandled option"

    if len(args) == 0 and not manual:
        usage(argv[0])
        sys.exit(2)

    pb = pastblast(debug=debug)
    if manual:
        pb.manual_add()
    else:
        for path in args:
            pb.scan_path(path, recursive)

    if pb.num_queued():
        pb.list_tracks()
        pb.submit_tracks(username=username, timeshift=timeshift)
    else:
        print("No tracks in queue.")


if __name__ == "__main__":
    import_error = False

    try:
        import pylast
    except ImportError as err:
        print("Importing pylast failed: {0}".format(err))
        print("  Project home: https://github.com/pylast/pylast")
        import_error = True

    try:
        from mutagen.id3 import ID3
    except ImportError:
        print("Importing mutagen failed: {0}".format(err))
        print("  Project homepage: https://github.com/quodlibet/mutagen")
        import_error = True

    if import_error:
        print("Exiting...")
        sys.exit(1)

    main(sys.argv)
