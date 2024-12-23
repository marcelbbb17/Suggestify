import React from "react";
import "../styles/Login.css"
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Signin from "../pages/Signin";

function Login() {

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
    {/* Login Section*/}
    <section className="login-form">
      <div className="login-header">
        <h1>Login</h1>
      </div>
      <div className="input-box">
        <input type="text" className="input-field" placeholder="Email" autoComplete="off" required></input>
      </div>
      <div className="input-box">
        <input type="password" className="input-field" placeholder="Password" autoComplete="off" required></input>
      </div>
      <div className="forgot">
        <section id="remember-me">
          <input type="checkbox" id="checkbox"></input>
          <label for="check">Remember me</label>
        </section>
        <section id="forgot-password">
          <a href="">Forgot Password</a>
        </section>
      </div>
      <div className="input-submit">
        <button className="submit-button" id="submit">Sign In</button>
      </div>
      <div className="sign-up-link">
        <p>Don't have an account? <Link to="/signin">Create Account</Link></p>
      </div>
    </section>

    <footer>
      <p>&copy; 2024 Suggestify. All rights reserved.</p>
    </footer>
  </div>
  );
}

export default Login; 