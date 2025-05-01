import numpy as np
from datetime import datetime
from collections import Counter
import json
from database import get_db_connection
from utils.movie_utils import (
    build_enhanced_movie_profile, 
    parse_list_from_db,
    fetch_movie,
    identify_themes,
    identify_tone,
    identify_target_audience,
    identify_franchise
)
from decimal import Decimal

class UserPreferenceModel:
    """Created a user preference modle that lears from user behaviours and adjust weights based on user"""
    
    def __init__(self, user_id=None):
        self.user_id = user_id
        
        # Base weights 
        self.base_weights = {
            'tfidf': 0.15,
            'genre': 0.20,
            'theme': 0.15,
            'tone': 0.10,
            'audience': 0.10,
            'franchise': 0.25,
            'actor': 0.05,
            'director': 0.05
        }
        
        # User's current preference weights (will be adjusted based on behavior)
        self.current_weights = self.base_weights.copy()
        
        # Stores user's ratings by category
        self.genre_ratings = {}
        self.theme_ratings = {}
        self.franchise_ratings = {}
        self.tone_ratings = {}
        self.actor_ratings = {}
        
        # Track interaction recency (will implement later)
        self.last_interaction_dates = {}
        
        # Maintain history of successful recommendations
        self.successful_recommendations = []
        
        # Load saved preferences if user_id is provided
        if user_id:
            self.load_from_database()
    
    def load_from_database(self):
        """ Load user preference model from database if it exist """
        if not self.user_id:
            return
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
    
        try:
            # Load style preferences
            cursor.execute("""
                SELECT * FROM user_style_preferences
                WHERE user_id = %s
            """, (self.user_id,))
        
            style_prefs = cursor.fetchone()
        
            if style_prefs:
                # Load preference vector if available
                if style_prefs.get('preference_vector'):
                    try:
                        self.current_weights = json.loads(style_prefs['preference_vector'])
                    except:
                        print("Error parsing preference vector")

                # Select "good" feeback from user from database
                cursor.execute("""
                    SELECT movie_id, feedback_value 
                    FROM recommendation_feedback
                    WHERE user_id = %s AND feedback_value = 'good'
                """, (self.user_id,))
            
                feedback_items = cursor.fetchall()
                for item in feedback_items:
                    self.successful_recommendations.append({
                    'movie_id': item['movie_id'],
                    'feedback': item.get('feedback_value')
                    })
        
            # Load ratings from watchlist
            cursor.execute("""
                SELECT movie_id, user_rating, status, date_added 
                FROM user_watchlist
                WHERE user_id = %s
            """, (self.user_id,))
        
            watchlist_items = cursor.fetchall()
        
            # Process watchlist items to extract preferences
            if watchlist_items:
                self._process_watchlist_items(watchlist_items)
            
        except Exception as e:
            print(f"Error loading user preference model: {e}")
        finally:
            cursor.close()
            connection.close()
    
    def _process_watchlist_items(self, watchlist_items):
        """ Process watchlist items to extract user preferences """
        genre_scores = {}
        theme_scores = {}
        franchise_scores = {}
        tone_scores = {}
        actor_scores = {}
        
        current_time = datetime.now()
        
        for item in watchlist_items:
            movie_id = item.get('movie_id')
            if not movie_id:
                continue
                
            # Get basic item information
            status = item.get('status', '')
            
            # Handle Decimal type for user_rating
            user_rating = item.get('user_rating')
            if user_rating is not None:
                if isinstance(user_rating, Decimal):
                    user_rating = float(user_rating)
            else:
                user_rating = 0
                
            date_added = item.get('date_added')
            
            # Calculate time decay factor (more recent = higher weight)
            time_decay = 1.0
            if date_added:
                try:
                    if isinstance(date_added, str):
                        date_obj = datetime.strptime(date_added, '%Y-%m-%d %H:%M:%S')
                    else:
                        date_obj = date_added
                        
                    days_diff = (current_time - date_obj).days
                    time_decay = np.exp(-0.05 * days_diff) 
                except:
                    pass
            
            # Calculate importance based on status and rating
            importance = 0.0
            
            if status == 'watched':
                importance = 1.0
            elif status == 'watching':
                importance = 0.7
            elif status == 'want_to_watch':
                importance = 0.3
                
            # Apply rating boost
            if user_rating and status == 'watched':
                rating_factor = user_rating / 10.0
                if rating_factor >= 0.7: 
                    importance *= (1.0 + rating_factor)
            
            # Apply time decay
            adjusted_importance = importance * time_decay
            
            # Extract and track preferences by category
            try:
                # For each movie in watchlist, fetch its details from TMDB
                movie_details = fetch_movie(movie_id)
                
                if movie_details:
                    # Extract and process genres
                    genres = [genre["name"] for genre in movie_details.get("genres", [])]
                    for genre in genres:
                        if genre not in genre_scores:
                            genre_scores[genre] = 0.0
                        genre_scores[genre] += adjusted_importance
                    
                    # Extract themes from overview
                    overview = movie_details.get("overview", "")
                    themes = identify_themes(overview)
                    for theme in themes:
                        if theme not in theme_scores:
                            theme_scores[theme] = 0.0
                        theme_scores[theme] += adjusted_importance
                    
                    # Extract tones
                    tones = identify_tone(overview)
                    for tone in tones:
                        if tone not in tone_scores:
                            tone_scores[tone] = 0.0
                        tone_scores[tone] += adjusted_importance

                    try:
                        franchises = identify_franchise(movie_details)
                        for franchise in franchises:
                            if franchise not in franchise_scores:
                                franchise_scores[franchise] = 0.0
                            # Give extra weight to franchise
                            franchise_scores[franchise] += adjusted_importance * 3.0
                    except Exception as e:
                        print(f"Error processing franchise for {movie_id}: {e}")   
                        import traceback
                        traceback.print_exc()                 
                    self.last_interaction_dates[movie_id] = date_added or current_time                    
            except Exception as e:
                print(f"Error processing watchlist item: {e}")
                continue
        
        # Normalise and store scores
        self.genre_ratings = self._normalise_scores(genre_scores)
        self.theme_ratings = self._normalise_scores(theme_scores)
        self.franchise_ratings = self._normalise_scores(franchise_scores)
        self.tone_ratings = self._normalise_scores(tone_scores)
        
        # Update weights based on learned preferences
        self._update_weights()
    
    def _normalise_scores(self, score_dict):
        """ Normalise scores to sum to 1.0 """
        if not score_dict:
            return {}
            
        total = sum(score_dict.values())
        if total <= 0:
            return {}
            
        return {k: v / total for k, v in score_dict.items()}
    
    def _calculate_consistency(self, preference_dict):
        """ Calculate preference consistency (0-1) """
        if not preference_dict or len(preference_dict) <= 1:
            return 0.0
            
        values = list(preference_dict.values())
        values.sort()
        n = len(values)

        if n > 10:
            top_values = values[-5:]  # Top 5 values
            n = len(top_values)
            values = top_values
            
        cum_values = np.cumsum(values)
        gini = (2 * np.sum((np.arange(1, n+1) * values)) / (n * np.sum(values))) - (n + 1) / n
        
        return gini
    
    def _update_weights(self):
        """ Update component weights based on learned preferences """
        # Calculate preference consistency
        genre_consistency = self._calculate_consistency(self.genre_ratings)
        theme_consistency = self._calculate_consistency(self.theme_ratings)
        franchise_consistency = self._calculate_consistency(self.franchise_ratings)
        
        # Start with base weights
        new_weights = self.base_weights.copy()
        
        # If user has strong genre preferences, increase genre weight
        if genre_consistency > 0.6:
            genre_boost = min(0.1 * genre_consistency, 0.1)
            new_weights['genre'] += genre_boost
            # Reduce TF-IDF weight to compensate
            new_weights['tfidf'] -= genre_boost/2
            new_weights['tone'] -= genre_boost/2
        
        # If user has strong franchise preferences, significantly boost franchise weight
        if franchise_consistency > 0.5:
            franchise_boost = min(0.2 * franchise_consistency, 0.15)
            new_weights['franchise'] += franchise_boost
            # Reduce other weights to compensate
            new_weights['tfidf'] -= franchise_boost/3
            new_weights['genre'] -= franchise_boost/3
            new_weights['theme'] -= franchise_boost/3
        
        # If user has strong theme preferences, boost theme weight
        if theme_consistency > 0.5:
            theme_boost = min(0.1 * theme_consistency, 0.08)
            new_weights['theme'] += theme_boost
            # Reduce to compensate
            new_weights['tfidf'] -= theme_boost/2
            new_weights['audience'] -= theme_boost/2
        
        # Normalise weights to ensure they sum to 1.0
        weight_sum = sum(new_weights.values())
        self.current_weights = {k: v / weight_sum for k, v in new_weights.items()}
    
    def save_to_database(self):
        """ Save the user preference model to the database """
        if not self.user_id:
            return False
            
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Convert current weights to JSON
            preference_vector_json = json.dumps(self.current_weights)
            
            # Calculate consistencies
            genre_consistency = self._calculate_consistency(self.genre_ratings)
            theme_consistency = self._calculate_consistency(self.theme_ratings)
            franchise_consistency = self._calculate_consistency(self.franchise_ratings)
            tone_consistency = self._calculate_consistency(self.tone_ratings)
            
            # Overall consistency metric
            preference_consistency = (
                0.3 * genre_consistency + 
                0.3 * theme_consistency + 
                0.2 * franchise_consistency + 
                0.2 * tone_consistency
            )
            
            # Determine dominant preferences for different categories
            animation_type = self._get_dominant_preference(self.genre_ratings, ['Animation'])
            target_age = "general"
            if self.genre_ratings.get('Family', 0) > 0.3 or self.genre_ratings.get('Animation', 0) > 0.3:
                target_age = "family"
            elif self.genre_ratings.get('Horror', 0) > 0.3 or self.genre_ratings.get('Thriller', 0) > 0.3:
                target_age = "adult"
                
            tone = self._get_dominant_preference(self.tone_ratings, ['dark', 'light', 'comedic', 'serious'])
            
            # Save or update user style preferences
            cursor.execute("""
                INSERT INTO user_style_preferences 
                (user_id, animation_type, target_age, tone, preference_consistency, preference_vector) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                animation_type = VALUES(animation_type),
                target_age = VALUES(target_age),
                tone = VALUES(tone),
                preference_consistency = VALUES(preference_consistency),
                preference_vector = VALUES(preference_vector),
                last_updated = CURRENT_TIMESTAMP
            """, (
                self.user_id, 
                animation_type,
                target_age, 
                tone,
                preference_consistency,
                preference_vector_json
            ))
            
            connection.commit()
            return True    
        except Exception as e:
            print(f"Error saving user preference model: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()
    
    def _get_dominant_preference(self, pref_dict, categories=None):
        """ Get the dominant preference from a preference dictionary """
        if not pref_dict:
            return None
            
        # If categories provided, filter the dictionary
        if categories:
            filtered_dict = {k: v for k, v in pref_dict.items() if k in categories}
            if filtered_dict:
                return max(filtered_dict, key=filtered_dict.get)
        
        # Otherwise return the overall highest value
        return max(pref_dict, key=pref_dict.get) if pref_dict else None
    
    def learn_from_watchlist(self, watchlist_items):
        """ Learn user preferences from watchlist items """
        if not watchlist_items:
            return
        
        self._process_watchlist_items(watchlist_items)
        self.save_to_database()
    
    def get_preference_weights(self):
        """ Get the current preference weights for similarity calculation """
        return self.current_weights
        
    def update_from_feedback(self, recommendation_feedback):
        """ Update weights based on user feedback on recommendations """
        if not recommendation_feedback:
            return
        
        # Successful recommendations get analysed to improve future recommendations
        successful_ids = []
        connection = get_db_connection()
        cursor = connection.cursor()
    
        try:
            for movie_id, feedback in recommendation_feedback.items():
                # Extract relevant feedback data
                is_positive = feedback.get('is_positive', False)
                feedback_value = 'good' if is_positive else 'bad'
            
                # Save feedback to database 
                cursor.execute("""
                    INSERT INTO recommendation_feedback 
                    (user_id, movie_id, feedback_value, feedback_date) 
                    VALUES (%s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE 
                    feedback_value = VALUES(feedback_value),
                    feedback_date = NOW()
                """, (
                    self.user_id,
                    movie_id,
                    feedback_value
                ))
            
                if is_positive:
                    successful_ids.append(movie_id)
                
                    # Add to successful recommendations 
                    rec_exists = False
                    for rec in self.successful_recommendations:
                        if rec.get('movie_id') == movie_id:
                            rec_exists = True
                            break
                
                    if not rec_exists:
                        self.successful_recommendations.append({
                            'movie_id': movie_id,
                            'feedback': feedback_value
                        })   
            connection.commit()
        except Exception as e:
            print(f"Error updating from feedback: {e}")
            connection.rollback()
        finally:
            cursor.close()
            connection.close()
    
        # If we have successful recommendations, analyse them
        if successful_ids:
            # Find common elements in successful recommendations
            self._analyze_successful_recommendations(successful_ids)
            self.save_to_database()
    
    def _analyze_successful_recommendations(self, movie_ids):
        """ Find common elements in successful recommendations to boost weights """
        
        if not movie_ids:
            return
            
        # Fetch movie details from API for each successful recommendation
        genre_counter = Counter()
        theme_counter = Counter()
        franchise_counter = Counter()
        tone_counter = Counter()
        
        count = 0
        for movie_id in movie_ids:
            try:
                # Fetch movie details from TMDB API
                movie_details = fetch_movie(movie_id)
                if not movie_details:
                    continue
                
                # Extract genres
                genres = [genre["name"] for genre in movie_details.get("genres", [])]
                for genre in genres:
                    genre_counter[genre] += 1
                
                # Extract overview for theme/tone analysis
                overview = movie_details.get("overview", "")
                
                # Extract themes
                themes = identify_themes(overview)
                for theme in themes:
                    theme_counter[theme] += 1
                
                # Extract tones
                tones = identify_tone(overview)
                for tone in tones:
                    tone_counter[tone] += 1
                
                # Extract franchises
                franchises = identify_franchise(movie_details)
                for franchise in franchises:
                    franchise_counter[franchise] += 1
                
                count += 1
            except Exception as e:
                print(f"Error analyzing movie {movie_id}: {e}")
                continue       
        if count == 0:
            return
            
        # Find dominant elements (ones that appear in at least half of successful recommendations)
        threshold = count / 2.0
        
        dominant_genres = [g for g, c in genre_counter.items() if c >= threshold]
        dominant_themes = [t for t, c in theme_counter.items() if c >= threshold]
        dominant_franchises = [f for f, c in franchise_counter.items() if c >= threshold]
        dominant_tones = [t for t, c in tone_counter.items() if c >= threshold]
        
        # If we found dominant elements, adjust weights
        if dominant_genres or dominant_themes or dominant_franchises:
            # Start with current weights
            new_weights = self.current_weights.copy()
            
            # Adjust based on findings
            if dominant_franchises:
                # Strong franchise preference detected
                new_weights['franchise'] += 0.05
                new_weights['tfidf'] -= 0.03
                new_weights['actor'] -= 0.02
            
            if dominant_genres and len(dominant_genres) <= 3:
                # Focused genre preference
                new_weights['genre'] += 0.03
                new_weights['tfidf'] -= 0.02
                new_weights['director'] -= 0.01
                
            if dominant_themes and len(dominant_themes) <= 3:
                # Focused theme preference
                new_weights['theme'] += 0.03
                new_weights['tone'] += 0.01
                new_weights['tfidf'] -= 0.02
                new_weights['audience'] -= 0.02
                
            if dominant_tones and len(dominant_tones) <= 2:
                # Strong tone preference
                new_weights['tone'] += 0.02
                new_weights['tfidf'] -= 0.01
                new_weights['director'] -= 0.01
            
            # Normalise weights
            weight_sum = sum(new_weights.values())
            self.current_weights = {k: v / weight_sum for k, v in new_weights.items()}
    
    def adjust_movie_scores(self, movie_scores, candidate_movies):
        """ Apply preference-based adjustments to similarity scores """
        if not movie_scores or not candidate_movies:
            return movie_scores
            
        adjusted_scores = {}
        
        for movie_id, score in movie_scores.items():
            if movie_id not in candidate_movies:
                adjusted_scores[movie_id] = score
                continue
                
            movie_data = candidate_movies[movie_id]
            
            # Get enhanced elements for the movie
            genres = parse_list_from_db(movie_data.get('genres', []))
            themes = parse_list_from_db(movie_data.get('themes', []))
            franchises = parse_list_from_db(movie_data.get('franchises', []))
            tones = parse_list_from_db(movie_data.get('tones', []))
            actors = parse_list_from_db(movie_data.get('actors', []))
            
            # Start with the base score
            adjusted_score = score

            # Genre match bonus
            genre_bonus = 0.0
            for genre in genres:
                genre_bonus += self.genre_ratings.get(genre, 0.0)
            
            # Theme match bonus
            theme_bonus = 0.0
            for theme in themes:
                theme_bonus += self.theme_ratings.get(theme, 0.0)
            
            # Franchise match bonus (stronger effect)
            franchise_bonus = 0.0
            for franchise in franchises:
                franchise_bonus += self.franchise_ratings.get(franchise, 0.0) * 1.5
            
            # Actor match bonus
            actor_bonus = 0.0
            for actor in actors:
                actor_bonus += self.actor_ratings.get(actor, 0.0)

            adjusted_score *= (1.0 + 0.2 * genre_bonus)
            adjusted_score *= (1.0 + 0.15 * theme_bonus)
            adjusted_score *= (1.0 + 0.25 * franchise_bonus)
            adjusted_score *= (1.0 + 0.1 * actor_bonus)
            
            adjusted_scores[movie_id] = adjusted_score
            
        return adjusted_scores


def build_user_preference_model(user_id, watchlist_items=None, questionnaire_data=None):
    """ Build a user preference model by combining watchlist and questionnaire data """

    # Create a new preference model
    model = UserPreferenceModel(user_id)
    
    # If we have watchlist items, process them
    if watchlist_items:
        model.learn_from_watchlist(watchlist_items)
    
    # Add questionnaire data
    if questionnaire_data:
        # Get a database connection
        connection = get_db_connection()
        cursor = connection.cursor()
        
        try:
            # Process favourite genres
            favorite_genres = parse_list_from_db(questionnaire_data.get('genres', []))
            for genre in favorite_genres:
                if genre not in model.genre_ratings:
                    model.genre_ratings[genre] = 0.0
                model.genre_ratings[genre] += 0.2  
            
            # Process favourite actors
            favorite_actors = parse_list_from_db(questionnaire_data.get('favourite_actors', []))
            for actor in favorite_actors:
                if actor not in model.actor_ratings:
                    model.actor_ratings[actor] = 0.0
                model.actor_ratings[actor] += 0.3  
            
            # Normalise again after adding questionnaire data
            model.genre_ratings = model._normalise_scores(model.genre_ratings)
            model.actor_ratings = model._normalise_scores(model.actor_ratings)
            
            # Update weights
            model._update_weights()
            
            # Save to database
            model.save_to_database()
            
        except Exception as e:
            print(f"Error building user preference model: {e}")
            pass
        finally:
            cursor.close()
            connection.close()
    
    return model