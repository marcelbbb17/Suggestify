import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from "react-router-dom";
import axios from 'axios';
import { useUser } from "../context/User_Context";
import '../styles/Watchlist.css';
import { API_BASE_URL } from '../index';

function Watchlist() {
  const { username } = useUser();
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [editMode, setEditMode] = useState(null);
  const [editedItem, setEditedItem] = useState({});

  // Status options for each movie in watch list
  const statusOptions = [
    { value: 'want_to_watch', label: 'Want to Watch' },
    { value: 'watching', label: 'Currently Watching' },
    { value: 'watched', label: 'Watched' }
  ];

  // Navigates to moviedetail page if clicked on 
  const handleMovieClick = (movieId, e) => {
    // Does not navigate if in edit mode
    if (editMode === null && 
        e.target.tagName !== 'BUTTON' && 
        !e.target.closest('button')) {
      navigate(`/movie/${movieId}`);
    }
  };

  // Load watchlist 
  useEffect(() => {
    fetchWatchlist();
  }, []);

  // Loads watchlist from database through /watchlist endpoint
  const fetchWatchlist = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE_URL}/watchlist`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.watchlist) {
        setWatchlist(response.data.watchlist);
      } else {
        setWatchlist([]);
      }
    } catch (err) {
      console.error('Error fetching watchlist:', err);
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to load your watchlist. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Filter watchlist by status
  const filterWatchlist = (status) => {
    setActiveFilter(status);
  };

  let filteredWatchlist = [];
  if (activeFilter === 'all') {
    filteredWatchlist = watchlist;
  } else {
    filteredWatchlist = watchlist.filter(item => item.status === activeFilter);
  }

  // Date of when user add to watchlist
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Edit mode 
  const handleEdit = (item, e) => {
    // Prevents navigation when clicking edit
    e.stopPropagation();
    setEditMode(item.id);
    
    let initialEditState = {
      status: item.status
    };
    
    if (item.user_rating) {
      initialEditState.user_rating = item.user_rating;
    } else {
      initialEditState.user_rating = '';
    }
    
    if (item.notes) {
      initialEditState.notes = item.notes;
    } else {
      initialEditState.notes = '';
    }
    
    setEditedItem(initialEditState);
  };

  // Cancel edit mode
  const cancelEdit = (e) => {
    e.stopPropagation();
    setEditMode(null);
    setEditedItem({});
  };

  // Save edited watchlist 
  const saveEdit = async (movieId, e) => {
    e.stopPropagation();
    
    try {
      // Updates changes made in database
      const token = localStorage.getItem('token');
      await axios.put(`${API_BASE_URL}/watchlist/${movieId}`, editedItem, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Updates visually for user 
      const updatedWatchlist = watchlist.map(item => {
        if (item.movie_id === movieId) {
          return { ...item, ...editedItem };
        } else {
          return item;
        }
      });
      setWatchlist(updatedWatchlist);
      setEditMode(null);
    } catch (err) {
      console.error('Error updating watchlist item:', err);
      let errorMessage = 'Failed to update item';
      if (err.response && err.response.data && err.response.data.error) {
        errorMessage = err.response.data.error;
      }
      alert(errorMessage);
    }
  };

  // Remove movie from watchlist
  const removeFromWatchlist = async (movieId, e) => {
    e.stopPropagation();   
    const confirmed = window.confirm('Are you sure you want to remove this movie from your watchlist?');
    if (!confirmed) {
      return;
    }
    
    try {
      // Deletes item from database 
      const token = localStorage.getItem('token');
      await axios.delete(`${API_BASE_URL}/watchlist/${movieId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Deletes item visually for user
      const updatedWatchlist = watchlist.filter(item => item.movie_id !== movieId);
      setWatchlist(updatedWatchlist);
    } catch (err) {
      console.error('Error removing from watchlist:', err);
      let errorMessage = 'Failed to remove movie from watchlist';
      if (err.response && err.response.data && err.response.data.error) {
        errorMessage = err.response.data.error;
      }
      alert(errorMessage);
    }
  };

  // Handles changes to the edited item form
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    const updatedItem = {
      ...editedItem,
      [name]: value
    };
    setEditedItem(updatedItem);
    e.stopPropagation();
  };

  // Get the label for a status value
  const getStatusLabel = (statusValue) => {
    for (let i = 0; i < statusOptions.length; i++) {
      if (statusOptions[i].value === statusValue) {
        return statusOptions[i].label;
      }
    }
    return 'Want to Watch'; // Default 
  };

  // Message for user with empty watchlist
  let emptyWatchlistMessage = '';
  if (activeFilter === 'all') {
    emptyWatchlistMessage = "Your watchlist is empty";
  } else {
    const filterLabel = getStatusLabel(activeFilter);
    emptyWatchlistMessage = `No movies in "${filterLabel}" category`;
  }

  // Messages for empty watchlist
  let emptyWatchlistInstructions = '';
  if (activeFilter === 'all') {
    emptyWatchlistInstructions = "Add movies from recommendations or search for movies that interest you";
  } else {
    emptyWatchlistInstructions = "Try a different filter or add more movies to your watchlist";
  }

  return (
    <div className="background watchlist-page">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><Link to="/movies">Movies</Link></li>
            <li><Link to="/recommended">Recommended</Link></li>
            <li><Link to="/profile">Profile</Link></li>
            <li><Link to="/homepage">Home</Link></li>
          </ul>
        </nav>
        <div className="username">
          <p>Hello, {username || ":("}</p>
        </div>
      </header>

      <div className="watchlist-hero">
        <div className="hero-content">
          <h1>Your Watchlist</h1>
          <p>Keep track of what you've watched and what you want to watch next</p>
        </div>
      </div>

      <div className="watchlist-container">
        {/* Status filter buttons */}
        <div className="filter-container">
          <h3>Filter by Status:</h3>
          <div className="status-filters">
            <button 
              className={activeFilter === 'all' ? 'filter-btn active' : 'filter-btn'}
              onClick={() => filterWatchlist('all')}
            >
              All
            </button>
            {statusOptions.map(option => (
              <button 
                key={option.value}
                className={activeFilter === option.value ? 'filter-btn active' : 'filter-btn'}
                onClick={() => filterWatchlist(option.value)}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Main watchlist content */}
        <div className="watchlist-content">
          {/* Loading state */}
          {loading && (
            <div className="loading-indicator">
              <p>Loading your watchlist...</p>
            </div>
          )}
          
          {/* Error state */}
          {!loading && error && (
            <div className="error-message">
              <p>{error}</p>
              <button className="retry-btn" onClick={fetchWatchlist}>
                Try Again
              </button>
            </div>
          )}
          
          {/* Empty watchlist */}
          {!loading && !error && filteredWatchlist.length === 0 && (
            <div className="empty-watchlist">
              <h3>{emptyWatchlistMessage}</h3>
              <p>{emptyWatchlistInstructions}</p>
              <Link to="/recommended" className="browse-btn">
                Browse Recommendations
              </Link>
            </div>
          )}
          
          {/* Watchlist items */}
          {!loading && !error && filteredWatchlist.length > 0 && (
            <div className="watchlist-items">
              {filteredWatchlist.map(item => (
                <div 
                  key={item.id} 
                  className={`watchlist-item ${item.status}`}
                  onClick={(e) => handleMovieClick(item.movie_id, e)}
                  style={{ cursor: editMode === null ? 'pointer' : 'default' }}
                >
                  <div className="movie-poster">
                    {item.poster_path ? (
                      <img 
                        src={`https://image.tmdb.org/t/p/w200${item.poster_path}`} 
                        alt={item.movie_title} 
                      />
                    ) : (
                      <div className="no-poster">No Image</div>
                    )}
                  </div>
                  
                  <div className="movie-details">
                    <h3>{item.movie_title}</h3>
                    <div className="movie-meta">
                      <span className="release-date">
                        {item.release_date ? item.release_date.substring(0, 4) : 'N/A'}
                      </span>
                      <span className="genres">
                        {Array.isArray(item.genres) && item.genres.slice(0, 3).join(', ')}
                      </span>
                    </div>
                    <p className="overview">{item.overview}</p>
                    
                    {/* Edit mode */}
                    {editMode === item.id && (
                      <div className="edit-form" onClick={(e) => e.stopPropagation()}>
                        <div className="form-group">
                          <label>Status:</label>
                          <select 
                            name="status" 
                            value={editedItem.status || 'want_to_watch'}
                            onChange={handleInputChange}
                          >
                            {statusOptions.map(option => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                        </div>
                        
                        <div className="form-group">
                          <label>Your Rating (0-10):</label>
                          <input 
                            type="number" 
                            name="user_rating"
                            min="0"
                            max="10"
                            step="0.1"
                            value={editedItem.user_rating || ''}
                            onChange={handleInputChange}
                          />
                        </div>
                        
                        <div className="form-group">
                          <label>Notes:</label>
                          <textarea 
                            name="notes"
                            value={editedItem.notes || ''}
                            onChange={handleInputChange}
                            rows="2"
                          ></textarea>
                        </div>
                        
                        <div className="edit-actions">
                          <button 
                            className="save-btn"
                            onClick={(e) => saveEdit(item.movie_id, e)}
                          >
                            Save
                          </button>
                          <button 
                            className="cancel-btn"
                            onClick={cancelEdit}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    )}
                    
                    {/* View mode */}
                    {editMode !== item.id && (
                      <div className="item-info">
                        <div className="status-badge">
                          {getStatusLabel(item.status)}
                        </div>
                        
                        {item.user_rating && (
                          <div className="user-rating">
                            <span className="rating-label">Your Rating:</span>
                            <span className="rating-value">{item.user_rating}/10</span>
                          </div>
                        )}
                        
                        {item.notes && (
                          <div className="notes">
                            <span className="notes-label">Notes:</span>
                            <p>{item.notes}</p>
                          </div>
                        )}
                        
                        <div className="date-added">
                          Added {formatDate(item.date_added)}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Item actions */}
                  {editMode !== item.id && (
                    <div className="item-actions">
                      <button 
                        className="edit-btn"
                        onClick={(e) => handleEdit(item, e)}
                      >
                        Edit
                      </button>
                      <button 
                        className="remove-btn"
                        onClick={(e) => removeFromWatchlist(item.movie_id, e)}
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Watchlist;