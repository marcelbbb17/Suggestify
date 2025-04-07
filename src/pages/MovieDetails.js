import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useUser } from '../context/User_Context';
import '../styles/MovieDetails.css';

const MovieDetails = () => {
  const { movieId } = useParams();
  const { username } = useUser();
  const navigate = useNavigate();

  const [movie, setMovie] = useState(null);
  const [cast, setCast] = useState([]);
  const [director, setDirector] = useState(null);
  const [similarMovies, setSimilarMovies] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [watchlistStatus, setWatchlistStatus] = useState(null);
  const [userRating, setUserRating] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    const fetchMovieDetails = async () => {
      setIsLoading(true);
      setError(null);

      try {
        if (!movieId) {
          setError("Movie ID not found");
          setIsLoading(false);
          return;
        }

        const token = localStorage.getItem('token');
        if (!token) {
          navigate('/login');
          return;
        }

        // Fetch movie detail
        const movieResponse = await axios.get(`http://127.0.0.1:5000/proxy?url=${encodeURIComponent(`https://api.themoviedb.org/3/movie/${movieId}`)}&append_to_response=videos,images,keywords`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        // Fetch cast and crew information
        const creditsResponse = await axios.get(`http://127.0.0.1:5000/proxy?url=${encodeURIComponent(`https://api.themoviedb.org/3/movie/${movieId}/credits`)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        // Fetch similar movies
        const similarResponse = await axios.get(`http://127.0.0.1:5000/proxy?url=${encodeURIComponent(`https://api.themoviedb.org/3/movie/${movieId}/similar`)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        // Fetch reviews
        const reviewsResponse = await axios.get(`http://127.0.0.1:5000/proxy?url=${encodeURIComponent(`https://api.themoviedb.org/3/movie/${movieId}/reviews`)}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        // Check if movie is in user's watchlist
        try {
          const watchlistResponse = await axios.get(`http://127.0.0.1:5000/watchlist`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          // Checks if movie from watchlist is the same as current movie
          const watchlistItem = watchlistResponse.data.watchlist.find(item => item.movie_id === parseInt(movieId));
          if (watchlistItem) {
            setWatchlistStatus(watchlistItem.status);
            setUserRating(watchlistItem.user_rating || 0);
          }
        } catch (err) {
          console.error('Error checking watchlist status:', err);
        }

        // Process the responses
        setMovie(movieResponse.data);
        
        // Process cast (top 10 actors)
        setCast(creditsResponse.data.cast.slice(0, 10));
        
        // Find director
        const directorData = creditsResponse.data.crew.find(person => person.job === 'Director');
        setDirector(directorData);
        
        // Process similar movies (top 10)
        setSimilarMovies(similarResponse.data.results.slice(0, 10));
        
        // Process reviews
        setReviews(reviewsResponse.data.results);

      } catch (err) {
        console.error('Error fetching movie details:', err);
        setError('Failed to load movie details. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };

    if (movieId) {
      fetchMovieDetails();
      // Resets all states when naviagting to another movie
      return () => {
        setMovie(null);
        setCast([]);
        setDirector(null);
        setSimilarMovies([]);
        setReviews([]);
        setWatchlistStatus(null);
        setUserRating(0);
      };
    }
  }, [movieId, navigate]);

  const handleAddToWatchlist = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('http://127.0.0.1:5000/watchlist', {
        movie_id: parseInt(movieId),
        status: 'want_to_watch'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Default status is "want_to_watch"
      setWatchlistStatus('want_to_watch');
      alert('Added to watchlist!');
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      alert('Failed to add to watchlist');
    }
  };

  const handleUpdateWatchlist = async (status) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`http://127.0.0.1:5000/watchlist/${movieId}`, {
        status: status
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setWatchlistStatus(status);
      alert('Watchlist updated!');
    } catch (error) {
      console.error('Error updating watchlist:', error);
      alert('Failed to update watchlist');
    }
  };

  const handleRateMovie = async (rating) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`http://127.0.0.1:5000/watchlist/${movieId}`, {
        user_rating: rating
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setUserRating(rating);
      alert('Rating saved!');
    } catch (error) {
      console.error('Error rating movie:', error);
      alert('Failed to save rating');
    }
  };

  // Runtime of movies 
  const formatRuntime = (minutes) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  // Release date of movies
  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
  };

  // Currency for movies 
  const formatCurrency = (amount) => {
    if (!amount) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Gets the trailer for movie if it exists
  const getTrailerUrl = () => {
    if (!movie || !movie.videos || !movie.videos.results) return null;
    
    const trailer = movie.videos.results.find(
      video => video.type === 'Trailer' && video.site === 'YouTube'
    );
    
    return trailer ? `https://www.youtube.com/embed/${trailer.key}` : null;
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="movie-detail-page">
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
        <div className="loading-container">
          <div className="loading-spinner">Loading movie details...</div>
        </div>
      </div>
    );
  }

  // Error State
  if (error || !movie) {
    return (
      <div className="movie-detail-page">
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
        <div className="error-container">
          <p>{error || 'Failed to load movie details.'}</p>
          <button className="primary-button" onClick={() => navigate('/homepage')}>
            Back to Homepage
          </button>
        </div>
      </div>
    );
  }

  const trailerUrl = getTrailerUrl();

  return (
    <div className="movie-detail-page">
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

      {/* Movie section with movie background image */}
      <div 
        className="movie-backdrop" 
        style={{
          backgroundImage: movie.backdrop_path 
            ? `url(https://image.tmdb.org/t/p/original${movie.backdrop_path})` 
            : 'none'
        }}
      >
        <div className="backdrop-overlay">
          <div className="movie-hero-content">
            <div className="movie-poster-container">
              {movie.poster_path ? (
                <img 
                  src={`https://image.tmdb.org/t/p/w500${movie.poster_path}`} 
                  alt={movie.title} 
                  className="movie-poster"
                />
              ) : (
                <div className="movie-poster-placeholder">
                  No Poster Available
                </div>
              )}
            </div>
            
            <div className="movie-info-container">
              <h1 className="movie-title">
                {movie.title} 
                <span className="movie-year">
                  {movie.release_date ? `(${new Date(movie.release_date).getFullYear()})` : ''}
                </span>
              </h1>
              
              <div className="movie-meta">
                <span className="movie-rating">★ {movie.vote_average.toFixed(1)}</span>
                <span className="movie-runtime">{formatRuntime(movie.runtime)}</span>
                <span className="movie-release-date">{formatDate(movie.release_date)}</span>
              </div>
              
              <div className="movie-genres">
                {movie.genres.map(genre => (
                  <span key={genre.id} className="genre-tag">{genre.name}</span>
                ))}
              </div>
              
              <div className="movie-tagline">{movie.tagline}</div>
              
              <div className="movie-actions">
                {!watchlistStatus ? (
                  <button 
                    className="primary-button"
                    onClick={handleAddToWatchlist}
                  >
                    Add to Watchlist
                  </button>
                ) : (
                  <div className="watchlist-options">
                    <div className="watchlist-status">
                      Status: {
                        (() => {
                          if (watchlistStatus === 'want_to_watch') {
                            return 'Want to Watch'
                          } else if (watchlistStatus === "watching") {
                            return 'Watching'
                          }else {
                            return 'Watched'
                          }
                        })
                      }
                    </div>
                    <div className="status-buttons">
                      <button 
                        className={`status-btn ${watchlistStatus === 'want_to_watch' ? 'active' : ''}`}
                        onClick={() => handleUpdateWatchlist('want_to_watch')}
                      >
                        Want to Watch
                      </button>
                      <button 
                        className={`status-btn ${watchlistStatus === 'watching' ? 'active' : ''}`}
                        onClick={() => handleUpdateWatchlist('watching')}
                      >
                        Watching
                      </button>
                      <button 
                        className={`status-btn ${watchlistStatus === 'watched' ? 'active' : ''}`}
                        onClick={() => handleUpdateWatchlist('watched')}
                      >
                        Watched
                      </button>
                    </div>
                  </div>
                )}
                
                {watchlistStatus === 'watched' && (
                  <div className="rating-container">
                    <div className="rating-label">Your Rating:</div>
                    <div className="rating-stars">
                      {[...Array(10)].map((_, i) => (
                        <span 
                          key={i}
                          className={`star ${i < userRating ? 'filled' : ''}`}
                          onClick={() => handleRateMovie(i + 1)}
                        >
                          ★
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Tabs */}
      <div className="content-tabs">
        <button 
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`tab-button ${activeTab === 'cast' ? 'active' : ''}`}
          onClick={() => setActiveTab('cast')}
        >
          Cast & Crew
        </button>
        <button 
          className={`tab-button ${activeTab === 'media' ? 'active' : ''}`}
          onClick={() => setActiveTab('media')}
        >
          Media
        </button>
        <button 
          className={`tab-button ${activeTab === 'reviews' ? 'active' : ''}`}
          onClick={() => setActiveTab('reviews')}
        >
          Reviews
        </button>
        <button 
          className={`tab-button ${activeTab === 'similar' ? 'active' : ''}`}
          onClick={() => setActiveTab('similar')}
        >
          Similar Movies
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="overview-section">
              <h2>Overview</h2>
              <p className="overview-text">{movie.overview || 'No overview available.'}</p>
            </div>
            
            <div className="details-grid">
              <div className="detail-item">
                <h3>Status</h3>
                <p>{movie.status}</p>
              </div>
              
              <div className="detail-item">
                <h3>Original Language</h3>
                <p>{movie.original_language?.toUpperCase() || 'N/A'}</p>
              </div>
              
              <div className="detail-item">
                <h3>Budget</h3>
                <p>{formatCurrency(movie.budget)}</p>
              </div>
              
              <div className="detail-item">
                <h3>Revenue</h3>
                <p>{formatCurrency(movie.revenue)}</p>
              </div>
            </div>
            
            {movie.production_companies && movie.production_companies.length > 0 && (
              <div className="companies-section">
                <h3>Production Companies</h3>
                <div className="companies-list">
                  {movie.production_companies.map(company => (
                    <div key={company.id} className="company-item">
                      {company.logo_path ? (
                        <img 
                          src={`https://image.tmdb.org/t/p/w200${company.logo_path}`} 
                          alt={company.name}
                          className="company-logo"
                        />
                      ) : (
                        <div className="company-name-only">{company.name}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {movie.keywords && movie.keywords.keywords && movie.keywords.keywords.length > 0 && (
              <div className="keywords-section">
                <h3>Keywords</h3>
                <div className="keywords-list">
                  {movie.keywords.keywords.map(keyword => (
                    <span key={keyword.id} className="keyword-tag">{keyword.name}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Cast & Crew Tab */}
        {activeTab === 'cast' && (
          <div className="cast-tab">
            <div className="director-section">
              <h2>Director</h2>
              {director ? (
                <div className="director-info">
                  {director.profile_path ? (
                    <img 
                      src={`https://image.tmdb.org/t/p/w200${director.profile_path}`} 
                      alt={director.name}
                      className="director-image"
                    />
                  ) : (
                    <div className="profile-placeholder">No Image</div>
                  )}
                  <div className="director-name">{director.name}</div>
                </div>
              ) : (
                <p>Director information not available</p>
              )}
            </div>
            
            <div className="cast-section">
              <h2>Top Cast</h2>
              <div className="cast-grid">
                {cast.length > 0 ? cast.map(person => (
                  <div key={person.id} className="cast-card">
                    {person.profile_path ? (
                      <img 
                        src={`https://image.tmdb.org/t/p/w200${person.profile_path}`} 
                        alt={person.name}
                        className="cast-image"
                      />
                    ) : (
                      <div className="profile-placeholder">No Image</div>
                    )}
                    <div className="cast-info">
                      <div className="cast-name">{person.name}</div>
                      <div className="cast-character">{person.character}</div>
                    </div>
                  </div>
                )) : (
                  <p>Cast information not available</p>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* Media Tab */}
        {activeTab === 'media' && (
          <div className="media-tab">
            {trailerUrl && (
              <div className="trailer-section">
                <h2>Trailer</h2>
                <div className="trailer-container">
                  <iframe
                    src={trailerUrl}
                    title="Movie Trailer"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  ></iframe>
                </div>
              </div>
            )}
            
            {movie.images && movie.images.backdrops && movie.images.backdrops.length > 0 && (
              <div className="images-section">
                <h2>Images</h2>
                <div className="images-grid">
                  {movie.images.backdrops.slice(0, 9).map((image, index) => (
                    <img 
                      key={index}
                      src={`https://image.tmdb.org/t/p/w500${image.file_path}`}
                      alt={`${movie.title} backdrop ${index + 1}`}
                      className="backdrop-image"
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Reviews Tab */}
        {activeTab === 'reviews' && (
          <div className="reviews-tab">
            <h2>Reviews</h2>
            {reviews.length > 0 ? (
              <div className="reviews-list">
                {reviews.map(review => (
                  <div key={review.id} className="review-card">
                    <div className="review-header">
                      <div className="reviewer-info">
                        <div className="reviewer-name">{review.author}</div>
                        {review.author_details && review.author_details.rating && (
                          <div className="reviewer-rating">
                            ★ {review.author_details.rating}
                          </div>
                        )}
                      </div>
                      <div className="review-date">
                        {new Date(review.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="review-content">
                      <p>{review.content.length > 500 
                        ? `${review.content.substring(0, 500)}...` 
                        : review.content}
                      </p>
                      {review.content.length > 500 && (
                        <a 
                          href={review.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="read-more-link"
                        >
                          Read full review
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-reviews">
                <p>No reviews available for this movie.</p>
              </div>
            )}
          </div>
        )}
        
        {/* Similar Movies Tab */}
        {activeTab === 'similar' && (
          <div className="similar-tab">
            <h2>Similar Movies You Might Like</h2>
            {similarMovies.length > 0 ? (
              <div className="similar-grid">
                {similarMovies.map(movie => (
                  <div 
                    key={movie.id} 
                    className="similar-card"
                    onClick={() => navigate(`/movie/${movie.id}`)}
                  >
                    {movie.poster_path ? (
                      <img 
                        src={`https://image.tmdb.org/t/p/w200${movie.poster_path}`}
                        alt={movie.title}
                        className="similar-poster"
                      />
                    ) : (
                      <div className="similar-poster-placeholder">No Image</div>
                    )}
                    <div className="similar-info">
                      <div className="similar-title">{movie.title}</div>
                      <div className="similar-year">
                        {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
                      </div>
                      <div className="similar-rating">★ {movie.vote_average.toFixed(1)}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="no-similar">
                <p>No similar movies found.</p>
              </div>
            )}
          </div>
        )}
      </div>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default MovieDetails;