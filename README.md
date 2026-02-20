## Setup
#### Terminal Commands

Ensure you have Python installed and do the following:
1. Define `CLIENT_ID` and `CLIENT_SECRET` in `.env`
    > The program will not run correctly without your own Spotify API credentials.
2. Setup a virtual environment: 
    - `python -m venv venv`
3. Activate your virtual environment: 
    - Windows: `source venv/Scripts/activate`
    - Linux / UNIX: `source venv/bin/activate`
    > You should now see `(venv)` or a similar prefix appear before the current terminal line.
4. Install required libraries (and conduct version checking): 
    - `pip install -r requirements.txt`

> NOTE: Currently, the program runs... with errors. Those are still being fixed, however these instructions shouldn't change if and when the errors are fixed.

5. Run the program:
    - `python emotional_fingerprint.py`


Notes: 
- Fix error 403
    - Consider the following:
        - OAuth method, with an html address as a "hook"
        - Make your own Spotify API keys
        - Secret third option...
