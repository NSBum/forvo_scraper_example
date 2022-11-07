# Forvo scaper example

Before introducing this code, I want to insert a couple caveats:

- Forvo is an excellent resource for language learners and I wish the company the best of luck in commercializing word and phrase pronunciations. This code is not meant to deprive them of resources to further their misson.
- They have an API that in principle should allow developers to access pronunciations. In fact, I'm a paid monthly subscriber to that API. But it is often very slow and frequently is down completely without any status information or response from the support staff.
- This is meant as an example for you to adapt. It only works for Russian pronunciations right now.

There are other projects - mostly Anki add-ons - that scrape pronunciations in this same fashion. The intent here is to do the same thing without integration into Anki. This was also a platform for me to learn to integrate Selenium with Beautiful Soup 4. For reasons unclear to me, despite using a browser user-agent string, some of my requests from Python to a Forvo pronunciation page resulted in errors. Therefore, I brought in Selenium to completely mimic the browser experience when viewed from the server side. This is all a little slower than using the API, _as long as the API is functioning as it did in the past_. Now it's often extremely slow or down. 

One unique feature of this Forvo scraper is that it seeks to prioritize pronunciation through a simple scoring system. You can change `FAVS` to whatever users are your favourites. Then the `Pronunciation` class attempts to rank the pronunciations by favourite user and number of votes.

## Usage

To use, you'll need to install Beautiful Soup 4, Selenium and anything else you don't have. Then download the code in `forvo_scraper_example.py` and make it executable. Then it's just `forvo_scraper_example.py --word 'кошка' --dest '/your/destination/directory'`
