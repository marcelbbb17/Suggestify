import React, { useState } from 'react';
import { Link } from "react-router-dom";
import {useUser} from "../context/User_Context";
import axios from "axios";
import Movie_Card from "../components/Movie_Card";

function Homepage() {
  const {username} = useUser();
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");
  const [showResults, setShowResults] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault()

    // If search query is empy return nothing
    if (!searchQuery.trim()) {
      return;
    }

    setIsSearching(true)
    setShowResults(true)
    setSearchError("")

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
    setShowResults(false)
  }
  
  return (
    /* Basic Structure for logged in homepage */   
    <div className="background">
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
          {/* Displays user username */}
          <p>Hello, {username || ":("}</p>
        </div>
      </header>
  
      <section className="main">
        <div className="main-content">
          <h1>Discover Your Next Favorite Movie</h1>
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="search-form">
            <input
              type="text"
              className="search-bar"
              placeholder="Search for movies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" className="submit-button" id='search-button'>Search</button>
            {showResults && (
              <button type="button" className="submit-button" onClick={clearSearch}> clear </button>
            )}
          </form>
        </div>
      </section>

      {/* Search results after user searches for movies */}
      {showResults && (
        <section className="search-results">
          <div className="search-results-header">
            <h2>Search Results</h2>
            {searchResults.length > 0 && (
              <p>Found {searchResults.length} results for "{searchQuery}"</p>
            )}
          </div>
          
          {isSearching ? (
            <div className="loading">Searching...</div>
          ) : searchError ? (
            <div className="error">{searchError}</div>
          ) : searchResults.length === 0 ? (
            <div className="no-results">No movies found matching your search.</div>
          ) : (
            <div className="search-grid">
              {searchResults.map(movie => (
                <Movie_Card key={movie.id} movie={movie} />
              ))}
            </div>
          )}
        </section>
      )}
  
      <section id="recommended" className="movies-section">
        <h2>Recommended For You</h2>
        <div className="movie-grid">
          <div className="movie">Movie 1</div>
          <div className="movie">Movie 2</div>
          <div className="movie">Movie 3</div>
          <div className="movie">Movie 4</div>
        </div>
      </section>
  
      <section id="trending" className="movies-section">
        <h2>Trending Movies</h2>
        <div className="movie-grid">
          <div className="movie">Movie 5</div>
          <div className="movie">Movie 6</div>
          <div className="movie">Movie 7</div>
          <div className="movie">Movie 8</div>
        </div>
      </section>
  
      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Homepage;