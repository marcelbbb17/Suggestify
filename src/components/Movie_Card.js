import React, { useState, useEffect } from 'react';
import "../styles/Movie_Card.css";
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; 

const Movie_Card = ({ movie }) => {
  const imgBaseURL = "https://image.tmdb.org/t/p/w500"; 
  const navigate = useNavigate(); 
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const getMovieId = () => {
    return movie.movie_id || movie.id;
  };
  
  // Release date 
  const formatDate = (dateString) => {
    if (!dateString) return "Unknown";
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
  };
  
  // Used to calculate the age of a movie so user know if its new or not
  const isNew = () => {
    if (!movie.release_date) return false;
    const releaseDate = new Date(movie.release_date);
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
    return releaseDate > threeMonthsAgo;
  };

  // Checks if movie is already in watchlist
  useEffect(() => {
    const checkWatchlistStatus = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          return;
        }
  
        const response = await axios.get('http://127.0.0.1:5000/watchlist', {
          headers: { Authorization: `Bearer ${token}`}
        });
  
        const watchlistItems = response.data.watchlist || [];
        const movieId = getMovieId();
  
        // Checks whether the movie exists in watchlist
        const inWatchlist = watchlistItems.some(item => 
          (item.movie_id === movieId) || (parseInt(item.movie_id) === parseInt(movieId))
        );
        
        setIsInWatchlist(inWatchlist);
      } catch (error) {
        console.error("Error determining item status", error);
      }
    };
    
    checkWatchlistStatus();
  }, [movie]);

  // watchlist function
  const addToWatchlist = async (e) => {
    // prevents navigating to movie details if "add to watchlist" is clicked
    e.stopPropagation();
    
    // Don't do anything if already in watchlist
    if (isInWatchlist) {
      return;
    }
    
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      // Handles the missmatch between movie ids 
      const movieId = getMovieId();

      if (!movieId) {
        console.error("No valid movie id format for:", movie);
        alert("Error: Could not find the correct movie ID")
        return;
      }

      await axios.post('http://127.0.0.1:5000/watchlist', {
        movie_id: movieId,
        status: 'want_to_watch'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setIsInWatchlist(true);
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      alert('Failed to add to watchlist');
    } finally {
      setIsLoading(false);
    }
  };

  // Navigates to movie details page when card is clicked
  const handleCardClick = () => {
    const movieId = getMovieId();
    if (movieId) {
      navigate(`/movie/${movieId}`);
    } else{
      console.error("No valid ID found for this movie:", movie)
    }
  };

  return (
    <div className="movie-card" onClick={handleCardClick}> 
      <img
        src={movie.poster_path ? `${imgBaseURL}${movie.poster_path}` : "/images/no-poster.jpg"} 
        alt={movie.title}
      />
      {isNew() && <div className="movie-badge">NEW</div>}
      <div className="movie-info">
        <h3>{movie.title}</h3>
        <p>{movie.overview || "No description available."}</p>
        <div className="movie-meta">
          <div className="movie-genres">
            {movie.genres && movie.genres.length > 0 
              ? movie.genres.slice(0, 2).join(", ")
              : "Unknown"}
          </div>
          {movie.vote_average && (
            <div className="movie-rating">
              ★ {Number(movie.vote_average).toFixed(1)}
            </div>
          )}
        </div>
        <p><small>{formatDate(movie.release_date)}</small></p>      
        <div className="card-actions">
          <button 
            onClick={addToWatchlist} 
            className={`watchlist-btn ${isInWatchlist ? 'added' : ''}`}
            disabled={isLoading || isInWatchlist}
          >
            {isLoading ? 'Adding...' : isInWatchlist ? 'Added ✓' : 'Add to Watchlist'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Movie_Card;