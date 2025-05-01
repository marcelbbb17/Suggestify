import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { useUser } from '../context/User_Context';
import '../styles/RecommendationInsights.css';

const RecommendationInsights = () => {
  const { username } = useUser();
  const [explanations, setExplanations] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedFactors, setSelectedFactors] = useState({});

  useEffect(() => {
    const fetchExplanations = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setError("Authentication required");
          setIsLoading(false);
          return;
        }
        
        const response = await axios.get(
          'http://127.0.0.1:5000/recommendation-explanations',
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        setExplanations(response.data.explanations || []);
      } catch (err) {
        console.error('Error fetching recommendation explanations:', err);
        setError('Failed to load recommendation insights. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchExplanations();
  }, []);

  const toggleFactorVisibility = (movieId) => {
    setSelectedFactors(prev => ({
      ...prev,
      [movieId]: !prev[movieId]
    }));
  };

  // Analyse overall factors that influenced recommendations
  const analyseOverallFactors = () => {
    if (!explanations.length) return null;
    
    const factorCounts = {};
    let totalMovies = explanations.length;
    
    // Count each factor's influence across all recommendations
    explanations.forEach(exp => {
      const aspects = exp.aspects || {};
      
      Object.entries(aspects).forEach(([factor, value]) => {
        // Only count significant factors 
        if (value > 0.05) {
          if (!factorCounts[factor]) {
            factorCounts[factor] = {
              count: 0,
              totalValue: 0
            };
          }
          
          factorCounts[factor].count += 1;
          factorCounts[factor].totalValue += value;
        }
      });
    });
    
    // Convert to array for sorting
    const factorArray = Object.entries(factorCounts).map(([factor, data]) => ({
      factor,
      count: data.count,
      percentage: (data.count / totalMovies) * 100,
      avgStrength: data.totalValue / data.count
    }));
    
    // Sort by how often the factor appears
    factorArray.sort((a, b) => b.count - a.count);
    
    return (
      <div className="overall-factors">
        <h3>What Influences Your Recommendations</h3>
        <div className="factors-grid">
          {factorArray.slice(0, 5).map(factor => (
            <div key={factor.factor} className="factor-card">
              <div className="factor-name">
                {factor.factor.replace(/_/g, ' ').replace(/boost|score/g, '').trim()}
              </div>
              <div className="factor-stats">
                <div className="factor-percentage">
                  {Math.round(factor.percentage)}% of recommendations
                </div>
                <div className="factor-strength" 
                  style={{
                    backgroundColor: getStrengthColor(factor.avgStrength)
                  }}>
                  {getStrengthLabel(factor.avgStrength)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };
  
  // Helper to get color based on strength value
  const getStrengthColor = (value) => {
    if (value > 0.2) return '#e74c3c'; // Strong - red
    if (value > 0.1) return '#f39c12'; // Medium - orange
    return '#3498db';                 // Light - blue
  };
  
  // Helper to get label based on strength value
  const getStrengthLabel = (value) => {
    if (value > 0.2) return 'Strong influence';
    if (value > 0.1) return 'Medium influence';
    return 'Light influence';
  };

  if (isLoading) {
    return (
      <div className="insights-page">
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
        
        <div className="insights-content">
          <div className="loading-indicator">
            <div className="spinner"></div>
            <p>Loading recommendation insights...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="insights-page">
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
        
        <div className="insights-content">
          <div className="error-message">
            <p>{error}</p>
            <button onClick={() => window.location.reload()} className="retry-btn">Try Again</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="insights-page">
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
      
      <div className="insights-hero">
        <div className="hero-content">
          <h1>Your Recommendation Insights</h1>
          <p>Understanding why movies are recommended for you</p>
        </div>
      </div>
      
      <div className="insights-content">
        {explanations.length > 0 ? (
          <>
            {analyseOverallFactors()}
            
            <div className="explanations-section">
              <h2>Why We Recommended These Movies</h2>
              
              <div className="explanations-list">
                {explanations.map(exp => (
                  <div key={exp.movie_id} className="explanation-card">
                    <div className="movie-info">
                      <h3>{exp.movie_title}</h3>
                      <p className="explanation-text">{exp.explanation}</p>
                    </div>
                    
                    <div className="explanation-actions">
                      <button 
                        className="show-factors-btn"
                        onClick={() => toggleFactorVisibility(exp.movie_id)}
                      >
                        {selectedFactors[exp.movie_id] ? 'Hide Factors' : 'Show Factors'}
                      </button>
                      
                      <Link to={`/movie/${exp.movie_id}`} className="view-movie-btn">
                        View Movie
                      </Link>
                    </div>
                    
                    {selectedFactors[exp.movie_id] && (
                      <div className="factor-breakdown">
                        {Object.entries(exp.aspects || {}).sort((a, b) => b[1] - a[1]).map(([factor, value]) => (
                          <div key={factor} className="factor-item">
                            <div className="factor-name">
                              {factor.replace(/_/g, ' ').replace(/boost|score/g, '').trim()}:
                            </div>
                            <div className="factor-bar-container">
                              <div 
                                className="factor-bar" 
                                style={{ 
                                  width: `${Math.min(value * 100, 100)}%`,
                                  backgroundColor: getStrengthColor(value)
                                }}
                              />
                              <span className="factor-value">{(value * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            <div className="how-it-works">
              <h2>How Recommendations Work</h2>
              <p>Your recommendations are based on multiple factors that work together to find movies that match your preferences:</p>
              
              <div className="factors-explanation">
                <div className="factor-explanation-item">
                  <h4>Genres</h4>
                  <p>We analyse the genres you enjoy based on your questionnaire responses and movies you've watched.</p>
                </div>
                
                <div className="factor-explanation-item">
                  <h4>Themes</h4>
                  <p>We look for themes that appear in your favorite films, such as redemption, coming-of-age, or survival.</p>
                </div>
                
                <div className="factor-explanation-item">
                  <h4>Actors</h4>
                  <p>If you consistently watch movies with certain actors, we'll recommend more films featuring them.</p>
                </div>
                
                <div className="factor-explanation-item">
                  <h4>Tone & Style</h4>
                  <p>We identify if you prefer dark, light, comedic, or serious content and find similar movies.</p>
                </div>
                
                <div className="factor-explanation-item">
                  <h4>Franchises</h4>
                  <p>If you're a fan of certain movie universes, we'll highlight related films you might enjoy.</p>
                </div>
                
                <div className="factor-explanation-item">
                  <h4>Ratings</h4>
                  <p>We give a small boost to highly-rated films to ensure quality recommendations.</p>
                </div>
              </div>
              
              <div className="feedback-reminder">
                <h4>Your Feedback Matters</h4>
                <p>When you rate movies or provide feedback on recommendations, we learn more about your preferences and improve future suggestions.</p>
                <Link to="/recommended" className="get-recommendations-btn">Back to Recommendations</Link>
              </div>
            </div>
          </>
        ) : (
          <div className="no-insights">
            <h2>No Recommendation Insights Available</h2>
            <p>We don't have enough data to generate insights about your recommendations yet. Try browsing more movies or completing the questionnaire to get personalized recommendations.</p>
            <div className="no-insights-actions">
              <Link to="/questionnaire" className="action-btn">Complete Questionnaire</Link>
              <Link to="/movies" className="action-btn">Browse Movies</Link>
            </div>
          </div>
        )}
      </div>
      
      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default RecommendationInsights;