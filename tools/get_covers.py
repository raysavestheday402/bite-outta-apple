"""
get_covers.py  (version 6 - posters, details, and Apple TV links)
Gets the best poster for every kids title in the Apple TV Library portal.

Where it looks, best first:
  1. TMDB (themoviedb.org)  - official posters for movies AND tall posters for TV shows
  2. fanart.tv              - high-quality posters, used when TMDB has none
  3. Wikipedia              - the poster on each title's exact Wikipedia page

TMDB and fanart.tv need a free personal API key. The script asks for them the first time
and saves them in keys.txt next to this script, so you only enter them once.
Without keys it still works, using Wikipedia only.
"""
import json, os, re, sys, time, csv, urllib.request, urllib.parse, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "Covers")
KEYS = os.path.join(HERE, "keys.txt")
os.makedirs(OUT, exist_ok=True)
PLAN = json.loads(r"""[{"n": 1, "kind": "tv", "label": "AAAHH!!! Real Monsters", "term": "AAAHH!!! Real Monsters", "year": 1994, "wiki": [], "alts": []}, {"n": 2, "kind": "tv", "label": "The Adventures of Rocky and Bullwinkle", "term": "The Adventures of Rocky and Bullwinkle", "year": "", "wiki": ["The Adventures of Rocky and Bullwinkle (film)"], "alts": []}, {"n": 3, "kind": "tv", "label": "The Amanda Show", "term": "The Amanda Show", "year": 1999, "wiki": [], "alts": []}, {"n": 4, "kind": "tv", "label": "Angry Beavers", "term": "The Angry Beavers", "year": 1997, "wiki": [], "alts": []}, {"n": 5, "kind": "tv", "label": "Animaniacs", "term": "Animaniacs", "year": 2020, "wiki": [], "alts": []}, {"n": 6, "kind": "tv", "label": "Baby Einstein Classics", "term": "Baby Einstein Classics", "year": "", "wiki": [], "alts": []}, {"n": 7, "kind": "tv", "label": "Courage the Cowardly Dog", "term": "Courage the Cowardly Dog", "year": 1999, "wiki": [], "alts": []}, {"n": 8, "kind": "tv", "label": "Cow & Chicken", "term": "Cow & Chicken", "year": 1997, "wiki": [], "alts": []}, {"n": 9, "kind": "tv", "label": "Dora the Explorer", "term": "Dora the Explorer", "year": 2000, "wiki": [], "alts": []}, {"n": 10, "kind": "movie", "label": "Halloweentown: 4-Movie Collection", "term": "Halloweentown", "year": 1998, "wiki": ["Halloweentown (film)"], "alts": []}, {"n": 11, "kind": "tv", "label": "Looney Tunes Cartoons", "term": "Looney Tunes Cartoons", "year": 2020, "wiki": [], "alts": []}, {"n": 12, "kind": "tv", "label": "Rocko's Modern Life", "term": "Rocko's Modern Life", "year": 1993, "wiki": [], "alts": []}, {"n": 13, "kind": "tv", "label": "Rugrats", "term": "Rugrats", "year": 1991, "wiki": [], "alts": []}, {"n": 14, "kind": "tv", "label": "Sabrina, The Teenage Witch", "term": "Sabrina the Teenage Witch", "year": 1996, "wiki": [], "alts": []}, {"n": 15, "kind": "tv", "label": "Steven Spielberg Presents... (1)", "term": "Steven Spielberg Presents", "year": "", "choices": [{"kind": "tv", "term": "Animaniacs", "year": 1993}, {"kind": "tv", "term": "Freakazoid!", "year": 1995}, {"kind": "tv", "term": "Pinky and the Brain", "year": 1995}, {"kind": "tv", "term": "Pinky, Elmyra & the Brain", "year": 1998}]}, {"n": 17, "kind": "tv", "label": "Tom and Jerry", "term": "Tom and Jerry", "year": "", "wiki": [], "alts": []}, {"n": 18, "kind": "movie", "label": "The Adventures of Rocky and Bullwinkle", "term": "The Adventures of Rocky and Bullwinkle", "year": 2000, "wiki": ["The Adventures of Rocky and Bullwinkle (film)"], "alts": []}, {"n": 19, "kind": "movie", "label": "Aladdin (1992)", "term": "Aladdin", "year": 1992, "wiki": ["Aladdin (1992 Disney film)"], "alts": []}, {"n": 20, "kind": "movie", "label": "All Dogs Go to Heaven", "term": "All Dogs Go to Heaven", "year": 1989, "wiki": ["All Dogs Go to Heaven"], "alts": []}, {"n": 21, "kind": "movie", "label": "Alvin and the Chipmunks", "term": "Alvin and the Chipmunks", "year": 2007, "wiki": ["Alvin and the Chipmunks (film)"], "alts": []}, {"n": 22, "kind": "movie", "label": "Alvin and the Chipmunks: Chipwrecked", "term": "Alvin and the Chipmunks: Chipwrecked", "year": 2011, "wiki": ["Alvin and the Chipmunks: Chipwrecked"], "alts": []}, {"n": 23, "kind": "movie", "label": "Alvin and the Chipmunks: The Road Chip", "term": "Alvin and the Chipmunks: The Road Chip", "year": 2015, "wiki": ["Alvin and the Chipmunks: The Road Chip"], "alts": []}, {"n": 24, "kind": "movie", "label": "Alvin and the Chipmunks: The Squeakquel", "term": "Alvin and the Chipmunks: The Squeakquel", "year": 2009, "wiki": ["Alvin and the Chipmunks: The Squeakquel"], "alts": []}, {"n": 25, "kind": "movie", "label": "Anastasia (1997)", "term": "Anastasia", "year": 1997, "wiki": ["Anastasia (1997 film)"], "alts": []}, {"n": 26, "kind": "movie", "label": "Antz", "term": "Antz", "year": 1998, "wiki": ["Antz"], "alts": []}, {"n": 27, "kind": "movie", "label": "Atlantis: The Lost Empire", "term": "Atlantis: The Lost Empire", "year": 2001, "wiki": ["Atlantis: The Lost Empire"], "alts": []}, {"n": 28, "kind": "movie", "label": "Baby Shark's Big Movie", "term": "Baby Shark's Big Movie", "year": 2023, "wiki": ["Baby Shark's Big Movie!", "Baby Shark's Big Movie"], "alts": ["Baby Shark's Big Movie!"]}, {"n": 29, "kind": "movie", "label": "The Bad Guys", "term": "The Bad Guys", "year": 2022, "wiki": ["The Bad Guys (2022 film)", "The Bad Guys (film)"], "alts": []}, {"n": 30, "kind": "movie", "label": "The Bad Guys 2", "term": "The Bad Guys 2", "year": 2025, "wiki": ["The Bad Guys 2"], "alts": []}, {"n": 31, "kind": "movie", "label": "Beauty and the Beast", "term": "Beauty and the Beast", "year": 1991, "wiki": ["Beauty and the Beast (1991 film)"], "alts": []}, {"n": 32, "kind": "movie", "label": "Big Hero 6", "term": "Big Hero 6", "year": 2014, "wiki": ["Big Hero 6 (film)"], "alts": []}, {"n": 33, "kind": "movie", "label": "The Boss Baby", "term": "The Boss Baby", "year": 2017, "wiki": ["The Boss Baby"], "alts": []}, {"n": 34, "kind": "movie", "label": "The Boss Baby: Family Business", "term": "The Boss Baby: Family Business", "year": 2021, "wiki": ["The Boss Baby: Family Business"], "alts": []}, {"n": 35, "kind": "movie", "label": "A Bug's Life", "term": "A Bug's Life", "year": 1998, "wiki": ["A Bug's Life"], "alts": []}, {"n": 36, "kind": "movie", "label": "Cars", "term": "Cars", "year": 2006, "wiki": ["Cars (film)"], "alts": []}, {"n": 37, "kind": "movie", "label": "Cars 2", "term": "Cars 2", "year": 2011, "wiki": ["Cars 2"], "alts": []}, {"n": 38, "kind": "movie", "label": "Cars 3", "term": "Cars 3", "year": 2017, "wiki": ["Cars 3"], "alts": []}, {"n": 39, "kind": "movie", "label": "Casper", "term": "Casper", "year": 1995, "wiki": ["Casper (film)"], "alts": []}, {"n": 40, "kind": "movie", "label": "Charlotte's Web", "term": "Charlotte's Web", "year": 2006, "wiki": ["Charlotte's Web (2006 film)"], "alts": []}, {"n": 41, "kind": "movie", "label": "Charlotte's Web (1973)", "term": "Charlotte's Web", "year": 1973, "wiki": ["Charlotte's Web (1973 film)"], "alts": []}, {"n": 42, "kind": "movie", "label": "Cinderella (1950)", "term": "Cinderella", "year": 1950, "wiki": ["Cinderella (1950 film)"], "alts": []}, {"n": 43, "kind": "movie", "label": "Cloudy with a Chance of Meatballs", "term": "Cloudy with a Chance of Meatballs", "year": 2009, "wiki": ["Cloudy with a Chance of Meatballs (film)"], "alts": []}, {"n": 44, "kind": "movie", "label": "The Day the Earth Blew Up: A Looney Tunes Movie", "term": "The Day the Earth Blew Up: A Looney Tunes Movie", "year": 2024, "wiki": ["The Day the Earth Blew Up: A Looney Tunes Movie"], "alts": []}, {"n": 45, "kind": "movie", "label": "Diary of a Wimpy Kid", "term": "Diary of a Wimpy Kid", "year": 2010, "wiki": ["Diary of a Wimpy Kid (2010 film)", "Diary of a Wimpy Kid (film)"], "alts": []}, {"n": 46, "kind": "movie", "label": "Diary of a Wimpy Kid: Dog Days", "term": "Diary of a Wimpy Kid: Dog Days", "year": 2012, "wiki": ["Diary of a Wimpy Kid: Dog Days (film)"], "alts": []}, {"n": 47, "kind": "movie", "label": "Diary of a Wimpy Kid: Rodrick Rules", "term": "Diary of a Wimpy Kid: Rodrick Rules", "year": 2011, "wiki": ["Diary of a Wimpy Kid: Rodrick Rules (2011 film)", "Diary of a Wimpy Kid: Rodrick Rules (film)"], "alts": []}, {"n": 48, "kind": "movie", "label": "Diary of a Wimpy Kid: The Long Haul", "term": "Diary of a Wimpy Kid: The Long Haul", "year": 2017, "wiki": ["Diary of a Wimpy Kid: The Long Haul (film)"], "alts": []}, {"n": 49, "kind": "movie", "label": "Dog Man", "term": "Dog Man", "year": 2025, "wiki": ["Dog Man (film)"], "alts": []}, {"n": 50, "kind": "movie", "label": "Dr. Seuss' How the Grinch Stole Christmas (2000)", "term": "How the Grinch Stole Christmas", "year": 2000, "wiki": ["How the Grinch Stole Christmas (2000 film)"], "alts": []}, {"n": 51, "kind": "movie", "label": "Dr. Seuss' The Lorax", "term": "The Lorax", "year": 2012, "wiki": ["The Lorax (film)"], "alts": []}, {"n": 52, "kind": "movie", "label": "E.T. The Extra-Terrestrial", "term": "E.T. The Extra-Terrestrial", "year": 1982, "wiki": ["E.T. the Extra-Terrestrial"], "alts": ["E.T. the Extra-Terrestrial"]}, {"n": 53, "kind": "movie", "label": "Elf (2003)", "term": "Elf", "year": 2003, "wiki": ["Elf (film)"], "alts": []}, {"n": 54, "kind": "movie", "label": "Elio", "term": "Elio", "year": 2025, "wiki": ["Elio (film)"], "alts": []}, {"n": 55, "kind": "movie", "label": "The Emperor's New Groove", "term": "The Emperor's New Groove", "year": 2000, "wiki": ["The Emperor's New Groove"], "alts": []}, {"n": 56, "kind": "movie", "label": "Encanto", "term": "Encanto", "year": 2021, "wiki": ["Encanto (film)"], "alts": []}, {"n": 57, "kind": "movie", "label": "An Extremely Goofy Movie", "term": "An Extremely Goofy Movie", "year": 2000, "wiki": ["An Extremely Goofy Movie"], "alts": []}, {"n": 58, "kind": "movie", "label": "FernGully 2: The Magical Rescue", "term": "FernGully 2: The Magical Rescue", "year": 1998, "wiki": ["FernGully 2: The Magical Rescue"], "alts": []}, {"n": 59, "kind": "movie", "label": "FernGully: The Last Rainforest", "term": "FernGully: The Last Rainforest", "year": 1992, "wiki": ["FernGully: The Last Rainforest"], "alts": []}, {"n": 60, "kind": "movie", "label": "Finding Dory", "term": "Finding Dory", "year": 2016, "wiki": ["Finding Dory"], "alts": []}, {"n": 61, "kind": "movie", "label": "Finding Nemo", "term": "Finding Nemo", "year": 2003, "wiki": ["Finding Nemo"], "alts": []}, {"n": 62, "kind": "movie", "label": "Freaky Friday (2003)", "term": "Freaky Friday", "year": 2003, "wiki": ["Freaky Friday (2003 film)"], "alts": []}, {"n": 63, "kind": "movie", "label": "Frozen", "term": "Frozen", "year": 2013, "wiki": ["Frozen (2013 film)"], "alts": []}, {"n": 64, "kind": "movie", "label": "George of the Jungle", "term": "George of the Jungle", "year": 1997, "wiki": ["George of the Jungle (film)"], "alts": []}, {"n": 65, "kind": "movie", "label": "GOAT", "term": "GOAT", "year": 2026, "wiki": ["Goat (2026 film)", "GOAT (2026 film)", "Goat (film)", "GOAT (film)"], "alts": ["Goat"]}, {"n": 66, "kind": "movie", "label": "Good Burger", "term": "Good Burger", "year": 1997, "wiki": ["Good Burger"], "alts": []}, {"n": 67, "kind": "movie", "label": "Good Burger 2", "term": "Good Burger 2", "year": 2023, "wiki": ["Good Burger 2"], "alts": []}, {"n": 68, "kind": "movie", "label": "Herbie: Fully Loaded", "term": "Herbie: Fully Loaded", "year": 2005, "wiki": ["Herbie: Fully Loaded"], "alts": []}, {"n": 69, "kind": "movie", "label": "Hercules", "term": "Hercules", "year": 1997, "wiki": ["Hercules (1997 film)"], "alts": []}, {"n": 70, "kind": "movie", "label": "Hey Arnold! The Movie", "term": "Hey Arnold! The Movie", "year": 2002, "wiki": ["Hey Arnold!: The Movie"], "alts": ["Hey Arnold!: The Movie"]}, {"n": 71, "kind": "movie", "label": "Hocus Pocus", "term": "Hocus Pocus", "year": 1993, "wiki": ["Hocus Pocus (1993 film)"], "alts": []}, {"n": 72, "kind": "movie", "label": "Holes", "term": "Holes", "year": 2003, "wiki": ["Holes (film)"], "alts": []}, {"n": 73, "kind": "movie", "label": "Home on the Range", "term": "Home on the Range", "year": 2004, "wiki": ["Home on the Range (2004 film)"], "alts": []}, {"n": 74, "kind": "movie", "label": "Hoppers", "term": "Hoppers", "year": 2026, "wiki": ["Hoppers (film)"], "alts": []}, {"n": 75, "kind": "movie", "label": "How the Grinch Stole Christmas (animated)", "term": "How the Grinch Stole Christmas", "year": 1966, "wiki": ["How the Grinch Stole Christmas! (TV special)"], "alts": ["How the Grinch Stole Christmas!"]}, {"n": 76, "kind": "movie", "label": "Ice Age", "term": "Ice Age", "year": 2002, "wiki": ["Ice Age (2002 film)"], "alts": []}, {"n": 77, "kind": "movie", "label": "Illumination Presents: Dr. Seuss' The Grinch", "term": "The Grinch", "year": 2018, "wiki": ["The Grinch (film)"], "alts": []}, {"n": 78, "kind": "movie", "label": "Inspector Gadget", "term": "Inspector Gadget", "year": 1999, "wiki": ["Inspector Gadget (1999 film)"], "alts": []}, {"n": 79, "kind": "movie", "label": "Jimmy Neutron: Boy Genius", "term": "Jimmy Neutron: Boy Genius", "year": 2001, "wiki": ["Jimmy Neutron: Boy Genius"], "alts": []}, {"n": 80, "kind": "movie", "label": "King Tweety", "term": "King Tweety", "year": 2022, "wiki": ["King Tweety"], "alts": []}, {"n": 81, "kind": "movie", "label": "Kronk's New Groove", "term": "Kronk's New Groove", "year": 2005, "wiki": ["Kronk's New Groove"], "alts": []}, {"n": 82, "kind": "movie", "label": "Kung Fu Panda", "term": "Kung Fu Panda", "year": 2008, "wiki": ["Kung Fu Panda (film)"], "alts": []}, {"n": 83, "kind": "movie", "label": "Lady and the Tramp", "term": "Lady and the Tramp", "year": 1955, "wiki": ["Lady and the Tramp"], "alts": []}, {"n": 84, "kind": "movie", "label": "The Land of Sometimes", "term": "The Land of Sometimes", "year": 2015, "wiki": ["The Land of Sometimes"], "alts": []}, {"n": 85, "kind": "movie", "label": "The LEGO Movie", "term": "The LEGO Movie", "year": 2014, "wiki": ["The Lego Movie"], "alts": ["The Lego Movie"]}, {"n": 86, "kind": "movie", "label": "Lemony Snicket's A Series of Unfortunate Events", "term": "Lemony Snicket's A Series of Unfortunate Events", "year": 2004, "wiki": ["Lemony Snicket's A Series of Unfortunate Events"], "alts": []}, {"n": 87, "kind": "movie", "label": "Lilo & Stitch", "term": "Lilo & Stitch", "year": 2002, "wiki": ["Lilo & Stitch"], "alts": []}, {"n": 88, "kind": "movie", "label": "Lilo & Stitch 2: Stitch Has a Glitch", "term": "Lilo & Stitch 2: Stitch Has a Glitch", "year": 2005, "wiki": ["Lilo & Stitch 2: Stitch Has a Glitch"], "alts": []}, {"n": 89, "kind": "movie", "label": "The Lion King", "term": "The Lion King", "year": 1994, "wiki": ["The Lion King"], "alts": []}, {"n": 90, "kind": "movie", "label": "The Little Mermaid (animated)", "term": "The Little Mermaid", "year": 1989, "wiki": ["The Little Mermaid (1989 film)"], "alts": []}, {"n": 91, "kind": "movie", "label": "The Little Mermaid (live action)", "term": "The Little Mermaid", "year": 2023, "wiki": ["The Little Mermaid (2023 film)"], "alts": []}, {"n": 92, "kind": "movie", "label": "Looney Tunes: Rabbits Run", "term": "Looney Tunes: Rabbits Run", "year": 2015, "wiki": ["Looney Tunes: Rabbits Run"], "alts": []}, {"n": 93, "kind": "movie", "label": "Mary Poppins", "term": "Mary Poppins", "year": 1964, "wiki": ["Mary Poppins (film)"], "alts": []}, {"n": 94, "kind": "movie", "label": "Mary Poppins Returns", "term": "Mary Poppins Returns", "year": 2018, "wiki": ["Mary Poppins Returns"], "alts": []}, {"n": 95, "kind": "movie", "label": "Matilda", "term": "Matilda", "year": 1996, "wiki": ["Matilda (1996 film)"], "alts": []}, {"n": 96, "kind": "movie", "label": "A Minecraft Movie", "term": "A Minecraft Movie", "year": 2025, "wiki": ["A Minecraft Movie"], "alts": []}, {"n": 97, "kind": "movie", "label": "Minions & Monsters", "term": "Minions & Monsters", "year": 2026, "wiki": ["Minions & Monsters", "Minions 3"], "alts": ["Minions 3"]}, {"n": 98, "kind": "movie", "label": "Monster Trucks", "term": "Monster Trucks", "year": 2017, "wiki": ["Monster Trucks (film)"], "alts": []}, {"n": 99, "kind": "movie", "label": "The Mouse and the Motorcycle", "term": "The Mouse and the Motorcycle", "year": "", "wiki": ["The Mouse and the Motorcycle (film)", "The Mouse and the Motorcycle (2025 film)", "The Mouse and the Motorcycle (2026 film)"], "alts": []}, {"n": 100, "kind": "movie", "label": "My Life as a Zucchini", "term": "My Life as a Zucchini", "year": 2016, "wiki": ["My Life as a Zucchini"], "alts": []}, {"n": 101, "kind": "movie", "label": "PAW Patrol movie", "term": "PAW Patrol: The Dino Movie", "year": 2026, "wiki": ["PAW Patrol: The Dino Movie"], "alts": []}, {"n": 102, "kind": "movie", "label": "Paws of Fury: The Legend of Hank", "term": "Paws of Fury: The Legend of Hank", "year": 2022, "wiki": ["Paws of Fury: The Legend of Hank"], "alts": []}, {"n": 103, "kind": "movie", "label": "Pinocchio", "term": "Pinocchio", "year": 1940, "wiki": ["Pinocchio (1940 film)"], "alts": []}, {"n": 104, "kind": "movie", "label": "Pocahontas", "term": "Pocahontas", "year": 1995, "wiki": ["Pocahontas (1995 film)"], "alts": []}, {"n": 105, "kind": "movie", "label": "The Pout-Pout Fish", "term": "The Pout-Pout Fish", "year": "", "wiki": ["The Pout-Pout Fish (film)", "The Pout-Pout Fish (2026 film)"], "alts": []}, {"n": 106, "kind": "movie", "label": "The Princess Diaries", "term": "The Princess Diaries", "year": 2001, "wiki": ["The Princess Diaries (film)"], "alts": []}, {"n": 107, "kind": "movie", "label": "Rango", "term": "Rango", "year": 2011, "wiki": ["Rango (2011 film)"], "alts": []}, {"n": 108, "kind": "movie", "label": "Roald Dahl's The Witches", "term": "Roald Dahl's The Witches", "year": 2020, "wiki": ["The Witches (2020 film)"], "alts": ["The Witches"]}, {"n": 109, "kind": "movie", "label": "Rudolph the Red-Nosed Reindeer", "term": "Rudolph the Red-Nosed Reindeer", "year": 1964, "wiki": ["Rudolph the Red-Nosed Reindeer (TV special)"], "alts": []}, {"n": 110, "kind": "movie", "label": "Rugrats Go Wild", "term": "Rugrats Go Wild", "year": 2003, "wiki": ["Rugrats Go Wild"], "alts": []}, {"n": 111, "kind": "movie", "label": "Rugrats in Paris: The Movie", "term": "Rugrats in Paris: The Movie", "year": 2000, "wiki": ["Rugrats in Paris: The Movie"], "alts": []}, {"n": 112, "kind": "movie", "label": "The Rugrats Movie", "term": "The Rugrats Movie", "year": 1998, "wiki": ["The Rugrats Movie"], "alts": []}, {"n": 113, "kind": "movie", "label": "Rumble", "term": "Rumble", "year": 2021, "wiki": ["Rumble (2021 film)"], "alts": []}, {"n": 114, "kind": "movie", "label": "The Santa Clause", "term": "The Santa Clause", "year": 1994, "wiki": ["The Santa Clause"], "alts": []}, {"n": 115, "kind": "movie", "label": "The Santa Clause 2", "term": "The Santa Clause 2", "year": 2002, "wiki": ["The Santa Clause 2"], "alts": []}, {"n": 116, "kind": "movie", "label": "The Santa Clause 3: The Escape Clause", "term": "The Santa Clause 3: The Escape Clause", "year": 2006, "wiki": ["The Santa Clause 3: The Escape Clause"], "alts": []}, {"n": 117, "kind": "movie", "label": "SCOOB!", "term": "SCOOB!", "year": 2020, "wiki": ["Scoob!"], "alts": ["Scoob!"]}, {"n": 118, "kind": "movie", "label": "Scooby-Doo and the Witch's Ghost", "term": "Scooby-Doo and the Witch's Ghost", "year": 1999, "wiki": ["Scooby-Doo and the Witch's Ghost"], "alts": []}, {"n": 119, "kind": "movie", "label": "A Scooby-Doo Valentine", "term": "Scooby-Doo! Valentine", "year": 2012, "wiki": ["A Scooby-Doo! Valentine", "A Scooby-Doo Valentine"], "alts": ["A Scooby-Doo Valentine", "A Scooby-Doo! Valentine"]}, {"n": 120, "kind": "movie", "label": "Scooby-Doo! and the Legend of the Vampire", "term": "Scooby-Doo! and the Legend of the Vampire", "year": 2003, "wiki": ["Scooby-Doo! and the Legend of the Vampire"], "alts": []}, {"n": 121, "kind": "movie", "label": "Scooby-Doo! Frankencreepy", "term": "Scooby-Doo! Frankencreepy", "year": 2014, "wiki": ["Scooby-Doo! Frankencreepy"], "alts": []}, {"n": 122, "kind": "movie", "label": "Scooby-Doo! Moon Monster Madness", "term": "Scooby-Doo! Moon Monster Madness", "year": 2015, "wiki": ["Scooby-Doo! Moon Monster Madness"], "alts": []}, {"n": 123, "kind": "movie", "label": "Scooby-Doo! Return to Zombie Island", "term": "Scooby-Doo! Return to Zombie Island", "year": 2019, "wiki": ["Scooby-Doo! Return to Zombie Island"], "alts": []}, {"n": 124, "kind": "movie", "label": "Shrek", "term": "Shrek", "year": 2001, "wiki": ["Shrek"], "alts": []}, {"n": 125, "kind": "movie", "label": "Shrek 2", "term": "Shrek 2", "year": 2004, "wiki": ["Shrek 2"], "alts": []}, {"n": 126, "kind": "movie", "label": "Shrek Forever After", "term": "Shrek Forever After", "year": 2010, "wiki": ["Shrek Forever After"], "alts": []}, {"n": 127, "kind": "movie", "label": "Shrek the Third", "term": "Shrek the Third", "year": 2007, "wiki": ["Shrek the Third"], "alts": []}, {"n": 128, "kind": "movie", "label": "Sonic the Hedgehog", "term": "Sonic the Hedgehog", "year": 2020, "wiki": ["Sonic the Hedgehog (film)"], "alts": []}, {"n": 129, "kind": "movie", "label": "Sonic the Hedgehog 2", "term": "Sonic the Hedgehog 2", "year": 2022, "wiki": ["Sonic the Hedgehog 2 (film)"], "alts": []}, {"n": 130, "kind": "movie", "label": "Sonic the Hedgehog 3", "term": "Sonic the Hedgehog 3", "year": 2024, "wiki": ["Sonic the Hedgehog 3 (film)"], "alts": []}, {"n": 131, "kind": "movie", "label": "Space Jam", "term": "Space Jam", "year": 1996, "wiki": ["Space Jam"], "alts": []}, {"n": 132, "kind": "movie", "label": "Space Jam: A New Legacy", "term": "Space Jam: A New Legacy", "year": 2021, "wiki": ["Space Jam: A New Legacy"], "alts": []}, {"n": 133, "kind": "movie", "label": "The SpongeBob SquarePants Movie", "term": "The SpongeBob SquarePants Movie", "year": 2004, "wiki": ["The SpongeBob SquarePants Movie"], "alts": []}, {"n": 134, "kind": "movie", "label": "Spy Kids", "term": "Spy Kids", "year": 2001, "wiki": ["Spy Kids (film)"], "alts": []}, {"n": 135, "kind": "movie", "label": "Spy Kids 2: The Island of Lost Dreams", "term": "Spy Kids 2: The Island of Lost Dreams", "year": 2002, "wiki": ["Spy Kids 2: The Island of Lost Dreams"], "alts": []}, {"n": 136, "kind": "movie", "label": "Spy Kids 3: Game Over", "term": "Spy Kids 3: Game Over", "year": 2003, "wiki": ["Spy Kids 3-D: Game Over"], "alts": ["Spy Kids 3-D: Game Over"]}, {"n": 137, "kind": "movie", "label": "Straight Outta Nowhere: Scooby-Doo! Meets Courage the Cowardly Dog", "term": "Straight Outta Nowhere: Scooby-Doo! Meets Courage the Cowardly Dog", "year": 2021, "wiki": ["Straight Outta Nowhere: Scooby-Doo! Meets Courage the Cowardly Dog"], "alts": []}, {"n": 138, "kind": "movie", "label": "The Super Mario Bros. Movie", "term": "The Super Mario Bros. Movie", "year": 2023, "wiki": ["The Super Mario Bros. Movie"], "alts": []}, {"n": 139, "kind": "movie", "label": "The Super Mario Galaxy Movie", "term": "The Super Mario Galaxy Movie", "year": 2026, "wiki": ["The Super Mario Galaxy Movie"], "alts": []}, {"n": 140, "kind": "movie", "label": "Tarzan (1999)", "term": "Tarzan", "year": 1999, "wiki": ["Tarzan (1999 film)"], "alts": []}, {"n": 141, "kind": "movie", "label": "Toy Story", "term": "Toy Story", "year": 1995, "wiki": ["Toy Story"], "alts": []}, {"n": 142, "kind": "movie", "label": "Toy Story 2", "term": "Toy Story 2", "year": 1999, "wiki": ["Toy Story 2"], "alts": []}, {"n": 143, "kind": "movie", "label": "Toy Story 3", "term": "Toy Story 3", "year": 2010, "wiki": ["Toy Story 3"], "alts": []}, {"n": 144, "kind": "movie", "label": "Toy Story 4", "term": "Toy Story 4", "year": 2019, "wiki": ["Toy Story 4"], "alts": []}, {"n": 145, "kind": "movie", "label": "Toy Story 5", "term": "Toy Story 5", "year": 2026, "wiki": ["Toy Story 5"], "alts": []}, {"n": 146, "kind": "movie", "label": "We're Back! A Dinosaur's Story", "term": "We're Back! A Dinosaur's Story", "year": 1993, "wiki": ["We're Back! A Dinosaur's Story"], "alts": []}, {"n": 147, "kind": "movie", "label": "The Wild Thornberrys Movie", "term": "The Wild Thornberrys Movie", "year": 2002, "wiki": ["The Wild Thornberrys Movie"], "alts": []}, {"n": 148, "kind": "movie", "label": "Willy Wonka and the Chocolate Factory", "term": "Willy Wonka & the Chocolate Factory", "year": 1971, "wiki": ["Willy Wonka & the Chocolate Factory"], "alts": []}, {"n": 149, "kind": "movie", "label": "The Wizard of Oz", "term": "The Wizard of Oz", "year": 1939, "wiki": ["The Wizard of Oz (1939 film)"], "alts": []}, {"n": 150, "kind": "movie", "label": "Zootopia 2", "term": "Zootopia 2", "year": 2025, "wiki": ["Zootopia 2"], "alts": []}]""")
UA = "AppleTVLibraryCovers/4.0 (personal, non-commercial) Python-urllib"
WIKI_BAD = ("novel", "book", "album", "soundtrack", "video game", "song", "franchise")

if os.name == "nt":
    os.system("")
def say(s, c=None):
    codes = {"g": "92", "y": "93", "r": "91", "c": "96", "d": "90"}
    print(f"\033[{codes[c]}m{s}\033[0m" if c else s, flush=True)

# ---------- keys ----------
def load_keys():
    keys = {}
    if os.path.exists(KEYS):
        for line in open(KEYS, encoding="utf-8"):
            if "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip().upper()] = v.strip()
    changed = False
    if "TMDB" not in keys:
        say("TMDB key (from themoviedb.org > Settings > API). Paste the 'API Key' or the long", "c")
        say("'API Read Access Token', then press Enter. Press Enter alone to skip TMDB:", "c")
        keys["TMDB"] = input("> ").strip(); changed = True
    if "FANART" not in keys:
        say("fanart.tv personal API key (from fanart.tv > your profile > API). Enter alone to skip:", "c")
        keys["FANART"] = input("> ").strip(); changed = True
    if changed:
        with open(KEYS, "w", encoding="utf-8") as f:
            f.write(f"TMDB={keys['TMDB']}\nFANART={keys['FANART']}\n")
        say("Saved keys to keys.txt (delete that file to enter new keys).\n", "d")
    return keys.get("TMDB", ""), keys.get("FANART", "")

