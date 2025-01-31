import React, { useState} from "react";
import "../styles/Login.css"
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useUser } from "../context/User_Context";

function Login() {

  const { setUsername } = useUser();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault(); // prevents page from relaoding everytime user click the button

    try {
      const response = await axios.post("http://127.0.0.1:5000/login", {
        email, password,
      });

      const token = response.data.token
      const username = response.data.username;
      if (token && username) {
        localStorage.setItem("token", token);
        localStorage.setItem("username", username);
        setUsername(username);
        setMessage(response.data.success);
        setTimeout(() => navigate("/homepage"), 1000);
      }
    } 
    catch (error) {
      if (error.response) {
        setMessage(error.response.data.error);
      } else {
        setMessage("An error occured")
      }
    }
  };


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
          <li><Link to="/app">Home</Link></li>
        </ul>
      </nav>
    </header>
    {/* Login Section*/}
    <section className="login-form">
      <div className="login-header">
        <h1>Login</h1>
      </div>
      <form onSubmit={handleSubmit} className="login-sigin-up-form-element">
      <div className="input-box">
        <input type="text" className="input-field" placeholder="Email" autoComplete="off" value={email} onChange={(e) => setEmail(e.target.value)} required ></input>
      </div>
      <div className="input-box">
        <input type="password" className="input-field" placeholder="Password" autoComplete="off" value={password} onChange={(e) => setPassword(e.target.value)} required></input>
      </div>
      <div className="forgot">
        <section id="remember-me">
          <input type="checkbox" id="checkbox"></input>
          <label for="check">Remember me</label>
        </section>
        <section id="forgot-password">
          <Link id="forgot-password-link" to="/forgot">Forgot Password</Link>
        </section>
      </div>
      <div className="input-submit">
        <button className="submit-button" id="submit">Sign In</button>
      </div>
      </form>
      <div className="sign-up-link">
        <p>Don't have an account? <Link id="create-account-link" to="/signin">Create Account</Link></p>
      </div>
      <div id="popup-message"> 
        {message && <p className="message">{message}</p>}
      </div>
    </section>

    <footer>
      <p>&copy; 2024 Suggestify. All rights reserved.</p>
    </footer>
  </div>
  );
}

export default Login; 