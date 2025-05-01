import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/RecommendationExplanation.css';

const RecommendationExplanation = ({ movieId }) => {
  const [explanation, setExplanation] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRecommended, setIsRecommended] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    if (!movieId) return;
    
    // Fetch explanation for this movie
    const fetchExplanation = async () => {
      setIsLoading(true);
      
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setIsLoading(false);
          return;
        }
        
        const response = await axios.get(
          `http://127.0.0.1:5000/recommendation-explanations?movie_id=${movieId}`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        
        // If we got a valid response with explanation data
        if (response.data && response.data.explanation) {
          setExplanation(response.data);
          setIsRecommended(true);
        } else {
          // The movie was not found in recommendations
          setIsRecommended(false);
        }
      } catch (err) {
        setIsRecommended(false);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchExplanation();
  }, [movieId]);
  
  // If still loading, show a loading indicator
  if (isLoading) {
    return <div className="recommendation-explanation-loading">
      <div className="loading-dots"></div>
    </div>;
  }
  
  // If the movie is not recommended, don't show anything
  if (!isRecommended) {
    return null; // Return nothing instead of an error message
  }
  
  // Format the aspects data for display
  const formatAspects = (aspects) => {
    if (!aspects) return null;
    
    // Sort aspects by value
    const sortedAspects = Object.entries(aspects)
      .sort(([, valueA], [, valueB]) => valueB - valueA);
    
    return (
      <div className="explanation-aspects">
        {sortedAspects.map(([key, value]) => {
          // Skip very low values
          if (value < 0.01) return null;
          
          // Format the key for display
          const displayKey = key
            .replace(/_/g, ' ')
            .replace(/boost/g, '')
            .replace(/score/g, '')
            .trim();
          
          // Calculate percentage for the bar
          const percentage = Math.min(value * 100, 100);
          
          return (
            <div key={key} className="aspect-item">
              <div className="aspect-label">{displayKey}</div>
              <div className="aspect-bar-container">
                <div 
                  className="aspect-bar" 
                  style={{ width: `${percentage}%` }}
                />
                <div className="aspect-value">{(value * 100).toFixed(1)}%</div>
              </div>
            </div>
          );
        })}
      </div>
    );
  };
  
  return (
    <div className="recommendation-explanation">
      <div className="explanation-text">
        {explanation.explanation}
      </div>
      
      <button 
        className="show-details-button"
        onClick={() => setShowDetails(!showDetails)}
      >
        {showDetails ? 'Hide Details' : 'Show Why This Was Recommended'}
      </button>
      
      {showDetails && (
        <div className="explanation-details">
          <h4>Factors that influenced this recommendation:</h4>
          {formatAspects(explanation.aspects)}
          
          <div className="explanation-footer">
            <small>Recommendation generated on {new Date(explanation.created_at).toLocaleDateString()}</small>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecommendationExplanation;