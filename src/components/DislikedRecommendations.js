import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useUser } from '../context/User_Context';
import MovieCard from '../components/Movie_Card'; 
import '../styles/DislikedRecommendations.css';

const DislikedRecommendations = () => {
  const { username } = useUser();
  const [dislikedMovies, setDislikedMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDislikedMovies = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setError("You need to be logged in to view this page");
          setIsLoading(false);
          return;
        }

        const response = await axios.get('http://127.0.0.1:5000/disliked-recommendations', {
          headers: { Authorization: `Bearer ${token}` }
        });

        // Fetch additional movie details for each disliked movie
        const dislikedData = response.data.disliked_movies || [];
        const enhancedMovies = await Promise.all(
          dislikedData.map(async (movie) => {
            try {
              // Fetch additional movie details from your proxy endpoint
              const movieDetails = await axios.get(
                `http://127.0.0.1:5000/proxy?url=${encodeURIComponent(`https://api.themoviedb.org/3/movie/${movie.movie_id}`)}`,
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              // Combine the disliked info with the full movie details
              return {
                ...movieDetails.data,
                ...movie,
                id: movie.movie_id, 
                vote_average: movieDetails.data.vote_average,
                poster_path: movieDetails.data.poster_path,
                overview: movieDetails.data.overview,
                disliked_date: movie.feedback_date
              };
            } catch (error) {
              console.error(`Error fetching details for movie ${movie.movie_id}:`, error);
              // Return the basic movie info if we can't get details
              return {
                ...movie,
                id: movie.movie_id,
                title: movie.title,
                overview: "Details unavailable",
                disliked_date: movie.feedback_date
              };
            }
          })
        );

        setDislikedMovies(enhancedMovies);
      } catch (err) {
        console.error('Error fetching disliked movies:', err);
        setError('Failed to load your disliked recommendations.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDislikedMovies();
  }, []);

  // Function to remove a movie from disliked list 
  const removeFromDisliked = async (movieId) => {
    try {
      const token = localStorage.getItem('token');
      
      // Update the feedback to 'neutral'
      await axios.post('http://127.0.0.1:5000/recommendation-feedback', {
        movie_id: movieId,
        feedback: 'neutral'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Update the UI by removing this movie
      setDislikedMovies(dislikedMovies.filter(movie => movie.id !== movieId && movie.movie_id !== movieId));
      
      alert('Movie removed from your disliked list');
    } catch (error) {
      console.error('Error removing from disliked list:', error);
      alert('Failed to update your preferences');
    }
  };

  return (
    <div className="disliked-page">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><Link to="/homepage">Home</Link></li>
            <li><Link to="/recommended">Recommendations</Link></li>
            <li><Link to="/watchlist">Watchlist</Link></li>
            <li><Link to="/profile">Profile</Link></li>
          </ul>
        </nav>
        <div className="username">
          <p>Hello, {username || ":("}</p>
        </div>
      </header>

      <div className="disliked-hero">
        <div className="hero-content">
          <h1>Movies You Didn't Like</h1>
          <p>We won't recommend similar movies in the future</p>
        </div>
      </div>

      <div className="disliked-content">
        {isLoading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <div className="loading-spinner-text">Loading your disliked movies...</div>
          </div>
        ) : error ? (
          <div className="error-message">
            <p>{error}</p>
          </div>
        ) : dislikedMovies.length > 0 ? (
          <div className="disliked-section">
            <div className="section-header">
              <p className="info-text">
                These are movies you've indicated you didn't like. We're using this information
                to avoid recommending similar movies to you in the future.
              </p>
            </div>
            
            <div className="disliked-grid">
              {dislikedMovies.map(movie => (
                <div key={movie.id || movie.movie_id} className="disliked-card-container">
                  <MovieCard movie={movie} />
                  <button 
                    className="remove-dislike-btn"
                    onClick={() => removeFromDisliked(movie.id || movie.movie_id)}
                  >
                    Remove from Disliked
                  </button>
                  <div className="disliked-info">
                    <span className="dislike-date">Disliked on: {new Date(movie.disliked_date).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="refresh-note">
              <h3>When will my recommendations update?</h3>
              <p>
                We automatically refresh your recommendations based on this feedback.
                You'll see the effects the next time you visit your recommendation page.
              </p>
              <Link to="/recommended" className="btn-primary">
                Go to Recommendations
              </Link>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <h2>No Disliked Movies</h2>
            <p>
              You haven't disliked any recommended movies yet. When you find a recommendation
              that isn't right for you, you can mark it with a thumbs down to help us
              improve your future recommendations.
            </p>
            <Link to="/recommended" className="btn-primary">
              View Your Recommendations
            </Link>
          </div>
        )}
      </div>
      
      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default DislikedRecommendations;