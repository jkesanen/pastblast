# Pastblast

A command line Last.fm track submitter

Scans the track information of given media files and scrobbles them as listened
tracks to Last.fm account.

I wanted to keep my listening charts very accurate, but I listen music from
vinyls and CDs quite often. Fortunately I have the most of the music I own also
on my computers. Therefore a simple script can easily read the metadata of the
listened records from files and scrobble that data to Last.fm.

## Features

* Takes directories and single files as arguments
* Uses Mutagen library to access metadata from tracks
* Specify when tracks were listened
* Submit tracks to Last.fm using Pylast library
* Manual track submitting (type in the information)

## Requirements

* Python (tested with 2.7 and 3.6)
* Pylast library
* Mutagen library

Installing required libraries: `pip3 install mutagen pylast`

## Usage example

Scrobble an album you finished listening to 7 hours and 20 minutes ago:

`pastblast.py -t 7h20 ~/music/Nine_Inch_Nails_-_The_Slip-2008`

Scrobble a two songs you just listened to:

`pastblast.py ~/music/How_To_Destroy_Angels_-_How_To_Destroy_Angels-EP-2010/02 Parasite.mp3 ~/music/Nine_Inch_Nails_-_The_Slip-2008/05-Nine_Inch_Nails_-_Echoplex.ogg`
