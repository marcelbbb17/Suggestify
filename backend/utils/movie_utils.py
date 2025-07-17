import re
import json
import nltk
import os
from collections import Counter
import requests
import ast
from datetime import datetime, timedelta

# Define global variables with fallback implementations
def simple_tokenize(text):
    """ Simple fallback tokenizer that splits text on whitespace """
    return text.lower().split() if text else []

class SimpleStopwords:
    """ Simple fallback for NLTK stopwords """
    @staticmethod
    def words(lang):
        return set(['a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'else', 'when', 
                   'at', 'from', 'by', 'for', 'with', 'about', 'against', 'between', 
                   'into', 'through', 'during', 'before', 'after', 'above', 'below', 
                   'to', 'of', 'in', 'on', 'is', 'are', 'was', 'were', 'be', 'been', 'being'])

class SimpleLemmatizer:
    """Simple fallback for NLTK WordNetLemmatizer."""
    def lemmatize(self, word, pos=None):
        return word

word_tokenize = simple_tokenize
stopwords = SimpleStopwords()
WordNetLemmatizer = SimpleLemmatizer()

def safe_initialize_nltk():
    """ Safely initialise NLTK """
    global word_tokenize, stopwords, WordNetLemmatizer
    
    try:
        # Use Render's NLTK data directory if available, otherwise use home directory
        if os.environ.get('RENDER'):
            nltk_data_dir = '/opt/render/nltk_data'
        else:
            home_dir = os.path.expanduser("~")
            nltk_data_dir = os.path.join(home_dir, "nltk_data")
        os.makedirs(nltk_data_dir, exist_ok=True)
        nltk.data.path.insert(0, nltk_data_dir)
        print(f"NLTK data directory set to: {nltk_data_dir}")
    except Exception as e:
        print(f"Error setting NLTK data directory: {e}")
    
    resources_available = {
        'punkt': False,
        'punkt_tab': False,  # Add this for Render
        'stopwords': False,
        'wordnet': False
    }
    
    # Try to download resources
    for resource in resources_available.keys():
        try:
            # Check if resource exists first
            try:
                if resource == 'punkt':
                    nltk.data.find('tokenizers/punkt')
                elif resource == 'punkt_tab':
                    nltk.data.find('tokenizers/punkt_tab')
                else:
                    nltk.data.find(f'corpora/{resource}')
                resources_available[resource] = True
                print(f"NLTK {resource} already available")
            except LookupError:
                # Download if not found
                print(f"Downloading NLTK {resource}")
                nltk.download(resource, download_dir=nltk_data_dir, quiet=True)
                resources_available[resource] = True
        except Exception as e:
            print(f"Failed to download/find {resource}: {e}")
    
    # Initialise tokenizer if punkt OR punkt_tab is available
    if resources_available['punkt'] or resources_available['punkt_tab']:
        try:
            from nltk.tokenize import word_tokenize as nltk_tokenize
            # Test it works
            test_result = nltk_tokenize("Test sentence")
            if test_result and isinstance(test_result, list):
                word_tokenize = nltk_tokenize
                print("Successfully loaded word_tokenize")
            else:
                print("word_tokenize test failed, using fallback")
        except Exception as e:
            print(f"Error initializing word_tokenize: {e}")
    
    # Initialise stopwords if available
    if resources_available['stopwords']:
        try:
            from nltk.corpus import stopwords as nltk_stopwords
            # Test it works
            test_result = nltk_stopwords.words('english')
            if test_result and isinstance(test_result, list):
                stopwords = nltk_stopwords
                print("Successfully loaded stopwords")
            else:
                print("stopwords test failed, using fallback")
        except Exception as e:
            print(f"Error initializing stopwords: {e}")
    
    # Initialise lemmatizer if wordnet is available
    if resources_available['wordnet']:
        try:
            from nltk.stem import WordNetLemmatizer as NltkLemmatizer
            lemmatizer = NltkLemmatizer()
            # Test it works
            test_result = lemmatizer.lemmatize("testing")
            if test_result and isinstance(test_result, str):
                WordNetLemmatizer = lemmatizer
                print("Successfully loaded WordNetLemmatizer")
            else:
                print("WordNetLemmatizer test failed, using fallback")
        except Exception as e:
            print(f"Error initializing WordNetLemmatizer: {e}")
    
    print("NLTK initialisation completed with the following components:")
    print(f"- word_tokenize: {'NLTK version' if word_tokenize != simple_tokenize else 'Fallback version'}")
    print(f"- stopwords: {'NLTK version' if stopwords != SimpleStopwords() else 'Fallback version'}")
    print(f"- WordNetLemmatizer: {'NLTK version' if not isinstance(WordNetLemmatizer, SimpleLemmatizer) else 'Fallback version'}")

safe_initialize_nltk()

from config import get_config

config = get_config()
TMDB_KEY = config.TMDB_API_KEY

THEME_KEYWORDS = {
    'redemption': ['redemption', 'redeem', 'second chance', 'forgiveness', 'atone', 'atonement', 'salvation'],
    'revenge': ['revenge', 'vengeance', 'avenge', 'retribution', 'payback', 'vendetta'],
    'coming_of_age': ['coming of age', 'growing up', 'adolescence', 'maturity', 'youth', 'teenager'],
    'survival': ['survival', 'survive', 'wilderness', 'disaster', 'apocalypse', 'catastrophe'],
    'love': ['love', 'romance', 'romantic', 'relationship', 'passion', 'affair'],
    'family': ['family', 'father', 'mother', 'son', 'daughter', 'parent', 'sibling', 'brother', 'sister'],
    'friendship': ['friend', 'friendship', 'bond', 'companionship', 'ally', 'camaraderie'],
    'betrayal': ['betray', 'betrayal', 'traitor', 'deception', 'deceive', 'treachery'],
    'heroism': ['hero', 'heroic', 'heroism', 'brave', 'courage', 'valiant', 'savior'],
    'sacrifice': ['sacrifice', 'sacrificial', 'give up', 'offer', 'martyr'],
    'good_vs_evil': ['good', 'evil', 'light', 'dark', 'moral', 'immoral', 'right', 'wrong'],
    'power_struggle': ['power', 'control', 'authority', 'domination', 'ruler', 'leadership', 'throne'],
    'conspiracy': ['conspiracy', 'plot', 'scheme', 'cover up', 'corruption', 'secret'],
    'dystopia': ['dystopia', 'dystopian', 'oppression', 'totalitarian', 'dictatorship', 'rebellion'],
    'supernatural': ['supernatural', 'paranormal', 'ghost', 'spirit', 'haunting', 'afterlife', 'possession'],
    'journey': ['journey', 'quest', 'adventure', 'expedition', 'voyage', 'pilgrimage'],
    'identity': ['identity', 'self-discovery', 'who am i', 'origin', 'true self', 'real self']
}

TONE_KEYWORDS = {
    'dark': ['dark', 'gritty', 'noir', 'bleak', 'grim', 'somber', 'disturbing', 'macabre', 'sinister'],
    'light': ['light', 'upbeat', 'cheerful', 'bright', 'jovial', 'happy', 'positive', 'uplifting'],
    'comedic': ['comedy', 'comedic', 'funny', 'hilarious', 'humor', 'amusing', 'laugh', 'slapstick'],
    'serious': ['serious', 'dramatic', 'grave', 'solemn', 'intense', 'heavy', 'profound', 'thoughtful'],
    'emotional': ['emotional', 'moving', 'touching', 'heartfelt', 'stirring', 'poignant', 'tear'],
    'inspirational': ['inspiration', 'inspirational', 'motivating', 'uplifting', 'encouraging'],
    'suspenseful': ['suspense', 'suspenseful', 'tension', 'thrilling', 'edge-of-seat', 'nail-biting'],
    'action_packed': ['action', 'fast-paced', 'explosive', 'thrilling', 'adrenaline', 'exciting', 'stunt'],
    'romantic': ['romantic', 'love', 'passion', 'intimate', 'affair', 'loving', 'tender']
}

