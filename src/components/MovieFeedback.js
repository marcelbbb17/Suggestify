import React, { useState } from 'react';
import axios from 'axios';
import '../styles/MovieFeedback.css';

const MovieFeedback = ({ movieId, onFeedbackSaved = () => {} }) => {
  const [feedback, setFeedback] = useState(null);
  const [rating, setRating] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showRating, setShowRating] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleFeedback = async (value) => {
    try {
      setIsSubmitting(true);
      setError(null);
      setFeedback(value);
      
      // If positive feedback, show rating option
      if (value === 'good') {
        setShowRating(true);
        return;
      }
      
      const token = localStorage.getItem('token');
      
      console.log('Sending feedback request:', {
        movie_id: movieId,
        feedback: value,
      });
      
      const response = await axios.post(
        'http://127.0.0.1:5000/recommendation-feedback',
        {
          movie_id: movieId,
          feedback: value
        },
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('Feedback response:', response.data);
      
      setSuccess(true);
      onFeedbackSaved(value);
    } catch (error) {
      console.error('Error saving feedback:', error);
      if (error.response) {
        console.error('Response error data:', error.response.data);
        console.error('Response error status:', error.response.status);
      }
      setError('Failed to save your feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRatingSubmit = async () => {
    try {
      setIsSubmitting(true);
      setError(null);
      
      const token = localStorage.getItem('token');
      
      console.log('Sending rating request:', {
        movie_id: movieId,
        feedback: feedback,
        rating: rating
      });
      
      const response = await axios.post(
        'http://127.0.0.1:5000/recommendation-feedback',
        {
          movie_id: movieId,
          feedback: feedback,
          rating: rating
        },
        {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
      
      console.log('Rating response:', response.data);
      
      setSuccess(true);
      onFeedbackSaved(feedback, rating);
    } catch (error) {
      console.error('Error saving rating:', error);
      if (error.response) {
        console.error('Response error data:', error.response.data);
        console.error('Response error status:', error.response.status);
      }
      setError('Failed to save your rating. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // If feedback already submitted successfully, show confirmation
  if (success) {
    return (
      <div className="movie-feedback success">
        <p>Thanks for your feedback!</p>
      </div>
    );
  }

  return (
    <div className="movie-feedback">
      {!feedback ? (
        <>
          <p>Was this a good recommendation for you?</p>
          <div className="feedback-buttons">
            <button 
              onClick={() => handleFeedback('good')}
              disabled={isSubmitting}
              className="feedback-btn good"
            >
              👍 Yes, great recommendation
            </button>
            <button
              onClick={() => handleFeedback('bad')}
              disabled={isSubmitting}
              className="feedback-btn bad"
            >
              👎 Not for me
            </button>
          </div>
        </>
      ) : showRating ? (
        <>
          <p>How would you rate this movie?</p>
          <div className="rating-stars">
            {[...Array(10)].map((_, i) => (
              <span 
                key={i}
                className={`star ${i < rating ? 'filled' : ''}`}
                onClick={() => setRating(i + 1)}
              >
                ★
              </span>
            ))}
            <span className="rating-value">{rating}/10</span>
          </div>
          <button 
            onClick={handleRatingSubmit} 
            disabled={isSubmitting}
            className="submit-rating-btn"
          >
            {isSubmitting ? 'Saving...' : 'Submit Rating'}
          </button>
        </>
      ) : (
        <p>Saving your feedback...</p>
      )}
      
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

export default MovieFeedback;