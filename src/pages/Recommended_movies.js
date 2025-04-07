import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';
import MovieCard from '../components/Movie_Card';
import {useUser} from "../context/User_Context";
import '../styles/Recommended_movies.css';

const Recommended_movies = () => {
  const {username} = useUser();
  const [movies, setMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const hasRequestedRef = useRef(false)

  useEffect(() => {
    const fetchRecommendations = async () => {
      // Prevents call the /recommend endpoint twice
      if (isLoading || hasRequestedRef.current) {
        return;
      }
      
      setIsLoading(true);
      hasRequestedRef.current = true;
      setError(null);
      
      try {
        console.log("Fetching recommended movies...");
        const token = localStorage.getItem("token");
        const response = await axios.get("http://127.0.0.1:5000/recommend", {
          headers: { Authorization: `Bearer ${token}` },
        });
        console.log("Response data:", response.data);
        setMovies(response.data.recommended_movies || []);
      } catch (error) {
        console.error("Error fetching recommendations:", error);
        setError("Oops! It looks like your recommendations aren't available yet. Complete the questionnaire to unlock your personalised movie list");
      } finally {
        setIsLoading(false);
      }
    };
  
    fetchRecommendations();

  }, []);

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

      <section className="recommendations-section">
        {isLoading ? (
          <div className="loading-spinner">
            <p>Loading your recommendations...</p>
          </div>
        ) : error ? (
          <div className="error-message">
            <p>{error}</p>
            <button 
              className="retry-btn"
              onClick={() => window.location.reload()}
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
                  <MovieCard key={movie.id} movie={movie} />
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
        </div>
      </div>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Recommended_movies;