TARGET_AUDIENCE = {
    'family': ['family', 'children', 'kid', 'child', 'all ages', 'family-friendly', 'wholesome', 'young'],
    'teen': ['teen', 'teenage', 'adolescent', 'young adult', 'youth', 'coming of age'],
    'adult': ['adult', 'mature', 'grown-up', 'explicit', 'violence', 'nude', 'sexual'],
    'general': ['everyone', 'universal', 'general audience', 'all audiences']
}

FRANCHISES = {
    'mcu': ['marvel', 'avengers', 'thor', 'iron man', 'hulk', 'captain america', 'black widow', 'guardians of the galaxy', 'ant-man', 'spider-man', 'doctor strange', 'black panther', 'captain marvel', 'thanos', 'wakanda', 'infinity stone', 'loki', 'scarlet witch', 'falcon', 'winter soldier', 'shang-chi', 'eternals'],
    'dceu': ['dc', 'batman', 'superman', 'wonder woman', 'justice league', 'aquaman', 'flash', 'cyborg', 'green lantern', 'gotham', 'metropolis', 'krypton', 'joker', 'suicide squad', 'birds of prey', 'black adam', 'shazam'],
    'star_wars': ['star wars', 'jedi', 'sith', 'force', 'lightsaber', 'darth', 'skywalker', 'rebellion', 'empire', 'droid', 'yoda', 'millennium falcon', 'tatooine', 'death star', 'clone wars', 'mandalorian', 'grogu', 'obi-wan', 'palpatine'],
    'harry_potter': ['harry potter', 'hogwarts', 'wizard', 'witchcraft', 'magic', 'wand', 'spell', 'voldemort', 'dumbledore', 'hermione', 'ron', 'snape', 'muggle', 'quidditch', 'hagrids', 'fantastic beasts', 'platform 9 3/4'],
    'lord_of_the_rings': ['lord of the rings', 'hobbit', 'middle earth', 'tolkien', 'gandalf', 'frodo', 'sauron', 'aragorn', 'mordor', 'gollum', 'ring', 'shire', 'elves', 'dwarves', 'orcs', 'rivendell', 'isengard'],
    'fast_and_furious': ['fast and furious', 'fast & furious', 'dom toretto', 'street racing', 'heist', 'family', 'cars', 'high-speed', 'brian o\'conner'],
    'jurassic_park': ['jurassic', 'dinosaur', 'isla nublar', 'tyrannosaurus', 'velociraptor', 'dna', 'theme park', 'fossil', 'ingen', 'paleontology', 'chaos theory', 'jeff goldblum'],
    'transformers': ['transformers', 'autobot', 'decepticon', 'cybertron', 'megatron', 'optimus prime', 'bumblebee', 'allspark', 'bayverse'],
    'mission_impossible': ['mission impossible', 'ethan hunt', 'imf', 'agent', 'espionage', 'tom cruise', 'gadgets', 'stunts', 'secret mission'],
    'james_bond': ['james bond', '007', 'secret agent', 'mi6', 'spy', 'gadgets', 'villains', 'exotic locations', 'shaken not stirred'],
    'alien': ['alien', 'xenomorph', 'space horror', 'ridley scott', 'sigourney weaver', 'nostromo', 'facehugger', 'chestburster'],
    'predator': ['predator', 'hunter', 'jungle', 'arnold schwarzenegger', 'stealth', 'alien hunter', 'heat vision'],
    'terminator': ['terminator', 'cyborg', 'time travel', 'skynet', 'sarah connor', 'artificial intelligence', 'judgment day', 'hasta la vista'],
    'matrix': ['matrix', 'neo', 'trinity', 'morpheus', 'simulation', 'red pill', 'blue pill', 'kung fu', 'bullet time'],
    'pirates_of_the_caribbean': ['pirates of the caribbean', 'jack sparrow', 'pirate', 'sea', 'treasure', 'black pearl', 'cursed', 'disney'],
    'ghostbusters': ['ghostbusters', 'ghost', 'paranormal', 'new york', 'proton pack', 'ecto-1', 'bill murray', 'dan aykroyd'],
    'indiana_jones': ['indiana jones', 'archaeologist', 'adventure', 'artifact', 'nazis', 'whip', 'fedora', 'harrison ford'],
    'back_to_the_future': ['back to the future', 'time travel', 'delorean', 'doc brown', 'marty mcfly', '1.21 gigawatts', 'hill valley'],
    'john_wick': ['john wick', 'hitman', 'assassin', 'continental hotel', 'keanu reeves', 'gun fu', 'revenge', 'dog'],
    'the_conjuring_universe': ['conjuring', 'annabelle', 'nun', 'paranormal investigation', 'haunted', 'demonic', 'warrens'],
    'saw': ['saw', 'jigsaw', 'trap', 'horror', 'gore', 'game', 'billy the puppet'],
    'resident_evil': ['resident evil', 'zombie', 'biohazard', 'umbrella corporation', 'raccoon city', 'milla jovovich', 't-virus'],
    'mad_max': ['mad max', 'post-apocalyptic', 'desert', 'vehicles', 'mel gibson', 'tom hardy', 'water wars', 'fury road'],
    'kung_fu_panda': ['kung fu panda', 'po', 'dragon warrior', 'kung fu', 'china', 'master shifu', 'furious five', 'dreamworks'],
    'how_to_train_your_dragon': ['how to train your dragon', 'hiccup', 'toothless', 'dragon', 'vikings', 'berk', 'dreamworks'],
    'shrek': ['shrek', 'ogre', 'donkey', 'princess fiona', 'far far away', 'dreamworks'],
    'toy_story': ['toy story', 'woody', 'buzz lightyear', 'andy', 'toys', 'pixar'],
    'despicable_me': ['despicable me', 'gru', 'minions', 'agnes', 'vector', 'illumination'],
    'ice_age': ['ice age', 'manny', 'sid', 'diego', 'scrat', 'mammoth', 'sloth', 'saber-tooth tiger', 'blue sky studios'],
    'the_hunger_games': ['hunger games', 'katniss everdeen', 'panem', 'districts', 'capitol', 'mockingjay', 'survival'],
    'divergent': ['divergent', 'tris prior', 'factions', 'chicago', 'dauntless', 'abnegation', 'insurgent'],
    'maze_runner': ['maze runner', 'thomas', 'glade', 'maze', 'grievers', 'wicked'],
    'avatar': ['avatar', 'pandora', 'navi', 'unobtanium', 'james cameron', 'flying creatures', 'tree of souls'],
    'planet_of_the_apes': ['planet of the apes', 'ape', 'human', 'caesar', 'simian flu', 'evolution', 'post-apocalyptic'],
    'godzilla': ['godzilla', 'kaiju', 'monster', 'tokyo', 'atomic breath', 'mothra', 'king ghidorah'],
    'king_kong': ['king kong', 'giant ape', 'skull island', 'new york', 'ann darrow'],
    'transformers_animated': ['transformers animated', 'optimus prime', 'bumblebee', 'bulkhead', 'prowl', 'ratchet', 'cybertron', 'earth', 'decepticons'],
    'teenage_mutant_ninja_turtles': ['teenage mutant ninja turtles', 'tmnt', 'leonardo', 'donatello', 'michelangelo', 'raphael', 'splinter', 'shredder', 'pizza', 'new york city'],
    'ghost_in_the_shell': ['ghost in the shell', 'motoko kusanagi', 'cyberpunk', 'section 9', 'cyberbrain', 'stand alone complex', 'anime'],
    'evangelion': ['evangelion', 'eva', 'shinji ikari', 'rei ayanami', 'asuka langley soryu', 'angels', 'nerv', 'apocalyptic', 'anime'],
    'gundam': ['gundam', 'mobile suit', 'amuro ray', 'char aznable', 'space opera', 'mecha', 'newtype', 'anime'],
    'star_trek': ['star trek', 'enterprise', 'kirk', 'spock', 'federation', 'vulcan', 'klingon', 'warp drive', 'beam me up'],
    'battlestar_galactica': ['battlestar galactica', 'cylons', 'colonial fleet', 'starbuck', 'apollo', 'so say we all', 'space opera'],
    'stargate': ['stargate', 'sg-1', 'daniel jackson', 'jack o\'neill', 'goa\'uld', 'ancient', 'wormhole', 'chevron'],
    'doctor_who': ['doctor who', 'the doctor', 'tardis', 'daleks', 'cybermen', 'sonic screwdriver', 'time lord', 'gallifrey'],
    'sherlock_holmes': ['sherlock holmes', 'detective', 'baker street', 'watson', 'mystery', 'deduction', 'arthur conan doyle'],
    'the_godfather': ['godfather', 'corleone', 'mafia', 'new york', 'crime family', 'don vito', 'michael corleone'],
    'pulp_fiction': ['pulp fiction', 'tarantino', 'crime', 'los angeles', 'non-linear', 'jules winnfield', 'vincent vega'],
    'starship_troopers': ['starship troopers', 'bugs', 'mobile infantry', 'federation', 'arachnids', 'paul verhoeven', 'space war'],
    'total_recall': ['total recall', 'mars', 'douglas quaid', 'memory implant', 'resistance', 'arnold schwarzenegger', 'science fiction'],
    'robocop': ['robocop', 'alex murphy', 'detroit', 'omni consumer products', 'cybernetic', 'crime', 'paul verhoeven'],
    'blade_runner': ['blade runner', 'rick deckard', 'replicant', 'los angeles', 'cyberpunk', 'philip k. dick', 'artificial intelligence'],
    'dune': ['dune', 'paul atreides', 'arrakis', 'spice', 'sandworms', 'fremen', 'house atreides', 'emperor'],
    'game_of_thrones': ['game of thrones', 'westeros', 'dragons', 'stark', 'lannister', 'winter is coming', 'iron throne', 'hbo'],
    'the_witcher': ['witcher', 'geralt of rivia', 'monsters', 'magic', 'ciri', 'yennefer', 'continent', 'netflix'],
    'the_expanse': ['expanse', 'rocinante', 'mars', 'earth', 'belt', 'protomolecule', 'james holden', 'space opera'],
    'foundation': ['foundation', 'hari seldon', 'psychohistory', 'galactic empire', 'apple tv+'],
    'westworld': ['westworld', 'host', 'guest', 'theme park', 'artificial intelligence', 'delos', 'hbo'],
    'black_mirror': ['black mirror', 'technology', 'dystopian', 'anthology', 'future', 'social commentary', 'netflix'],
    'the_twilight_zone': ['twilight zone', 'rod serling', 'science fiction', 'horror', 'anthology', 'unexplained', 'dimension'],
    'the_x_files': ['x-files', 'mulder', 'scully', 'aliens', 'conspiracy', 'paranormal', 'fbi', 'truth is out there'],
    'stranger_things': ['stranger things', 'hawkins', 'upside down', 'eleven', 'demogorgon', '80s', 'netflix'],
    'the_walking_dead': ['walking dead', 'zombies', 'apocalypse', 'rick grimes', 'survival', 'amc'],
    'breaking_bad': ['breaking bad', 'walter white', 'jesse pinkman', 'meth', 'albuquerque', 'crime drama', 'amc'],
    'better_call_saul': ['better call saul', 'saul goodman', 'jimmy mcgill', 'breaking bad universe', 'prequel', 'amc'],
    'the_sopranos': ['sopranos', 'tony soprano', 'mafia', 'new jersey', 'crime drama', 'hbo'],
    'the_wire': ['the wire', 'baltimore', 'drugs', 'police', 'social issues', 'hbo'],
    'seinfeld': ['seinfeld', 'jerry seinfeld', 'new york', 'sitcom', 'show about nothing', 'nineties'],
    'friends': ['friends', 'new york', 'sitcom', 'central perk', 'six friends', 'nineties'],
    'the_office_us': ['the office', 'dwight schrute', 'michael scott', 'dunder mifflin', 'scranton', 'mockumentary', 'comedy'],
    'parks_and_recreation': ['parks and recreation', 'leslie knope', 'pawnee', 'government', 'mockumentary', 'comedy'],
    'the_simpsons': ['simpsons', 'springfield', 'homer', 'marge', 'bart', 'lisa', 'cartoon', 'fox'],
    'south_park': ['south park', 'cartman', 'stan', 'kyle', 'kenny', 'cartoon', 'comedy central'],
    'family_guy': ['family guy', 'peter griffin', 'stewie', 'brian', 'cartoon', 'fox'],
    'futurama': ['futurama', 'fry', 'bender', 'leela', 'planet express', 'cartoon', 'science fiction'],
    'rick_and_morty': ['rick and morty', 'rick sanchez', 'morty smith', 'interdimensional', 'adult swim', 'cartoon', 'science fiction'],
    'spongebob_squarepants': ['spongebob', 'bikini bottom', 'patrick', 'squidward', 'krusty krab', 'nickelodeon', 'cartoon'],
    'pokemon': ['pokemon', 'pikachu', 'ash ketchum', 'trainer', 'pocket monsters', 'anime', 'game freak'],
    'studio_ghibli': ['studio ghibli', 'miyazaki', 'spirited away', 'my neighbor totoro', 'princess mononoke', 'anime', 'japan'],
    'star_trek_animated': ['star trek animated', 'kirk', 'spock', 'mccoy', 'enterprise', 'cartoon', 'science fiction'],
    'he-man_and_the_masters_of_the_universe': ['he-man', 'skeletor', 'eternia', 'castle grayskull', 'by the power of grayskull', 'cartoon', '80s'],
    'transformers_generation_1': ['transformers g1', 'optimus prime', 'megatron', 'cybertron', 'autobots', 'decepticons', 'cartoon', '80s'],
    'gi_joe_a_real_american_hero': ['gi joe', 'cobra', 'duke', 'snake eyes', 'a real american hero', 'cartoon', '80s'],
    'thundercats': ['thundercats', 'liono', 'mumm-ra', 'third earth', 'thunder cats ho!', 'cartoon', '80s'],
    'voltron_defender_of_the_universe': ['voltron', 'lions', 'go lions!', 'defender of the universe', 'cartoon', '80s'],
    'robotech': ['robotech', 'rick hunter', 'lisa hayes', 'macross', 'zentraedi', 'mecha', 'anime', '80s'],
    'captain_tsubasa': ['captain tsubasa', 'soccer', 'tsubasa ozora', 'anime', 'sports'],
    'dragon_ball': ['dragon ball', 'goku', 'vegeta', 'saiyan', 'kamehameha', 'anime', 'shonen'],
    'one_piece': ['one piece', 'luffy', 'straw hat pirates', 'grand line', 'devil fruit', 'anime', 'shonen'],
    'naruto': ['naruto', 'uzumaki', 'ninja', 'konoha', 'jutsu', 'anime', 'shonen'],
    'attack_on_titan': ['attack on titan', 'eren yeager', 'titans', 'walls', 'survey corps', 'anime', 'dark fantasy'],
    'death_note': ['death note', 'light yagami', 'ryuk', 'shinigami', 'anime', 'psychological thriller'],
    'sword_art_online': ['sword art online', 'kirito', 'asuna', 'virtual reality', 'mmorpg', 'anime', 'isekai'],
    'my_hero_academia': ['my hero academia', 'izuku midoriya', 'all might', 'quirks', 'ua high', 'anime', 'superhero'],
    'jojo_s_bizarre_adventure': ['jojo\'s bizarre adventure', 'jojo', 'stands', 'hamon', 'anime', 'shonen'],
    'demon_slayer': ['demon slayer', 'tanjiro kamado', 'demons', 'demon slayer corps', 'anime', 'dark fantasy'],
    'spy_x_family': ['spy x family', 'loid forger', 'anya forger', 'yor forger', 'spy', 'assassin', 'telepath', 'anime'],
    'attack_on_titan': ['attack on titan', 'eren yeager', 'titans', 'walls', 'survey corps', 'anime', 'dark fantasy'],
    'death_note': ['death note', 'light yagami', 'ryuk', 'shinigami', 'anime', 'psychological thriller'],
    'sword_art_online': ['sword art online', 'kirito', 'asuna', 'virtual reality', 'mmorpg', 'anime', 'isekai'],
    'my_hero_academia': ['my hero academia', 'izuku midoriya', 'all might', 'quirks', 'ua high', 'anime', 'superhero'],
    'jojo_s_bizarre_adventure': ['jojo\'s bizarre adventure', 'jojo', 'stands', 'hamon', 'anime', 'shonen'],
    'demon_slayer': ['demon slayer', 'tanjiro kamado', 'demons', 'demon slayer corps', 'anime', 'dark fantasy'],
    'spy_x_family': ['spy x family', 'loid forger', 'anya forger', 'yor forger', 'spy', 'assassin', 'telepath', 'anime', 'comedy'],
    'fullmetal_alchemist': ['fullmetal alchemist', 'edward elric', 'alphonse elric', 'alchemy', 'automail', 'anime', 'fantasy'],
    'steins_gate': ['steins;gate', 'rintaro okabe', 'time travel', 'world lines', 'anime', 'science fiction', 'thriller'],
    'code_geass': ['code geass', 'lelouch lamperouge', 'geass', 'britannia', 'black knights', 'mecha', 'anime', 'alternate history'],
    'cowboy_bebop': ['cowboy bebop', 'spike spiegel', 'space bounty hunter', 'bebop', 'jazz', 'anime', 'space western'],
    'neon_genesis_evangelion': ['neon genesis evangelion', 'shinji ikari', 'eva', 'angels', 'nerv', 'apocalyptic', 'anime', 'mecha'],
    'princess_mononoke': ['princess mononoke', 'ashitaka', 'san', 'forest spirit', 'nature vs humanity', 'studio ghibli', 'anime'],
    'spirited_away': ['spirited away', 'chihiro', 'yubaba', 'spirit world', 'bathhouse', 'studio ghibli', 'anime'],
    'howl_s_moving_castle': ['howl\'s moving castle', 'sophie', 'howl', 'moving castle', 'magic', 'studio ghibli', 'anime'],
    'my_neighbor_totoro': ['my neighbor totoro', 'satsuki', 'mei', 'totoro', 'forest spirit', 'studio ghibli', 'anime'],
    'kiki_s_delivery_service': ['kiki\'s delivery service', 'kiki', 'jiji', 'witch', 'flying', 'studio ghibli', 'anime'],
    'grave_of_the_fireflies': ['grave of the fireflies', 'seita', 'setsuko', 'world war ii', 'loss', 'studio ghibli', 'anime', 'drama'],
    'the_wind_rises': ['the wind rises', 'jiro horikoshi', 'airplane designer', 'world war ii', 'studio ghibli', 'anime', 'biographical'],
    'ponyo': ['ponyo', 'sosuke', 'fish princess', 'ocean', 'magic', 'studio ghibli', 'anime'],
    'arrietty': ['arrietty', 'borrowers', 'shawn', 'tiny people', 'house', 'studio ghibli', 'anime'],
    'from_up_on_poppy_hill': ['from up on poppy hill', 'umi', 'shun', 'school', 'yokohama', 'studio ghibli', 'anime', 'romance'],
    'the_tale_of_the_princess_kaguya': ['tale of the princess kaguya', 'bamboo cutter', 'moon princess', 'studio ghibli', 'anime', 'folktale'],
    'when_marnie_was_there': ['when marnie was there', 'anna', 'marnie', 'friendship', 'secrets', 'studio ghibli', 'anime'],
    'whisper_of_the_heart': ['whisper of the heart', 'shizuku', 'seiji', 'dreams', 'library', 'studio ghibli', 'anime', 'romance'],
    'the_cat_returns': ['the cat returns', 'haru', 'cat kingdom', 'baron', 'toto', 'studio ghibli', 'anime', 'fantasy'],
    'tales_from_earthsea': ['tales from earthsea', 'arren', 'ged', 'dragons', 'magic', 'studio ghibli', 'anime', 'fantasy'],
    'ocean_waves': ['ocean waves', 'taku', 'rikako', 'high school', 'romance', 'studio ghibli', 'anime'],
    'my_neighbors_the_yamadas': ['my neighbors the yamadas', 'yamada family', 'everyday life', 'comedy', 'studio ghibli', 'anime'],
    'porco_rosso': ['porco rosso', 'marco pagot', 'pig pilot', 'adriatic sea', 'world war i', 'studio ghibli', 'anime', 'adventure'],
    'only_yesterday': ['only yesterday', 'taeko', 'childhood memories', 'countryside', 'studio ghibli', 'anime', 'drama'],
    'pom_poko': ['pom poko', 'tanuki', 'raccoon dogs', 'nature', 'urbanization', 'studio ghibli', 'anime', 'comedy'],
    'the_secret_world_of_arrietty': ['secret world of arrietty', 'arrietty', 'shawn', 'borrowers', 'tiny people', 'house', 'studio ghibli', 'anime'],
    'earwig_and_the_witch': ['earwig and the witch', 'earwig', 'bella yaga', 'magic', 'studio ghibli', 'anime'],
    'ronja_the_robber_s_daughter': ['ronja the robber\'s daughter', 'ronja', 'birk', 'forest', 'robbers', 'studio ghibli', 'anime', 'fantasy'],
    'aya_and_the_witch': ['aya and the witch', 'aya', 'bella yaga', 'magic', 'studio ghibli', 'anime'],
    'spirited_away_2': ['spirited away 2', 'chihiro', 'yubaba', 'spirit world', 'bathhouse', 'studio ghibli', 'anime', 'sequel'],
    'princess_mononoke_2': ['princess mononoke 2', 'ashitaka', 'san', 'forest spirit', 'nature vs humanity', 'studio ghibli', 'anime', 'sequel'],
    'my_neighbor_totoro_2': ['my neighbor totoro 2', 'satsuki', 'mei', 'totoro', 'forest spirit', 'studio ghibli', 'anime', 'sequel'],
    'kiki_s_delivery_service_2': ['kiki\'s delivery service 2', 'kiki', 'jiji', 'witch', 'flying', 'studio ghibli', 'anime', 'sequel'],
    'howl_s_moving_castle_2': ['howl\'s moving castle 2', 'sophie', 'howl', 'moving castle', 'magic', 'studio ghibli', 'anime', 'sequel'],
    'ponyo_2': ['ponyo 2', 'sosuke', 'fish princess', 'ocean', 'magic', 'studio ghibli', 'anime', 'sequel'],
    'arrietty_2': ['arrietty 2', 'borrowers', 'shawn', 'tiny people', 'house', 'studio ghibli', 'anime', 'sequel'],
    'from_up_on_poppy_hill_2': ['from up on poppy hill 2', 'umi', 'shun', 'school', 'yokohama', 'studio ghibli', 'anime', 'romance', 'sequel'],
    'the_tale_of_the_princess_kaguya_2': ['tale of the princess kaguya 2', 'bamboo cutter', 'moon princess', 'studio ghibli', 'anime', 'folktale', 'sequel'],
    'when_marnie_was_there_2': ['when marnie was there 2', 'anna', 'marnie', 'friendship', 'secrets', 'studio ghibli', 'anime', 'sequel'],
    'whisper_of_the_heart_2': ['whisper of the heart 2', 'shizuku', 'seiji', 'dreams', 'library', 'studio ghibli', 'anime', 'romance', 'sequel'],
    'the_cat_returns_2': ['the cat returns 2', 'haru', 'cat kingdom', 'baron', 'toto', 'studio ghibli', 'anime', 'fantasy', 'sequel'],
    'tales_from_earthsea_2': ['tales from earthsea 2', 'arren', 'ged', 'dragons', 'magic', 'studio ghibli', 'anime', 'fantasy', 'sequel'],
    'ocean_waves_2': ['ocean waves 2', 'taku', 'rikako', 'high school', 'romance', 'studio ghibli', 'anime', 'sequel'],
    'my_neighbors_the_yamadas_2': ['my neighbors the yamadas 2', 'yamada family', 'everyday life', 'comedy', 'studio ghibli', 'anime', 'sequel'],
    'porco_rosso_2': ['porco rosso 2', 'marco pagot', 'pig pilot', 'adriatic sea', 'world war i', 'studio ghibli', 'anime', 'adventure', 'sequel'],
    'only_yesterday_2': ['only yesterday 2', 'taeko', 'childhood memories', 'countryside', 'studio ghibli', 'anime', 'drama', 'sequel'],
    'pom_poko_2': ['pom poko 2', 'tanuki', 'raccoon dogs', 'nature', 'urbanization', 'studio ghibli', 'anime', 'comedy', 'sequel'],
    'the_secret_world_of_arrietty_2': ['secret world of arrietty 2', 'arrietty', 'shawn', 'borrowers', 'tiny people', 'house', 'studio ghibli', 'anime', 'sequel'],
    'earwig_and_the_witch_2': ['earwig and the witch 2', 'earwig', 'bella yaga', 'magic', 'studio ghibli', 'anime', 'sequel'],
    'ronja_the_robber_s_daughter_2': ['ronja the robber\'s daughter 2', 'ronja', 'birk', 'forest', 'robbers', 'studio ghibli', 'anime', 'fantasy', 'sequel'],
    'aya_and_the_witch_2': ['aya and the witch 2', 'aya', 'bella yaga', 'magic', 'studio ghibli', 'anime', 'sequel'],
    'disney': ['disney', 'classic animation', 'princess', 'mouse', 'magic kingdom', 'animated musical', 'fairytale', 'pixar'],
    'pixar': ['pixar', 'cgi animation', 'dreamworks', 'illumination', 'blue sky studios'],
    'lego_movie': ['lego movie', 'everything is awesome', 'master builder', 'bricksburg', 'emmet', 'wyldstyle', 'batman lego'],
    'frozen': ['frozen', 'elsa', 'anna', 'olaf', 'arendelle', 'let it go', 'snow queen'],
    'moana': ['moana', 'ocean', 'heihei', 'maui', 'south pacific', 'voyage'],
    'tangled': ['tangled', 'rapunzel', 'flynn rider', 'lanterns', 'tower', 'healing hair'],
    'the_lion_king': ['lion king', 'simba', 'nala', 'mufasa', 'hakuna matata', 'pride rock', 'savanna'],
    'beauty_and_the_beast': ['beauty and the beast', 'belle', 'beast', 'enchanted castle', 'tale as old as time'],
    'aladdin': ['aladdin', 'genie', 'jasmine', 'agrabah', 'magic carpet', 'three wishes'],
    'the_little_mermaid': ['little mermaid', 'ariel', 'sebastian', 'flounder', 'under the sea', 'ursula'],
    'cinderella': ['cinderella', 'fairy godmother', 'glass slipper', 'prince charming', 'pumpkin carriage'],
    'sleeping_beauty': ['sleeping beauty', 'aurora', 'maleficent', 'briar rose', 'spinning wheel'],
    'snow_white': ['snow white', 'seven dwarfs', 'poison apple', 'evil queen', 'fairest of them all'],
    'mulan': ['mulan', 'mushu', 'china', 'warrior', 'dishonor on your cow'],
    'pocahontas': ['pocahontas', 'john smith', 'jamestown', 'wind and the trees'],
    'the_hunchback_of_notre_dame': ['hunchback of notre dame', 'quasimodo', 'esmeralda', 'notre dame', 'frollo'],
    'hercules': ['hercules', 'hades', 'megara', 'olympus', 'zero to hero'],
    'tarzan': ['tarzan', 'jane', 'jungle', 'gorilla', 'phil collins'],
    'lilo_and_stitch': ['lilo and stitch', 'stitch', 'ohana', 'hawaii', 'experiment 626'],
    'fantasia': ['fantasia', 'mickey mouse', 'sorcerer\'s apprentice', 'classical music', 'animation'],
    'pinocchio': ['pinocchio', 'geppetto', 'jiminy cricket', 'wooden puppet', 'whale'],
    'dumbo': ['dumbo', 'flying elephant', 'timothy q. mouse', 'circus', 'big ears'],
    'bambi': ['bambi', 'thumper', 'flower', 'forest', 'mother\'s death'],
    'peter_pan': ['peter pan', 'wendy', 'tinkerbell', 'neverland', 'captain hook', 'lost boys'],
    'alice_in_wonderland': ['alice in wonderland', 'mad hatter', 'cheshire cat', 'wonderland', 'tea party'],
    'the_jungle_book': ['jungle book', 'mowgli', 'baloo', 'bagheera', 'shere khan', 'jungle'],
    'robin_hood_disney': ['robin hood', 'disney animals', 'nottingham', 'sheriff'],
    'the_aristocats': ['aristocats', 'duchess', 'thomas o\'malley', 'paris', 'jazz cat'],
    '101_dalmatians': ['101 dalmatians', 'pongo', 'perdita', 'cruella de vil', 'puppies'],
    'sleeping_beauty': ['sleeping beauty', 'aurora', 'maleficent', 'briar rose', 'spinning wheel'],
    'the_sword_in_the_stone': ['sword in the stone', 'wart', 'merlin', 'magic', 'arthur'],
    'oliver_and_company': ['oliver and company', 'oliver', 'dodger', 'fagin', 'new york city dogs'],
    'the_great_mouse_detective': ['great mouse detective', 'basil', 'dawson', 'ratigan', 'mouse london'],
    'the_rescuers': ['rescuers', 'bernard', 'bianca', 'penny', 'swamp'],
    'the_fox_and_the_hound': ['fox and the hound', 'tod', 'copper', 'friendship', 'forest'],
    'cars': ['cars', 'lightning mcqueen', 'mater', 'radiator springs', 'racing'],
    'finding_nemo': ['finding nemo', 'nemo', 'marlin', 'dory', 'ocean', 'great barrier reef'],
'the_incredibles': ['incredibles', 'mr incredible', 'elastigirl', 'violet', 'dash', 'superhero family'],
'monsters_inc': ['monsters inc', 'sully', 'mike wazowski', 'boo', 'monstropolis', 'scaring'],
'up': ['up', 'carl fredricksen', 'russell', 'balloons', 'south america', 'adventure'],
'ratatouille': ['ratatouille', 'remy', 'linguini', 'paris', 'cooking', 'restaurant'],
'wall-e': ['wall-e', 'eve', 'robot', 'space', 'earth', 'pollution'],
'brave': ['brave', 'merida', 'scotland', 'archery', 'bear', 'magic'],
'inside_out': ['inside out', 'joy', 'sadness', 'anger', 'fear', 'disgust', 'emotions'],
'coco': ['coco', 'miguel', 'land of the dead', 'day of the dead', 'music', 'family'],
'onward': ['onward', 'ian', 'barley', 'elf brothers', 'magic', 'quest'],
'soul': ['soul', 'joe gardner', '22', 'great before', 'jazz', 'afterlife'],
'luca': ['luca', 'alberto', 'sea monster', 'italian riviera', 'friendship', 'gelato'],
'turning_red': ['turning red', 'mei', 'red panda', 'toronto', 'puberty', 'girlhood'],
'elemental': ['elemental', 'ember', 'wade', 'element city', 'fire', 'water'],
'toystory': ['toy story', 'woody', 'buzz lightyear', 'andy', 'toys', 'space ranger', 'sheriff'], 
'a_bug_s_life': ['a bug\'s life', 'flik', 'atta', 'ants', 'grasshoppers', 'circus'],
'monsters_university': ['monsters university', 'sully', 'mike wazowski', 'college', 'scaring school'],
'finding_dory': ['finding dory', 'dory', 'nemo', 'marlin', 'ocean', 'memory loss'],
'cars_2': ['cars 2', 'lightning mcqueen', 'mater', 'spy', 'world grand prix'],
'cars_3': ['cars 3', 'lightning mcqueen', 'cruise ramirez', 'racing', 'next-gen racers'],
'the_incredibles_2': ['incredibles 2', 'elastigirl', 'mr incredible', 'violet', 'dash', 'jack-jack', 'superhero family'],
'walle': ['wall-e', 'eve', 'robot', 'space', 'earth', 'pollution'],
'ratatouille': ['ratatouille', 'remy', 'linguini', 'paris', 'cooking', 'restaurant'], 
'brave': ['brave', 'merida', 'scotland', 'archery', 'bear', 'magic'], 
'insideout': ['inside out', 'joy', 'sadness', 'anger', 'fear', 'disgust', 'emotions'], 
'coco': ['coco', 'miguel', 'land of the dead', 'day of the dead', 'music', 'family'], 
'onward': ['onward', 'ian', 'barley', 'elf brothers', 'magic', 'quest'], 
'soul': ['soul', 'joe gardner', '22', 'great before', 'jazz', 'afterlife'], 
'luca': ['luca', 'alberto', 'sea monster', 'italian riviera', 'friendship', 'gelato'], 
'turningred': ['turning red', 'mei', 'red panda', 'toronto', 'puberty', 'girlhood'], 
'elemental': ['elemental', 'ember', 'wade', 'element city', 'fire', 'water'], 
}

