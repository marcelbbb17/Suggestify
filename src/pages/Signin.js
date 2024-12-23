import React from "react";
import "../styles/Signin.css";
import { Link } from "react-router-dom";

function Signin() {
  return (
    <div className="background">
    <header>
      <div className="logo">Suggestify</div>
      <nav>
        <ul>
          <li><a href="#movies">Movies</a></li>
          <li><a href="#trending">Trending</a></li>
          <li><a href="#watchlist">Watchlist</a></li>
          <li><a href="#profile">Profile</a></li>
        </ul>
      </nav>
    </header>
    {/* Sign Up Section Section*/}
    <section className="signup-form">
      <div className="signup-header">
        <h1>Sign Up</h1>
      </div>
      <div className="input-box">
        <input type="text" className="input-field" placeholder="Email" autoComplete="off" required></input>
      </div>
      <div className="input-box">
        <input type="password" className="input-field" placeholder="Password" autoComplete="off" required></input>
      </div>
      <div className="input-box">
        <input type="password" className="input-field" placeholder="Confirm Password" autoComplete="off" required></input>
      </div>  
      <div className="forgot">
        <section id="remember-me">
          <input type="checkbox" id="checkbox"></input>
          <label for="check">Remember me</label>
        </section>
      </div>
      <div className="input-submit">
        <button className="submit-button" id="submit">Sign Up</button>
      </div>
    </section>
    <footer>
      <p>&copy; 2024 Suggestify. All rights reserved.</p>
    </footer>
  </div>

  );
}

export default Signin;