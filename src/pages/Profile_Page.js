import React from "react";
import {useUser} from "../context/User_Context";
import { Link, useNavigate } from "react-router-dom";
import "../styles/Profile.css"


function Profile_Page() {
  const { username, profileImage, setProfileImage, logout } = useUser();
  const navigate = useNavigate();


  const changeProfilePicture = (event) => {
    const file = event.target.files[0]; 
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setProfileImage(e.target.result); 
        localStorage.setItem("profilePicture", e.target.result);
      };
      reader.readAsDataURL(file); 
    }
  };

  const handleLogout = () =>{
    return logout(navigate)
  }

  const handleRecommendationPage = () => {
    setTimeout(()=> navigate("/recommended"), 1000)
  }

  return (
    <div className="background">
      <header>
        <div className="logo">Suggestify</div>
        <nav>
          <ul>
            <li><a href="#movies">Movies</a></li>
            <li><a href="#trending">Trending</a></li>
            <li><a href="#watchlist">Watchlist</a></li>
            <li><Link to="/homepage">Home</Link></li>
          </ul>
        </nav>
        <div className="username">
          <p>Hello, {username || ":("}</p>
        </div>
      </header>

      <section className="main-profile-content">

        <div className="profile-information">
          <h1>Profile Page</h1>
          <div class="profile-picture-content">
            <label htmlFor="upload-input">
              <img id="profile-picture" src={profileImage} alt="profile" style={{cursor: "pointer"}}/>
            </label>
            <input type="file" id="upload-input" className="submit-button" accept="image/*" style={{display: "none"}}  onChange={changeProfilePicture}/> 
          </div>
          <h2>Welcome {username}!</h2>          
        </div>

        <div id="questionnaire-section">
          <p>Complete the questionnaire below to get your recommended movies</p>
          <Link to="/questionnaire" className="submit-button" id="complete-questionnaire-button">Complete Questionnaire</Link>
        </div>

        <div className="secondary-main-content">
          <h3>See Your Recommended Movies Below</h3>
          <button className="submit-button" onClick={handleRecommendationPage}> Recommended Movies </button>
        <button className="submit-button" onClick={handleLogout}>Logout</button>
        </div>
      </section>

      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default Profile_Page;