def fetch_genre_mapping():
    """ Fetch the mapping of genre IDs to names from TMDB """
    url = f"https://api.themoviedb.org/3/genre/movie/list?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    genre_dict = {}
    
    if response.status_code == 200:
        genres = response.json().get("genres", [])
        for genre in genres:
            genre_id = genre["id"]
            genre_name = genre["name"]
            genre_dict[genre_id] = genre_name
        return genre_dict
    else:
        print("Failed to fetch genre mapping")
        return {}

def get_actors(movie_id):
    """ Get the top 5 cast members for a movie """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    actors = []

    if response.status_code == 200:
        credits = response.json()
        cast_list = credits.get("cast", [])[:5]  
        for cast_member in cast_list:
            actor_name = cast_member["name"]
            actors.append(actor_name)
        return actors
    return []

def get_director(movie_id):
    """ Get the directors of a movie """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    directors = []

    if response.status_code == 200:
        credits = response.json()
        crew = credits.get("crew", [])
        for crew_member in crew:
            if crew_member.get("job") == "Director":
                directors.append(crew_member.get("name"))
        return directors
    return []

def fetch_movie_details(movie_id):
    """ Fetch detailed information about a movie """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=en-US&append_to_response=release_dates,content_ratings"
    response = requests.get(url)
    genre_list = []

    if response.status_code == 200:
        data = response.json()
        for genre in data.get("genres", []):
            genre_name = genre["name"]
            genre_list.append(genre_name)
            
        # Get content rating 
        content_rating = "Not Rated"
        release_dates = data.get("release_dates", {}).get("results", [])
        for country in release_dates:
            if country.get("iso_3166_1") == "US": 
                for release in country.get("release_dates", []):
                    if release.get("certification"):
                        content_rating = release.get("certification")
                        break
                break
        
        return {
            "title": data.get("title", ""),
            "original_title": data.get("original_title", ""),
            "overview": data.get("overview", ""),
            "poster_path": data.get("poster_path", ""),
            "backdrop_path": data.get("backdrop_path", ""),
            "release_date": data.get("release_date", ""),
            "vote_average": data.get("vote_average", 0),
            "vote_count": data.get("vote_count", 0),
            "runtime": data.get("runtime", 0),
            "budget": data.get("budget", 0),
            "revenue": data.get("revenue", 0),
            "popularity": data.get("popularity", 0),
            "adult": data.get("adult", False),
            "content_rating": content_rating,
            "genres": genre_list,
            "original_language": data.get("original_language", ""),
            "production_companies": [company.get("name") for company in data.get("production_companies", [])],
            "production_countries": [country.get("name") for country in data.get("production_countries", [])]
        }
    else:
        print(f"Failed to retrieve data for {movie_id}")
        return None    

