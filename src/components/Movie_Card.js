import React from 'react';
import "../styles/Movie_Card.css";
import axios from 'axios';
import { useNavigate } from 'react-router-dom'; 

const Movie_Card = ({ movie }) => {
  const imgBaseURL = "https://image.tmdb.org/t/p/w500"; 
  const navigate = useNavigate(); 
  console.log("Movie card received movie:", movie);  
  console.log("Movie ID in card:", movie?.movie_id); 
  
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

  // watchlist function
  const addToWatchlist = async (e) => {
    // prevents navigating to movie details if "add to watchlist" is clicked
    e.stopPropagation();
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://127.0.0.1:5000/watchlist', {
        movie_id: movie.movie_id,
        status: 'want_to_watch'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('Added to watchlist!');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      alert('Failed to add to watchlist');
    }
  };

  // Navigates to movie details page when card is clicked
  const handleCardClick = () => {
    if (movie.movie_id) {
      navigate(`/movie/${movie.movie_id}`);
    } else if (movie.id) {
      navigate(`/movie/${movie.id}`);
    } else {
      console.error("No valid ID found for this movie:", movie);
    }
  };

  return (
    <div className="movie-card" onClick={handleCardClick}> 
      <img
        src={movie.poster_path ? `${imgBaseURL}${movie.poster_path}` : "If it fails it fails"} 
        alt={movie.title}
      />
      {isNew() && <div className="movie-badge">NEW</div>}
      <div className="movie-info">
        <h3>{movie.title}</h3>
        <p>{movie.overview || "No description available."}</p>
        <div className="movie-meta">
          <div className="movie-genres">
            {movie.genres && movie.genres.length > 0 
              ? movie.genres.slice(0, 2).join(", ") || movie.genres.name.slice(0,2).join(", ") 
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
          <button onClick={addToWatchlist} className="watchlist-btn">
            Add to Watchlist
          </button>
        </div>
      </div>
    </div>
  );
};

export default Movie_Card;