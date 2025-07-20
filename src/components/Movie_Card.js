import React, { useState } from 'react';
import "../styles/Movie_Card.css";
import { useNavigate } from 'react-router-dom'; 
import { useWatchlist } from '../context/Watchlist_Context';
import MovieFeedback from '../components/MovieFeedback'

const Movie_Card = ({ movie, showFeedback = false }) => {
  const imgBaseURL = "https://image.tmdb.org/t/p/w500"; 
  const navigate = useNavigate(); 
  const [isLoading, setIsLoading] = useState(false);
  const { isInWatchlist, addToWatchlist } = useWatchlist();
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  
  // Debug logging for data structure issues
  if (!movie) {
    console.error("Movie_Card received null/undefined movie");
    return null;
  }
  
  const getMovieId = () => {
    // Handle both movie_id (from recommendations) and id (from TMDB API)
    const movieId = movie.movie_id || movie.id;
    if (!movieId) {
      console.warn("No movie ID found for movie:", movie);
    }
    return movieId;
  };
  
  // Release date 
  const formatDate = (dateString) => {
    if (!dateString) return "Unknown";
    try {
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString('en-US', options);
    } catch (error) {
      return "Unknown";
    }
  };
  
  // Used to calculate the age of a movie so user know if its new or not
  const isNew = () => {
    if (!movie.release_date) return false;
    try {
      const releaseDate = new Date(movie.release_date);
      const threeMonthsAgo = new Date();
      threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
      return releaseDate > threeMonthsAgo;
    } catch (error) {
      return false;
    }
  };

  // Helper function to safely get genres
  const getGenres = () => {
    if (!movie.genres) return "Unknown";
    
    if (Array.isArray(movie.genres)) {
      return movie.genres.slice(0, 2).join(", ");
    } else if (typeof movie.genres === 'string') {
      // Handle case where genres might be stored as a string
      try {
        const parsed = JSON.parse(movie.genres);
        if (Array.isArray(parsed)) {
          return parsed.slice(0, 2).join(", ");
        }
      } catch (e) {
        // If it's just a comma-separated string
        return movie.genres.split(',').slice(0, 2).join(", ");
      }
    }
    return "Unknown";
  };

  const getOverview = () => {
    if (!movie.overview || movie.overview.trim() === '') {
      return "No description available.";
    }
    return movie.overview;
  };

  const getRating = () => {
    if (!movie.vote_average && movie.vote_average !== 0) {
      return null;
    }
    return Number(movie.vote_average).toFixed(1);
  };

  // Use the movieId to check if it's in the watchlist
  const movieId = getMovieId();
  const movieInWatchlist = isInWatchlist(movieId);

  // watchlist function
  const handleAddToWatchlist = async (e) => {
    // prevents navigating to movie details if "add to watchlist" is clicked
    e.stopPropagation();
    
    // Don't do anything if already in watchlist
    if (movieInWatchlist) {
      return;
    }
    
    setIsLoading(true);

    try {
      // Use context function to add to watchlist
      await addToWatchlist(movieId, 'want_to_watch');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      alert('Failed to add to watchlist');
    } finally {
      setIsLoading(false);
    }
  };

  // Toggle feedback form visibility
  const toggleFeedback = (e) => {
    e.stopPropagation(); 
    setShowFeedbackForm(!showFeedbackForm);
  };

  // Navigates to movie details page when card is clicked
  const handleCardClick = () => {
    if (movieId) {
      navigate(`/movie/${movieId}`);
    } else {
      console.error("No valid ID found for this movie:", movie)
    }
  };

  return (
    <div className="movie-card-container">
      <div className="movie-card" onClick={handleCardClick}> 
        <img
          src={movie.poster_path ? `${imgBaseURL}${movie.poster_path}` : "/images/no-poster.jpg"} 
          alt={movie.title || movie.movie_title || "Movie"}
          onError={(e) => {
            e.target.src = "/images/no-poster.jpg";
          }}
        />
        {isNew() && <div className="movie-badge">NEW</div>}
        <div className="movie-info">
          <h3>{movie.title || movie.movie_title || "Unknown Title"}</h3>
          <p>{getOverview()}</p>
          <small>{formatDate(movie.release_date)}</small>
          <div className="movie-meta">
            <div className="movie-genres">
              {getGenres()}
            </div>
            {getRating() && (
              <div className="movie-rating">
                ★ {getRating()}
              </div>
            )}
          </div>
          <div className="card-actions">
            <button 
              onClick={handleAddToWatchlist} 
              className={`watchlist-btn ${movieInWatchlist ? 'added' : ''}`}
              disabled={isLoading || movieInWatchlist}
            >
              {isLoading ? 'Adding...' : movieInWatchlist ? 'Added ✓' : 'Add to Watchlist'}
            </button>
            
            {showFeedback && (
              <button 
                onClick={toggleFeedback} 
                className="feedback-toggle-btn"
              >
                {showFeedbackForm ? 'Hide Feedback' : 'Rate This Recommendation'}
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Feedback form outside the clickable card area */}
      {showFeedback && showFeedbackForm && (
        <div className="movie-feedback-wrapper" onClick={(e) => e.stopPropagation()}>
          <MovieFeedback 
            movieId={movieId} 
            onFeedbackSaved={() => {
              // Auto-hide the form after feedback is submitted
              setTimeout(() => setShowFeedbackForm(false), 2000);
            }}
          />
        </div>
      )}
    </div>
  );
};

export default Movie_Card;