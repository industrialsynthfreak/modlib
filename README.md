# modlib
At the time this is a simple converter/jsonizer for music tracker modules. 
I'll try to make a simple tracker after implementing all the planned formats.

## Usage:
Ensure it's `chmod +x` and run (you'll probably need python3.4+):

    `console.py [-v for verbose (no log)] [path]`

## What it can do:
- Load files and folders using UNIX style cl syntax
- Guess tracker format by extension, sample parameters, special flags, etc.
- Unpack module data into python dict object and save it to json
- Unpack module samples and save them to wav

## Supported formats:
- All 15-samples Ultimate Soundtracker, Soundtracker II-IX, Master 
Soundtracker, SoundTracker 2.0 original mods

## Going to be supported:
- Definitely 31-sample Noisetracker and Protracker modules
- Compressed formats
- XMs

## Do you know about libxmp and what your code sucks?
- Yes, I do, but I can't compete with that crazy jap anyway.