def fetch_keywords_for_movies(movie_id):
    """ Fetch keywords for a movie """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords?api_key={TMDB_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        return {
            "keywords": [keyword["name"] for keyword in data.get("keywords", [])]
        }
    else:
        print(f"Failed to retrieve keywords for {movie_id}")
        return {"keywords": []}

def preprocess_text(text):
    """ Clean and preprocess text for analysis """
    if not text:
        return []
    
    try:
        # Lowercase and remove punctuation
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Tokenize
        try:
            tokens = word_tokenize(text)
        except Exception as e:
            print(f"Tokenization failed: {e}, using fallback")
            tokens = simple_tokenize(text)
        
        # Get stopwords
        try:
            stop_words = set(stopwords.words('english'))
        except Exception as e:
            print(f"Stopwords retrieval failed: {e}, using fallback")
            stop_words = SimpleStopwords().words('english')
        
        # Lemmatize and filter
        filtered_tokens = []
        for word in tokens:
            if word not in stop_words and len(word) > 2:
                try:
                    if isinstance(WordNetLemmatizer, SimpleLemmatizer):
                        lemma = WordNetLemmatizer.lemmatize(word)
                    else:
                        lemma = WordNetLemmatizer.lemmatize(word)
                    filtered_tokens.append(lemma)
                except Exception as e:
                    print(f"Lemmatization failed: {e}, using word as is")
                    filtered_tokens.append(word)
        return filtered_tokens
    except Exception as e:
        print(f"Text preprocessing failed completely: {e}")
        return [w for w in text.lower().split() if len(w) > 2]

def identify_themes(text):
    """ Identify major themes in a movie's description """
    if not text:
        return []
    
    text = text.lower()
    themes = []
    
    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                themes.append(theme)
                break
    
    return themes

def identify_tone(text):
    """ Identify the tone of a movie's description """
    if not text:
        return []
    
    text = text.lower()
    tones = []
    
    for tone, keywords in TONE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                tones.append(tone)
                break
    
    return tones

def identify_target_audience(movie_details):
    "" "Determine the target audience based on movie details """
    if not movie_details:
        return "general"
    
    # Get text to analyse
    text = f"{movie_details.get('title', '')} {movie_details.get('overview', '')}"
    text = text.lower()
    
    # Check content rating first 
    content_rating = movie_details.get('content_rating', '')
    
    if content_rating in ['G', 'PG']:
        return "family"
    elif content_rating in ['PG-13']:
        return "teen"
    elif content_rating in ['R', 'NC-17']:
        return "adult"
    
    # If no content rating, analyze genres
    genres = movie_details.get('genres', [])
    genre_str = ' '.join(genres).lower()
    
    if any(g in genre_str for g in ['family', 'animation', 'children']):
        return "family"
    elif any(g in genre_str for g in ['horror', 'thriller']) or movie_details.get('adult', False):
        return "adult"
    
    # If still unclear, use keyword analysis
    audiences = []
    for audience, keywords in TARGET_AUDIENCE.items():
        for keyword in keywords:
            if keyword in text:
                audiences.append(audience)
                break
    
    # Count audience mentions
    audience_counter = Counter(audiences)
    
    # Return the most likely audience, or general if unclear
    if audience_counter:
        return audience_counter.most_common(1)[0][0]
    else:
        return "general"

def identify_franchise(movie_details):
    """ Franchise detection with pattern recognition and filtering """
    if not movie_details:
        return []
    
    title = movie_details.get('title', '').lower()
    original_title = movie_details.get('original_title', '').lower() if movie_details.get('original_title') else ''
    overview = movie_details.get('overview', '').lower() if movie_details.get('overview') else ''
    
    # Get production companies
    production_companies = []
    for company in movie_details.get('production_companies', []):
        if isinstance(company, dict) and 'name' in company:
            production_companies.append(company['name'].lower())
        elif isinstance(company, str):
            production_companies.append(company.lower())
    
    # Get collection information
    collection_name = ""
    if isinstance(movie_details.get('belongs_to_collection'), dict) and 'name' in movie_details.get('belongs_to_collection', {}):
        collection_name = movie_details['belongs_to_collection']['name'].lower()
    
    # Generate the combined text for searching
    text = f"{title} {original_title} {collection_name}"
    
    # Isolate the title for more precise matching
    # Remove common words and numbers from title for matching
    clean_title = re.sub(r'[0-9]', '', title)
    clean_title = re.sub(r'\bthe\b|\ba\b|\ban\b|\band\b|\bof\b|\bin\b|\bon\b|\bto\b|\bfor\b|\bwith\b|\bat\b|\bfrom\b|\bby\b', '', clean_title)
    clean_title = clean_title.strip()
    
    franchises = []
    
    # Direct franchise identification based on exact title/collection matches
    if 'marvel' in collection_name or 'avengers' in collection_name or 'mcu' in collection_name:
        franchises.append('mcu')
    elif 'dc' in collection_name or 'batman' in collection_name or 'superman' in collection_name:
        franchises.append('dceu')
    elif 'star wars' in collection_name:
        franchises.append('star_wars')
    elif 'harry potter' in collection_name or 'wizarding world' in collection_name:
        franchises.append('harry_potter')
    elif 'lord of the rings' in collection_name or 'middle earth' in collection_name:
        franchises.append('lord_of_the_rings')
    elif 'fast' in collection_name and ('furious' in collection_name or 'saga' in collection_name):
        franchises.append('fast_and_furious')
    elif 'jurassic' in collection_name:
        franchises.append('jurassic_park')
    
    # Production company matching (
    company_franchise_map = {
        'marvel studios': 'mcu',
        'marvel entertainment': 'mcu',
        'dc films': 'dceu', 
        'dc entertainment': 'dceu',
        'lucasfilm': 'star_wars',
        'warner bros. animation': 'dceu',
        'mgm': 'james_bond',
        'eon productions': 'james_bond',
        'studio ghibli': 'studio_ghibli',
        'pixar': 'pixar',
        'dreamworks': 'dreamworks',
        'disney': 'disney'
    }
    
    for company in production_companies:
        for company_pattern, franchise in company_franchise_map.items():
            if company_pattern in company:
                franchises.append(franchise)
    
    # Title-based franchise detection
    if 'spider-man' in title or 'spiderman' in title:
        franchises.append('mcu') 
    
    elif 'captain america' in title:
        franchises.append('mcu')
        
    elif 'iron man' in title:
        franchises.append('mcu')
        
    elif 'thor' in title and 'thor' in clean_title:  
        franchises.append('mcu')
        
    elif 'hulk' in title and 'hulk' in clean_title:
        franchises.append('mcu')
        
    elif 'avengers' in title:
        franchises.append('mcu')
        
    elif 'guardians of the galaxy' in title:
        franchises.append('mcu')
        
    elif 'black panther' in title:
        franchises.append('mcu')
        
    elif 'doctor strange' in title:
        franchises.append('mcu')
        
    elif 'ant-man' in title or 'antman' in title:
        franchises.append('mcu')
        
    elif 'black widow' in title:
        franchises.append('mcu')
    
    elif 'batman' in title and 'lego' not in title:  
        franchises.append('dceu')
        
    elif 'superman' in title and 'lego' not in title:
        franchises.append('dceu')
        
    elif 'wonder woman' in title:
        franchises.append('dceu')
        
    elif 'justice league' in title:
        franchises.append('dceu')
        
    elif 'aquaman' in title:
        franchises.append('dceu')
        
    elif 'shazam' in title:
        franchises.append('dceu')
        
    elif 'suicide squad' in title:
        franchises.append('dceu')
    
    elif 'fast & furious' in title or 'fast and furious' in title:
        franchises.append('fast_and_furious')
    
    elif 'star wars' in title:
        franchises.append('star_wars')
        
    elif 'rogue one' in title and 'star wars' in collection_name:
        franchises.append('star_wars')
        
    elif 'the last jedi' in title:
        franchises.append('star_wars')
        
    elif 'the force awakens' in title:
        franchises.append('star_wars')
    
    elif 'harry potter' in title:
        franchises.append('harry_potter')
        
    elif 'fantastic beasts' in title:
        franchises.append('harry_potter')
    
    elif 'lord of the rings' in title:
        franchises.append('lord_of_the_rings')
        
    elif 'the hobbit' in title:
        franchises.append('lord_of_the_rings')
    
    elif 'jurassic' in title:
        franchises.append('jurassic_park')
    
    # Only if we haven't found any franchises yet, try a more general keyword approach
    if not franchises:
        # Use FRANCHISES dictionary from movie_utils.py for keyword matching
        for franchise, keywords in FRANCHISES.items():
            # Check for franchise keywords in the text
            keyword_matches = sum(1 for keyword in keywords if keyword in text)
            if keyword_matches >= 3:  # Require at least 3 matches to avoid false positives
                franchises.append(franchise)
    
    # Filter out frequently mismatched franchises
    known_mismatches = {
        'guardians of the galaxy': ['onward'],
        'captain america': ['brave'],
        'avengers': ['wall-e', 'walle'],
        'solo': ['wall-e', 'walle'], 
        'minecraft': ['onward']
    }
    
    for movie_pattern, wrong_franchises in known_mismatches.items():
        if movie_pattern in title:
            franchises = [f for f in franchises if f not in wrong_franchises]
    
    # Remove duplicates
    return list(set(franchises))


def extract_core_concepts(text, n=5):
    """ Extract the most important concepts from text """
    if not text:
        return []
    
    tokens = preprocess_text(text)
    
    # Count word frequencies
    word_counts = Counter(tokens)
    
    # Extract most common words (excluding very common words)
    common_words = [word for word, count in word_counts.most_common(n*2) 
                    if word not in ['movie', 'film', 'story', 'character']]
    
    return common_words[:n]  

def build_enhanced_movie_profile(movie_id):
    """ Build text profile of a movie """
    try:
        # Fetch movie data
        movie_details = fetch_movie_details(movie_id)
        if not movie_details:
            print(f"Could not fetch movie details for ID {movie_id}")
            return None
        
        # Get basic movie information
        title = movie_details.get('title', '')
        overview = movie_details.get('overview', '')
        genres = movie_details.get('genres', [])
        
        # Try to get actors
        try:
            actors = get_actors(movie_id)
        except Exception as e:
            print(f"Error getting actors for movie {movie_id}: {e}")
            actors = []
        
        # Try to get directors
        try:
            directors = get_director(movie_id)
        except Exception as e:
            print(f"Error getting directors for movie {movie_id}: {e}")
            directors = []
        
        # Try to get keywords
        try:
            keywords_data = fetch_keywords_for_movies(movie_id)
            keywords = keywords_data.get("keywords", [])
        except Exception as e:
            print(f"Error getting keywords for movie {movie_id}: {e}")
            keywords = []
        
        # Extract themes 
        try:
            themes = identify_themes(overview)
        except Exception as e:
            print(f"Error identifying themes for movie {movie_id}: {e}")
            themes = []
        
        # Extract tone 
        try:
            tones = identify_tone(overview)
        except Exception as e:
            print(f"Error identifying tones for movie {movie_id}: {e}")
            tones = []
        
        # Identify target audience 
        try:
            target_audience = identify_target_audience(movie_details)
        except Exception as e:
            print(f"Error identifying target audience for movie {movie_id}: {e}")
            target_audience = "general"
        
        # Identify franchise connection 
        try:
            franchises = identify_franchise(movie_details)
        except Exception as e:
            print(f"Error identifying franchises for movie {movie_id}: {e}")
            franchises = []
        
        # Extract core concepts 
        try:
            core_concepts = extract_core_concepts(overview)
        except Exception as e:
            print(f"Error extracting core concepts for movie {movie_id}: {e}")
            core_concepts = []
        
        # Build enhanced profile elements
        enhanced_elements = {
            'title': title,
            'genres': genres,
            'actors': actors,
            'directors': directors,
            'themes': themes,
            'tones': tones,
            'target_audience': target_audience,
            'franchises': franchises,
            'keywords': keywords,
            'core_concepts': core_concepts,
            'overview': overview
        }
        
        # Build a comprehensive text profile
        profile_text = f"{title} {title} "  
        
        # Add genres
        profile_text += f"{' '.join(genres)} {' '.join(genres)} "
        
        # Add actors
        profile_text += f"{' '.join(actors)} "
        
        # Add directors
        profile_text += f"{' '.join(directors)} {' '.join(directors)} "
        
        # Add themes
        profile_text += f"{' '.join(themes)} {' '.join(themes)} {' '.join(themes)} "
        
        # Add tones
        profile_text += f"{' '.join(tones)} {' '.join(tones)} "
        
        # Add target audience
        profile_text += f"{target_audience} {target_audience} "
        
        # Add franchises
        profile_text += f"{' '.join(franchises)} {' '.join(franchises)} {' '.join(franchises)} "
        
        # Add keywords
        profile_text += f"{' '.join(keywords)} "
        
        # Add core concepts
        profile_text += f"{' '.join(core_concepts)} "
        
        # Add overview last
        profile_text += overview
        
        return profile_text, enhanced_elements, movie_details
    
    except Exception as e:
        print(f"Error building profile for movie {movie_id}: {e}")
        return None

def parse_list_from_db(list_str):
    """ Safely parse a list string from the database """
    if not list_str:
        return []
        
    if isinstance(list_str, str):
        try:
            return ast.literal_eval(list_str)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing list: {e}")
            return []
    return list_str

def fetch_movie(movie_id):
    """ Fetch a single movie by ID """
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=en-US"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def fetch_movie_by_title(title):
    """ Fetch a single movie by exact title match """
    # First search for movies with similar titles
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={title}&language=en-US"
    response = requests.get(search_url)
    
    if response.status_code != 200:
        return None
    
    # Find exact title match (case-insensitive)
    movies = response.json().get("results", [])
    for movie in movies:
        if movie.get("title", "").lower() == title.lower():
            # Get detials
            movie_id = movie.get("id")
            if movie_id:
                details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_KEY}&language=en-US"
                details_response = requests.get(details_url)
                if details_response.status_code == 200:
                    return details_response.json()
    return None