# ---------- web ----------
def fetch(url, headers=None, tries=4):
    h = {"User-Agent": UA, "Accept": "application/json"}
    h.update(headers or {})
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=40) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403) and "themoviedb" in url:
                raise PermissionError("TMDB key was rejected")
            if e.code == 404:
                return None
            if e.code in (429, 503) and i < tries - 1:
                wait = e.headers.get("Retry-After")
                wait = min(int(wait), 20) if (wait and wait.isdigit()) else 4 * (i + 1)
                say(f"   (busy - waiting {wait}s)", "d")
                time.sleep(wait)
            else:
                time.sleep(1.5)
        except PermissionError:
            raise
        except Exception:
            time.sleep(1.5)
    return None

def getjson(url, headers=None):
    raw = fetch(url, headers)
    try:
        return json.loads(raw.decode("utf-8")) if raw else None
    except Exception:
        return None

def norm(s):
    s = (s or "").lower().replace("&", "and")
    s = re.sub(r"^(the|a|an)\s+", "", s)
    return re.sub(r"[^a-z0-9]", "", s)

def safe(s):
    return re.sub(r'[\\/:*?"<>|]', "", s).strip()

# ---------- TMDB ----------
class TMDB:
    def __init__(self, key):
        self.key = key
        self.bearer = len(key) > 40
    def get(self, path, **params):
        params.setdefault("language", "en-US")
        if not self.bearer:
            params["api_key"] = self.key
        hdr = {"Authorization": f"Bearer {self.key}"} if self.bearer else {}
        js = getjson("https://api.themoviedb.org/3" + path + "?" + urllib.parse.urlencode(params), hdr)
        time.sleep(0.12)
        return js
    def find(self, kind, names, year):
        """Return (result, sure) for the best match, or (None, False)."""
        wanted = {norm(n) for n in names if n}
        best, best_score = None, -999
        for name in names:
            if kind == "tv":
                js = self.get("/search/tv", query=name, include_adult="false")
            else:
                js = self.get("/search/movie", query=name, include_adult="false")
            for r in (js or {}).get("results", [])[:10]:
                title = r.get("name") if kind == "tv" else r.get("title")
                orig = r.get("original_name") if kind == "tv" else r.get("original_title")
                date = r.get("first_air_date") if kind == "tv" else r.get("release_date")
                y = int(date[:4]) if date and date[:4].isdigit() else None
                s = 0
                if norm(title) in wanted or norm(orig) in wanted: s += 100
                elif any(w and (norm(title).startswith(w) or w.startswith(norm(title))) for w in wanted): s += 40
                else: continue
                if year and y:
                    d = abs(y - int(year))
                    s += 60 if d == 0 else (35 if d == 1 else -80)
                if not r.get("poster_path"): s -= 50
                s += min(r.get("popularity", 0), 50) / 10
                if s > best_score:
                    best, best_score = r, s
            if best_score >= 160:
                break
        if not best or best_score < 90:
            return None, False
        return best, (best_score >= 160 or (not year and best_score >= 100))
    def poster(self, r):
        p = r.get("poster_path")
        return f"https://image.tmdb.org/t/p/w780{p}" if p else None
    def tvdb_id(self, tmdb_id):
        js = self.get(f"/tv/{tmdb_id}/external_ids")
        return (js or {}).get("tvdb_id")

