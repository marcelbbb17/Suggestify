import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from "react-router-dom";
import { useUser } from "../context/User_Context";
import axios from "axios";
import Movie_Card from "../components/Movie_Card";
import "../styles/Homepage.css";

function Homepage() {
  const { username } = useUser();
  const navigate = useNavigate();
  const [featuredMovies, setFeaturedMovies] = useState([]);
  const [trendingMovies, setTrendingMovies] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMoviesData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Fetch trending movies
        const trendingResponse = await axios.get(
          'http://127.0.0.1:5000/proxy?url=https://api.themoviedb.org/3/trending/movie/week&page=1',
          { headers: { Authorization: `Bearer ${token}` } }
        );

        // Fetch popular movies 
        const popularResponse = await axios.get(
          'http://127.0.0.1:5000/proxy?url=https://api.themoviedb.org/3/movie/popular&page=1',
          { headers: { Authorization: `Bearer ${token}` } }
        );

        // Set the data
        setTrendingMovies(trendingResponse.data.results?.slice(0, 6) || []);
        setFeaturedMovies(popularResponse.data.results?.slice(0, 8) || []);
      } catch (error) {
        console.error('Error fetching movies for homepage:', error);
        setError('Failed to load movies. Please try refreshing the page.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMoviesData();
  }, [navigate]);

  // Function to navigate to recommendations page
  const goToRecommendations = () => {
    navigate('/recommended');
  };

  // Function to navigate to movies page
  const browseAllMovies = () => {
    navigate('/movies');
  };

  return (
    <div className="homepage background">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><Link to="/movies">Movies</Link></li>
            <li><Link to="/recommended">Recommended</Link></li>
            <li><Link to="/watchlist">Watchlist</Link></li>
            <li><Link to="/profile">Profile</Link></li>
          </ul>
        </nav>
        <div className="username">
          <p>Hello, {username || ":("}</p>
        </div>
      </header>

      {/* Hero section */}
      <section className="main">
        <div className="main-content">
          <h1>Welcome to Suggestify</h1>
          <p>Discover personalised recommendations, trending films, and build your watchlist</p>
          <div className="hero-buttons">
            <button className="primary-btn" onClick={goToRecommendations}>View Your Recommendations</button>
            <button className="secondary-btn" onClick={browseAllMovies}>Browse All Movies</button>
          </div>
        </div>
      </section>

      {/* Content sections */}
      {isLoading ? (
        <div className="loading-section">
          <div className="loading-spinner"></div>
          <p>Loading content...</p>
        </div>
      ) : error ? (
        <div className="error-section">
          <p>{error}</p>
          <button onClick={() => window.location.reload()} className="retry-btn">Try Again</button>
        </div>
      ) : (
        <>
          {/* Popular Movies Section */}
          <section id="popular" className="movies-section">
            <div className="section-header">
              <h2>Popular Movies</h2>
              <Link to="/movies" className="see-all-link">See All</Link>
            </div>
            <div className="movie-grid">
              {featuredMovies.map(movie => (
                <Movie_Card key={movie.id} movie={movie} />
              ))}
            </div>
          </section>

          {/* Trending Movies Section */}
          <section id="trending" className="movies-section">
            <div className="section-header">
              <h2>Trending Now</h2>
              <Link to="/movies" className="see-all-link">See All</Link>
            </div>
            <div className="movie-grid">
              {trendingMovies.map(movie => (
                <Movie_Card key={movie.id} movie={movie} />
              ))}
            </div>
          </section>

          {/* Quick Links Section */}
          <section className="quick-links-section">
            <div className="quick-link-card">
              <div className="quick-link-icon">🎬</div>
              <h3>Your Watchlist</h3>
              <p>Track movies you want to watch and those you've already seen</p>
              <Link to="/watchlist" className="quick-link-btn">Go to Watchlist</Link>
            </div>
            
            <div className="quick-link-card">
              <div className="quick-link-icon">🎯</div>
              <h3>Personalised Recommendations</h3>
              <p>Discover movies tailored just for you based on your preferences</p>
              <Link to="/recommended" className="quick-link-btn">View Recommendations</Link>
            </div>
            
            <div className="quick-link-card">
              <div className="quick-link-icon">🔍</div>
              <h3>Find Movies</h3>
              <p>Search and browse through our extensive collection of films</p>
              <Link to="/movies" className="quick-link-btn">Browse Movies</Link>
            </div>
          </section>
        </>
      )}

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Homepage;