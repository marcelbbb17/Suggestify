import React, { useState, useEffect } from 'react';
import { Link } from "react-router-dom";
import '../styles/LandingPage.css';

const LandingPage = () => {
  // Animation and featured content
  const [isVisible, setIsVisible] = useState(false);
  const [currentFeatureIndex, setCurrentFeatureIndex] = useState(0);
  
  // Features of suggestify
  const features = [
    {
      title: "Personalised Recommendations",
      description: "Discover movies tailored to your unique taste",
      icon: "🎯"
    },
    {
      title: "Track Your Watchlist",
      description: "Keep track of what you want to watch next",
      icon: "📋"
    },
    {
      title: "Rate & Review",
      description: "Share your opinions and see what others think",
      icon: "⭐"
    },
    {
      title: "Stay Updated",
      description: "Never miss the latest trending movies",
      icon: "🔥"
    }
  ];
  
  // Animation effect 
  useEffect(() => {
    setIsVisible(true);
    
    // Changes features every 3 seconds
    const featureInterval = setInterval(() => {
      setCurrentFeatureIndex((prevIndex) => 
        prevIndex === features.length - 1 ? 0 : prevIndex + 1
      );
    }, 3000);
    
    return () => clearInterval(featureInterval);
  }, [features.length]);

  return (
    <div className="landing-container">
      <header className="landing-header">
        <div className="logo">Suggestify</div>
        <div className="auth-buttons">
          <Link to="/login" className="login-button">Login</Link>
          <Link to="/signin" className="signup-button">Sign Up</Link>
        </div>
      </header>

      <main className="landing-main">
        <section className={`hero-section ${isVisible ? 'visible' : ''}`}>
          <div className="hero-content">
            <h1>Your Personal Movie Curator</h1>
            <p className="hero-subtitle">
              Discover films you'll love with AI-powered recommendations 
              tailored to your unique taste.
            </p>
            <Link to="/signin" className="cta-button">Get Started For Free</Link>
          </div>
          
          <div className="feature-highlight">
            <div className="feature-icon">{features[currentFeatureIndex].icon}</div>
            <h2>{features[currentFeatureIndex].title}</h2>
            <p>{features[currentFeatureIndex].description}</p>
          </div>
        </section>
        
        <section className="benefits-section">
          <h2>Why Choose Suggestify?</h2>
          
          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">🧠</div>
              <h3>Smart Recommendations</h3>
              <p>Our algorithm learns your preferences to suggest movies you'll actually enjoy.</p>
            </div>
            
            <div className="benefit-card">
              <div className="benefit-icon">🔍</div>
              <h3>Discover Hidden Gems</h3>
              <p>Find amazing films you might never have discovered on your own.</p>
            </div>
            
            <div className="benefit-card">
              <div className="benefit-icon">👥</div>
              <h3>Community Insights</h3>
              <p>See what other movie enthusiasts are watching and recommending.</p>
            </div>
            
            <div className="benefit-card">
              <div className="benefit-icon">⏱️</div>
              <h3>Save Time</h3>
              <p>No more endless scrolling. Find your next favorite movie quickly.</p>
            </div>
          </div>
        </section>
        
        <section className="cta-section">
          <div className="cta-content">
            <h2>Ready to transform your movie watching experience?</h2>
            <p>Join thousands of movie lovers who have discovered their new favorites with Suggestify.</p>
            <Link to="/signin" className="cta-button">Create Free Account</Link>
          </div>
        </section>
      </main>

      <footer className="landing-footer">
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default LandingPage;