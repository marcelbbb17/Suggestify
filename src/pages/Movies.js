import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useUser } from '../context/User_Context';
import Movie_Card from '../components/Movie_Card';
import '../styles/Movies.css';

const Movies = () => {
  const { username } = useUser();
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('trending');
  const [movies, setMovies] = useState({
    trending: [],
    popular: [],
    topRated: [],
    upcoming: []
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Search functionality
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [showSearchResults, setShowSearchResults] = useState(false);

  useEffect(() => {
    // Get movies for different categories based on what user clicks on 
    const fetchMovies = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Token Validation
        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Different categories 
        const categories = {
          trending: 'https://api.themoviedb.org/3/trending/movie/week',
          popular: 'https://api.themoviedb.org/3/movie/popular',
          topRated: 'https://api.themoviedb.org/3/movie/top_rated',
          upcoming: 'https://api.themoviedb.org/3/movie/upcoming'
        };

        // Get data for each category
        const requests = Object.entries(categories).map(async ([category, endpoint]) => {
          const response = await axios.get(`http://127.0.0.1:5000/proxy?url=${encodeURIComponent(endpoint)}&page=1`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          return { category, data: response.data.results || [] };
        });

        const results = await Promise.all(requests);

        if (results.length > 0 && results[0].data.length > 0) {
          console.log("Movie data from API:", results[0].data[0])
        }
        
        // Get and update results 
        const newMoviesState = { ...movies };
        results.forEach(({ category, data }) => {
          newMoviesState[category] = data;
        });

        setMovies(newMoviesState);
      } catch (err) {
        console.error('Error fetching movies:', err);
        setError('Failed to load movies. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchMovies();
  }, [navigate]);

  const handleCategoryChange = (category) => {
    setActiveCategory(category);
    // Clear search results when changing categories
    setShowSearchResults(false);
    setSearchQuery("");
  };

  // Handle search functionality
  const handleSearch = async (e) => {
    e.preventDefault();

    // If search query is empty return nothing
    if (!searchQuery.trim()) {
      return;
    }

    setIsSearching(true);
    setShowSearchResults(true);
    setSearchError("");

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`http://127.0.0.1:5000/search?query=${encodeURIComponent(searchQuery)}`, {
        headers: {Authorization: `Bearer ${token}`}
      });
      const results = response.data.results || [];
      setSearchResults(results);
    } 
    catch (error) {
      setSearchError("Failed to search for movie");
      setSearchResults([]);
    }
    finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery("");
    setSearchResults([]);
    setShowSearchResults(false);
  };

  // Get the movies based on category selected or search results
  const displayedMovies = showSearchResults ? searchResults : movies[activeCategory] || [];

  return (
    <div className="movies-page">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><Link to="/homepage">Home</Link></li>
            <li><Link to="/recommended">Recommended</Link></li>
            <li><Link to="/watchlist">Watchlist</Link></li>
            <li><Link to="/profile">Profile</Link></li>
          </ul>
        </nav>
        <div className="username">
          <p>Hello, {username || ":("}</p>
        </div>
      </header>

      <div className="movies-hero">
        <div className="hero-content">
          <h1>Discover Movies</h1>
          <p>Explore trending, popular, and critically acclaimed films</p>
          
          {/* Search bar */}
          <form onSubmit={handleSearch} className="search-form">
            <input
              type="text"
              className="search-bar"
              placeholder="Search for movies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="submit-button" id='search-button'>Search</button>
            {showSearchResults && (
              <button type="button" className="clear-button" onClick={clearSearch}>Clear</button>
            )}
          </form>
        </div>
      </div>

      {!showSearchResults && (
        <div className="categories-container">
          <div className="category-tabs">
            <button 
              className={activeCategory === 'trending' ? 'category-tab active' : 'category-tab'}
              onClick={() => handleCategoryChange('trending')}
            >
              Trending
            </button>
            <button 
              className={activeCategory === 'popular' ? 'category-tab active' : 'category-tab'}
              onClick={() => handleCategoryChange('popular')}
            >
              Popular
            </button>
            <button 
              className={activeCategory === 'topRated' ? 'category-tab active' : 'category-tab'}
              onClick={() => handleCategoryChange('topRated')}
            >
              Top Rated
            </button>
            <button 
              className={activeCategory === 'upcoming' ? 'category-tab active' : 'category-tab'}
              onClick={() => handleCategoryChange('upcoming')}
            >
              Upcoming
            </button>
          </div>
        </div>
      )}

      <div className="movies-content">
        {/* Show search results header if searching */}
        {showSearchResults && (
          <div className="search-results-header">
            <h2>Search Results</h2>
            {searchResults.length > 0 && (
              <p>Found {searchResults.length} results for "{searchQuery}"</p>
            )}
          </div>
        )}

        {isSearching ? (
          <div className="loading-indicator">
            <p>Searching for movies...</p>
          </div>
        ) : isLoading ? (
          <div className="loading-indicator">
            <p>Loading movies...</p>
          </div>
        ) : error ? (
          <div className="error-message">
            <p>{error}</p>
            <button className="retry-btn" onClick={() => window.location.reload()}>
              Try Again
            </button>
          </div>
        ) : showSearchResults && searchError ? (
          <div className="error-message">
            <p>{searchError}</p>
          </div>
        ) : showSearchResults && searchResults.length === 0 ? (
          <div className="no-movies">
            <p>No movies found matching your search.</p>
          </div>
        ) : displayedMovies.length === 0 ? (
          <div className="no-movies">
            <p>No movies available in this category.</p>
          </div>
        ) : (
          <div className="movies-grid">
            {displayedMovies.map(movie => (
              <div key={movie.id} className="movie-card-wrapper" onClick={() => navigate(`/movie/${movie.id}`)}>
                <Movie_Card movie={movie} />
              </div>
            ))}
          </div>
        )}
      </div>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Movies;