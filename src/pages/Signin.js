import React, {useState} from "react";
import "../styles/Signin.css";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { useUser } from "../context/User_Context";
import { API_BASE_URL } from '../index';

function Signin() {
  const {setUsername} = useUser()
  const [email, setEmail] = useState("");
  const [username, setLocalUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("")
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault(); // prevents page from relaoding everytime user click the button

    try {
      const response = await axios.post(`${API_BASE_URL}/signup`, {
        email, username, password,
      });
      const token = response.data.token
      const receivedUsername = response.data.username
      if (token && receivedUsername){
        if (token && receivedUsername) {
          localStorage.setItem("token", token);
          localStorage.setItem("username", receivedUsername);
          setUsername(username);
          setMessage(response.data.success);
          setTimeout(() => navigate("/homepage"), 1000);
        }
        
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
          <li><Link to="/">Home</Link></li>
        </ul>
      </nav>
      <div className="extra-space">
        {/*div to provide extra space so that the navigation bar is centred*/}
      </div>
    </header>
    {/* Sign Up Section Section*/}
    <section className="signup-form">
      <div className="signup-header">
        <h1>Sign Up</h1>
      </div>
      <form onSubmit={handleSubmit} className="login-sigin-up-form-element">
      
      <div className="input-box">
        <input type="text" className="input-field" placeholder="Email" autoComplete="off" value={email} onChange={(event) => setEmail(event.target.value)} required></input>
      </div>
      <div className="input-box">
        <input type="text" className="input-field" placeholder="Username" autoComplete="off" value={username} onChange={(event) => setLocalUsername(event.target.value)} required></input>
      </div>
      <div className="input-box">
        <input type="password" className="input-field" placeholder="Password" autoComplete="off" value={password} onChange={(event) => setPassword(event.target.value)} required></input>
      </div>  
      <div className="forgot">
        <section id="remember-me">
          <input type="checkbox" id="checkbox"></input>
          <label htmlFor="check">Remember me</label>
        </section>
      </div>
      <div className="input-submit">
        <button className="submit-button" id="sign-in-botton">Sign Up</button>
      </div>
      </form>
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

export default Signin;