# ---------- fanart.tv ----------
def fanart_poster(key, kind, ident):
    if not key or not ident:
        return None
    url = f"https://webservice.fanart.tv/v3/{'tv' if kind == 'tv' else 'movies'}/{ident}?api_key={key}"
    js = getjson(url)
    time.sleep(0.2)
    if not js:
        return None
    arts = js.get("tvposter" if kind == "tv" else "movieposter") or []
    arts = sorted(arts, key=lambda a: (a.get("lang") not in ("en", "00", ""), -int(a.get("likes") or 0)))
    return arts[0]["url"] if arts else None

# ---------- Wikipedia (exact pages) ----------
QIDS = {}
def wiki_lookup(titles):
    out = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        p = {"action": "query", "format": "json", "formatversion": 2, "redirects": 1,
             "prop": "pageimages|description|pageprops", "ppprop": "wikibase_item",
             "piprop": "original|thumbnail", "pithumbsize": 600,
             "pilicense": "any", "titles": "|".join(chunk)}
        js = getjson("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(p))
        q = (js or {}).get("query", {})
        name = {t: t for t in chunk}
        for m in q.get("normalized", []) + q.get("redirects", []):
            for k, v in name.items():
                if v == m["from"]:
                    name[k] = m["to"]
        pages = {pg["title"]: pg for pg in q.get("pages", []) if not pg.get("missing")}
        for asked, final in name.items():
            pg = pages.get(final)
            if not pg:
                continue
            q = (pg.get("pageprops") or {}).get("wikibase_item")
            if q:
                QIDS[asked] = q
            if any(b in (pg.get("description") or "").lower() for b in WIKI_BAD):
                continue
            o, t = pg.get("original") or {}, pg.get("thumbnail") or {}
            src = o.get("source") if o.get("width", 9999) <= 1200 else t.get("source")
            src = src or t.get("source")
            if src and not src.lower().endswith(".svg"):
                out[asked] = src
        time.sleep(1)
    return out

# ---------- saving ----------
def clear(prefix):
    for f in os.listdir(OUT):
        if re.match(re.escape(prefix) + r"[a-z]? - ", f):
            try: os.remove(os.path.join(OUT, f))
            except OSError: pass

def download(url):
    data = fetch(url, {"Accept": "image/*"})
    return data if data and len(data) > 1500 else None

def write(data, prefix, label):
    ext = ".png" if data[:4] == b"\x89PNG" else ".jpg"
    fn = f"{prefix} - {safe(label)}{ext}"
    with open(os.path.join(OUT, fn), "wb") as f:
        f.write(data)
    return fn

# ---------- Apple TV links (from Wikidata) ----------
def sparql(query):
    data = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
    req = urllib.request.Request("https://query.wikidata.org/sparql", data=data,
                                 headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8")).get("results", {}).get("bindings", [])
        except Exception:
            time.sleep(5)
    return []

UMC = 'FILTER(isLiteral(?v) && STRSTARTS(STR(?v), "umc.cmc."))'

def apple_links(entries):
    """entries: {n3: {"kind":..., "tmdb": id or None, "qid": Q or None}} -> {n3: {"kind":..., "id": umc...}}"""
    found = {}
    qids = sorted({e["qid"] for e in entries.values() if e.get("qid")})
    by_q = {}
    for i in range(0, len(qids), 80):
        vals = " ".join("wd:" + q for q in qids[i:i + 80])
        for b in sparql(f"SELECT ?item ?v WHERE {{ VALUES ?item {{ {vals} }} ?item ?p ?v . {UMC} }}"):
            by_q[b["item"]["value"].rsplit("/", 1)[-1]] = b["v"]["value"]
        time.sleep(1)
    by_tmdb = {}
    for kind, prop in (("movie", "P4947"), ("tv", "P4983")):
        ids = sorted({str(e["tmdb"]) for e in entries.values() if e.get("tmdb") and e["kind"] == kind})
        for i in range(0, len(ids), 80):
            vals = " ".join(f'"{x}"' for x in ids[i:i + 80])
            for b in sparql(f"SELECT ?tm ?v WHERE {{ VALUES ?tm {{ {vals} }} ?item wdt:{prop} ?tm . ?item ?p ?v . {UMC} }}"):
                by_tmdb[(kind, b["tm"]["value"])] = b["v"]["value"]
            time.sleep(1)
    for n3, e in entries.items():
        umc = by_tmdb.get((e["kind"], str(e.get("tmdb")))) or by_q.get(e.get("qid") or "")
        if umc:
            found[n3] = {"kind": e["kind"], "id": umc}
    return found

# ---------- details (year, rating, runtime, summary) ----------
META = {}
def details(tm, tid):
    if not tm or not tid:
        return {}
    kind, ident = tid
    try:
        if kind == "tv":
            js = tm.get(f"/tv/{ident}", append_to_response="content_ratings") or {}
            rating = next((x.get("rating") for x in (js.get("content_ratings") or {}).get("results", []) if x.get("iso_3166_1") == "US"), "")
            return dict(tmdb_id=ident, kind="tv", title=js.get("name"), year=(js.get("first_air_date") or "")[:4],
                        rating=rating, seasons=js.get("number_of_seasons"), genres=[g["name"] for g in js.get("genres", [])],
                        overview=js.get("overview", ""))
        js = tm.get(f"/movie/{ident}", append_to_response="release_dates") or {}
        rating = ""
        for c in (js.get("release_dates") or {}).get("results", []):
            if c.get("iso_3166_1") == "US":
                rating = next((d.get("certification") for d in c.get("release_dates", []) if d.get("certification")), "")
        return dict(tmdb_id=ident, kind="movie", title=js.get("title"), year=(js.get("release_date") or "")[:4],
                    rating=rating, runtime=js.get("runtime"), genres=[g["name"] for g in js.get("genres", [])],
                    overview=js.get("overview", ""))
    except PermissionError:
        raise
    except Exception:
        return {}

# ---------- main ----------
def find_one(tm, fkey, wiki, kind, names, year, wiki_titles):
    """Try TMDB, then fanart.tv, then Wikipedia. Returns (url, source, sure, found)."""
    if tm:
        r, sure = tm.find(kind, names, year)
        if r:
            title = r.get("name") if kind == "tv" else r.get("title")
            date = (r.get("first_air_date") if kind == "tv" else r.get("release_date")) or ""
            found = f"{title} ({date[:4]})"
            url = tm.poster(r)
            if url:
                return url, "TMDB", sure, found, (kind, r["id"])
            ident = tm.tvdb_id(r["id"]) if kind == "tv" else r["id"]
            url = fanart_poster(fkey, kind, ident)
            if url:
                return url, "fanart.tv", sure, found, (kind, r["id"])
    for t in wiki_titles:
        if t in wiki:
            return wiki[t], "Wikipedia", True, t, None
    return None, None, False, "", None

def main():
    tkey, fkey = load_keys()
    tm = TMDB(tkey) if tkey else None
    if tm:
        try:
            tm.get("/configuration")
        except PermissionError:
            say("TMDB didn't accept that key. Delete keys.txt and run again to re-enter it.", "r")
            tm = None
    say("Sources: " + ", ".join(s for s, on in (("TMDB", tm), ("fanart.tv", fkey), ("Wikipedia", True)) if on), "c")

    say("Looking up Wikipedia pages (backup source)...", "d")
    all_wiki = sorted({t for p in PLAN for t in p.get("wiki", [])})
    wiki = wiki_lookup(all_wiki)
    say(f"Getting covers for {len(PLAN)} titles into: {OUT}\n", "c")

    log = []
    LINKS_IN = {}
    for p in PLAN:
        n3 = f"{p['n']:03d}"
        label = p["label"]
        say(f"[{p['n']}] {label}")
        try:
            if "choices" in p:
                got = []
                for i, ch in enumerate(p["choices"]):
                    wt = [p["wiki"][i]] if i < len(p.get("wiki", [])) else []
                    url, src, sure, found, tid = find_one(tm, fkey, wiki, ch["kind"], [ch["term"]], ch["year"], wt)
                    data = download(url) if url else None
                    if data:
                        got.append((data, src, found or ch["term"]))
                        key = f"{n3}{chr(97 + len(got) - 1)}"
                        META[key] = details(tm, tid)
                        LINKS_IN[key] = {"kind": ch["kind"], "tmdb": tid[1] if tid else None,
                                         "qid": QIDS.get(wt[0]) if wt else None}
                if got:
                    clear(n3)
                    for i, (data, src, found) in enumerate(got):
                        fn = write(data, f"{n3}{chr(97 + i)}", found)
                        say(f"   choice {chr(97 + i)}: {found}  [{src}]", "y")
                        log.append(dict(number=f"{p['n']}{chr(97 + i)}", title=label, found=found, source=src, file=fn, status="CHOICE"))
                else:
                    say("   nothing found - keeping what's there", "r")
                    log.append(dict(number=p["n"], title=label, found="", source="", file="", status="NOT FOUND"))
                continue

            names = [p["term"]] + p.get("alts", [])
            url, src, sure, found, tid = find_one(tm, fkey, wiki, p["kind"], names, p["year"], p.get("wiki", []))
            data = download(url) if url else None
            if data:
                clear(n3)
                fn = write(data, n3, label)
                status = "OK" if sure else "CHECK"
                META[n3] = details(tm, tid)
                LINKS_IN[n3] = {"kind": p["kind"], "tmdb": tid[1] if tid else None,
                                "qid": next((QIDS[t] for t in p.get("wiki", []) if t in QIDS), None)}
                say(f"   {found}  [{src}]", "g" if sure else "y")
                log.append(dict(number=p["n"], title=label, found=found, source=src, file=fn, status=status))
            else:
                have = [f for f in os.listdir(OUT) if f.startswith(n3)]
                say("   not found" + (" - keeping the one already there" if have else ""), "r")
                log.append(dict(number=p["n"], title=label, found="", source="", file=have[0] if have else "", status="NOT FOUND"))
        except PermissionError:
            say("TMDB stopped accepting the key - continuing without it.", "r")
            tm = None

    say("\nLooking up Apple TV links...", "c")
    links = apple_links(LINKS_IN)
    say(f"Found direct Apple TV links for {len(links)} of {len(LINKS_IN)} titles (the rest will open an Apple TV search).", "c")
    with open(os.path.join(OUT, "apple-links.json"), "w", encoding="utf-8") as f:
        json.dump(links, f, indent=1)
    with open(os.path.join(OUT, "details.json"), "w", encoding="utf-8") as f:
        json.dump(META, f, indent=1, ensure_ascii=False)
    with open(os.path.join(OUT, "covers-log.json"), "w", encoding="utf-8") as f:
        json.dump(log, f, indent=1)
    with open(os.path.join(OUT, "covers-log.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["number", "title", "found", "source", "file", "status"])
        w.writeheader(); w.writerows(log)
    ok = sum(x["status"] in ("OK", "CHOICE") for x in log)
    chk = sum(x["status"] == "CHECK" for x in log)
    bad = sum(x["status"] == "NOT FOUND" for x in log)
    say(f"\nDone. {ok} matched, {chk} to double-check, {bad} not found.", "c")
    say("Go back to Claude and say: covers are done")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say("\nStopped. Run it again any time.", "y")
    try:
        input("\nPress Enter to close this window...")
    except EOFError:
        pass