def fetch_movies_by_genre(genre, limit=30):
    """ Fetch movies by genre from TMDB API """
    # First get the genre ID from the name
    genre_mapping = fetch_genre_mapping()
    genre_id = None
    
    # Find the genre ID (case-insensitive)
    for id, name in genre_mapping.items():
        if name.lower() == genre.lower():
            genre_id = id
            break
    
    if not genre_id:
        print(f"Genre '{genre}' not found in genre mapping")
        return []
    
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_KEY}&with_genres={genre_id}&sort_by=popularity.desc&page=1&vote_count.gte=100"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("results", [])[:limit]
    return []

def fetch_movies_by_keyword(keyword, limit=20):
    """ Fetch movies by keyword from TMDB API """
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_KEY}&query={keyword}&page=1"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("results", [])[:limit]
    return []

def is_same_movie(candidate_title, favourite_title, threshold=0.8):
    """ Check if two titles refer to the same movie """
    if not candidate_title or not favourite_title:
        return False
    
    # Normalise titles
    def normalize_title(title):
        return re.sub(r'[^\w\s]', '', title.lower().strip())
    
    candidate_norm = normalize_title(candidate_title)
    favourite_norm = normalize_title(favourite_title)
    
    if candidate_norm == favourite_norm:
        return True
    
    # Check for franchise pattern 
    if candidate_norm.startswith(favourite_norm + " ") or favourite_norm.startswith(candidate_norm + " "):
        return True
    
    # Word-based similarity for longer titles
    if len(candidate_norm) > 4 and len(favourite_norm) > 4:
        candidate_words = set(candidate_norm.split())
        favourite_words = set(favourite_norm.split())
        
        if not candidate_words or not favourite_words:
            return False
        
        # Check intersection ratio
        common = candidate_words.intersection(favourite_words)
        ratio = len(common) / min(len(candidate_words), len(favourite_words))
        
        return ratio >= threshold
    
    return False

