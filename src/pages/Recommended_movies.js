import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import MovieCard from '../components/Movie_Card';
import {useUser} from "../context/User_Context";
import '../styles/Recommended_movies.css';


const RecommendationFeedback = ({ onRefresh, onSaveFeedback }) => {
  const [feedbackValue, setFeedbackValue] = useState(null);
  
  const handleFeedback = (value) => {
    setFeedbackValue(value);
    onSaveFeedback(value);
  };
  
  return (
    <div className="recommendation-feedback">
      <h3>How are these recommendations?</h3>
      <div className="feedback-buttons">
        <button 
          className={`feedback-btn ${feedbackValue === 'good' ? 'active' : ''}`}
          onClick={() => handleFeedback('good')}
        >
          👍 Good Recommendations
        </button>
        <button 
          className={`feedback-btn ${feedbackValue === 'bad' ? 'active' : ''}`}
          onClick={() => handleFeedback('bad')}
        >
          👎 Not What I Expected
        </button>
      </div>
      {feedbackValue === 'bad' && (
        <button className="refresh-btn" onClick={onRefresh}>
          Generate New Recommendations
        </button>
      )}
    </div>
  );
};

const Recommended_movies = () => {
  const {username} = useUser();
  const [movies, setMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const requestInProgressRef = useRef(false);
  const retryTimeoutRef = useRef(null);

  const handleSaveFeedback = async (feedbackValue) => {
    try {
      const token = localStorage.getItem("token");
      await axios.post("http://127.0.0.1:5000/recommendation-feedback", {
        feedback: feedbackValue
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Show confirmation to the user
      if (feedbackValue === 'good') {
        alert('Thanks for your feedback! We\'ll use this to improve future recommendations.');
      }
    } catch (error) {
      console.error("Error saving feedback:", error);
    }
  };

  const fetchRecommendations = async () => {
    // Prevents calling the /recommend endpoint twice
    if (requestInProgressRef.current) {
      console.log("Recommendations request already in progress");
      return;
    }
    
    setIsLoading(true);
    requestInProgressRef.current = true;
    setError(null);
    
    try {
      console.log("Fetching recommended movies...");
      const token = localStorage.getItem("token");
      const response = await axios.get("http://127.0.0.1:5000/recommend", {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      console.log("Response data:", response.data);
      setMovies(response.data.recommended_movies || []);
      
      // If recommendations are still being generated, poll 
      if (response.data.status === "generating") {
        console.log("Recommendations are still being generated, will retry in 5 seconds");
        // Clear timeouts to prevent multiple timers
        if (retryTimeoutRef.current) {
          clearTimeout(retryTimeoutRef.current);
        }
        
        retryTimeoutRef.current = setTimeout(() => {
          console.log("Retrying recommendation fetch");
          requestInProgressRef.current = false;
          fetchRecommendations();
        }, 5000);
      } else {
        // Once response is complete reset the request flag
        requestInProgressRef.current = false;
        setIsLoading(false);
      }
    } catch (error) {
      console.error("Error fetching recommendations:", error);
      setError("Oops! It looks like your recommendations aren't available yet. Complete the questionnaire to unlock your personalised movie list");
      requestInProgressRef.current = false;
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();

    // Function to handle component unmount
    return () => {
      // Clear any timeouts
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
      // Reset the request flag
      requestInProgressRef.current = false;
    };
  }, []);

  // Function to manually refresh recommendations will implement full version later
  const refreshRecommendations = () => {
    if (!requestInProgressRef.current) {
      fetchRecommendations();
    }
  };

  // Gets genres from all movies
  const allGenres = [...new Set(movies.flatMap(movie => movie.genres || []))];

  // Filter movies by genre
  const filterMovies = (genre) => {
    setActiveFilter(genre);
  };

  const filteredMovies = activeFilter === 'all' 
    ? movies 
    : movies.filter(movie => (movie.genres || []).includes(activeFilter));

  return (   
    <div className="recommended-page">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><Link to="/movies">Movies</Link></li>
            <li><Link to="/homepage">Home</Link></li>
            <li><Link to="/watchlist">Watchlist</Link></li>
            <li><Link to="/profile">Profile</Link></li>
          </ul>
        </nav>
        <div className='username'>
          <p>Hello, {username || ":("}</p>
        </div>
      </header>

      <div className="recommendations-hero">
        <div className="hero-content">
          <h1>Your Personalised Recommendations</h1>
          <p>Movies curated just for you based on your preferences</p>
        </div>
      </div>

      <div className="filter-container">
        <h3>Filter by Genre:</h3>
        <div className="genre-filters">
          <button 
            className={activeFilter === 'all' ? 'filter-btn active' : 'filter-btn'}
            onClick={() => filterMovies('all')}
          >
            All
          </button>
          {allGenres.map(genre => (
            <button 
              key={genre}
              className={activeFilter === genre ? 'filter-btn active' : 'filter-btn'}
              onClick={() => filterMovies(genre)}
            >
              {genre}
            </button>
          ))}
        </div>
      </div>
      {!isLoading && !error && movies.length > 0 && (
        <div className="feedback-container">
          <RecommendationFeedback 
            onSaveFeedback={handleSaveFeedback} 
            onRefresh={refreshRecommendations} 
          />
        </div>
      )}
      <section className="recommendations-section">
        {isLoading ? (
          <div className="loading-spinner">
            <p>Loading your recommendations... This might take a while</p>
            <div className="spinner-animation"></div>
          </div>
        ) : error ? (
          <div className="error-message">
            <p>{error}</p>
            <button 
              className="retry-btn"
              onClick={refreshRecommendations}
              disabled={requestInProgressRef.current}
            >
              Try Again
            </button>
          </div>
        ) : (
          <>
            <h2>Recommended For You</h2>
            {filteredMovies.length > 0 ? (
              <div className="recommendations-grid">
                {filteredMovies.map(movie => (
                  <MovieCard key={movie.id || movie.movie_id} movie={movie} />
                ))}
              </div>
            ) : (
              <div className="no-results">
                <p>No movies found matching your filter criteria.</p>
              </div>
            )}
          </>
        )}
      </section>

      <div className="recommendation-info">
        <div className="info-card">
          <h3>How We Recommend</h3>
          <p>Our recommendations are based on your questionnaire responses, viewing history, and ratings.</p>
        </div>
        <div className="info-card">
          <h3>Update Preferences</h3>
          <Link to="/questionnaire" className="update-btn">Retake Questionnaire</Link>
          <button 
            className="refresh-btn"
            onClick={refreshRecommendations}
            disabled={requestInProgressRef.current}
          >
            Refresh Recommendations
          </button>
        </div>
      </div>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Recommended_movies;