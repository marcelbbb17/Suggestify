import React from 'react';
import "../styles/Movie_Card.css";

const Movie_Card = ({ movie }) => {
  const imgBaseURL = "https://image.tmdb.org/t/p/w500"; 
  
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

  return (
    <div className="movie-card">
      <img
        src={movie.poster_path ? `${imgBaseURL}${movie.poster_path}` : "If it fails it fails"} // Add a fallback image later
        alt={movie.title}
      />
      {isNew() && <div className="movie-badge">NEW</div>}
      <div className="movie-info">
        <h3>{movie.title}</h3>
        <p>{movie.overview || "No description available."}</p>
        <div className="movie-meta">
          <div className="movie-genres">
            {movie.genres && movie.genres.length > 0 
            // Two genre because the card is small
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
      </div>
    </div>
  );
};

export default Movie_Card;