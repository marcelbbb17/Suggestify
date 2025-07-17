import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";
import { API_BASE_URL } from '../index';

const WatchlistContext = createContext();

// Provider components
export function WatchlistProvider({ children }) {
  const [watchlistItems, setWatchlistItems] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastFetched, setLastFetched] = useState(null);

  // Function to fetch the watchlist
  const fetchWatchlist = async (force = false) => {
    // Ifd we've fetche the watchlist in the last minute and force is false, don't fetch again
    if (
      !force && 
      lastFetched && 
      Date.now() - lastFetched < 60000
    ) {
      return watchlistItems;
    }

    setIsLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setWatchlistItems([]);
        setIsLoading(false);
        return [];
      }
      
      const response = await axios.get(`${API_BASE_URL}/watchlist`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const items = response.data.watchlist || [];
      setWatchlistItems(items);
      setLastFetched(Date.now());
      return items;
    } catch (error) {
      console.error("Error fetching watchlist:", error);
      return [];
    } finally {
      setIsLoading(false);
    }
  };

  // Check if a movie is in the watchlist
  const isInWatchlist = (movieId) => {
    if (!movieId) return false;
    
    return watchlistItems.some(item => 
      (item.movie_id === movieId) || 
      (parseInt(item.movie_id) === parseInt(movieId))
    );
  };

  // Add a movie to the watchlist
  const addToWatchlist = async (movieId, status = 'want_to_watch', notes = '') => {
    if (!movieId) return false;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;
      
      await axios.post(`${API_BASE_URL}/watchlist`, {
        movie_id: movieId,
        status,
        notes
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh the watchlist
      await fetchWatchlist(true);
      return true;
    } catch (error) {
      console.error("Error adding to watchlist:", error);
      return false;
    }
  };

  // Remove a movie from the watchlist
  const removeFromWatchlist = async (movieId) => {
    if (!movieId) return false;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;
      
      await axios.delete(`${API_BASE_URL}/watchlist/${movieId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh the watchlist
      await fetchWatchlist(true);
      return true;
    } catch (error) {
      console.error("Error removing from watchlist:", error);
      return false;
    }
  };

  // Update a movie in the watchlist
  const updateWatchlistItem = async (movieId, updates) => {
    if (!movieId) return false;
    
    try {
      const token = localStorage.getItem('token');
      if (!token) return false;
      
      await axios.put(`${API_BASE_URL}/watchlist/${movieId}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh the watchlist
      await fetchWatchlist(true);
      return true;
    } catch (error) {
      console.error("Error updating watchlist item:", error);
      return false;
    }
  };

  // Fetch watchlist 
  useEffect(() => {
    fetchWatchlist();
    
    // Refreshes watchlist every 5 min
    const interval = setInterval(() => {
      fetchWatchlist(true);
    }, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const value = {
    watchlistItems,
    isLoading,
    fetchWatchlist,
    isInWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    updateWatchlistItem
  };

  return (
    <WatchlistContext.Provider value={value}>
      {children}
    </WatchlistContext.Provider>
  );
}

export function useWatchlist() {
  return useContext(WatchlistContext);
}