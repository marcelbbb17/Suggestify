import React, { useState } from "react";
import "../styles/Questionnaire.css";
import {useUser} from "../context/User_Context";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";


function Questionnaire() {
  const {username} = useUser()
  const navigate = useNavigate()
  const [favouriteMovies, setFavouriteMovies] = useState([]);
  const [movieInput, setMovieInput] = useState("");
  const [genres, setGenres] = useState([]);
  const [age, setAge] = useState("");
  const [gender, setGender] = useState("Male");
  const [watchFrequency, setWatchFrequency] = useState("Daily");
  const [favouriteActors, setFavouriteActors] = useState([]);
  const [actorInput, setActorInput] = useState("");
  const [message, setMessage] = useState("")

  const handleGenreChange = (event) => { 
    const value = event.target.value; 
    setGenres((prevGenres) => { 
      if (prevGenres.includes(value)) {
        return prevGenres.filter((genre) => genre !== value); 
      } else {
        return [...prevGenres, value]; 
      }
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevents page from relaoding 

    if (!favouriteMovies.length || !genres.length || !favouriteActors.length || !age) {
      alert("Please complete ALL fields");
      return;
    }
    try {
      const token = localStorage.getItem("token")
      const response = await axios.post("http://127.0.0.1:5000/save_questionnaire", {
        favouriteMovies,
        genres,
        age,
        gender,
        watchFrequency,
        favouriteActors,
      }, 
      {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
      },
    })
      setMessage(response.data.success);
      setTimeout(() => navigate("/recommended"), 1000)
    }
    catch(error) {
      if (error.response){
        setMessage(error.response.data.error);
      } else{
        setMessage("An error occured")
      }
    }
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
        <p>Hello, {username}</p>
      </div>
    </header>
    <div className="main-questionnaire-content">
      <h1>Complete the Questionnaire</h1>
      <form id="questionnaire-form" onSubmit={handleSubmit}>
        <div id="favourite-movie-section">
          <h2>What are your favourite movies</h2>
          {/* Allow users to add as many movies they want for better recs */}
          <input className="questionnaire-search-bar" type="text" placeholder="Enter a movie" value={movieInput} onChange={(e) => setMovieInput(e.target.value)}/>
          <button type="button" className="submit-button" onClick={() => {
            if (movieInput.trim() !== "") {
              setFavouriteMovies((prevMovies) => [...prevMovies, movieInput]);
              setMovieInput("");
            }
          }}>
            Add Movies
          </button>

          <ul>
            {/* Displays users favourtite movies as a list which they can then remove if they entered incorrect one */}
            {favouriteMovies.map((movie, index) => (
              <li key={index}>
                {movie}{" "}
                <button type="button" className="remove-button"
                  onClick={() =>
                    setFavouriteMovies((prevMovies) => prevMovies.filter((m) => m !== movie))
                  }
                >
                  Remove
                </button>
              </li>
            ))}
          </ul> 
        </div> 

          <div id="genre-section">
            <h2>Select Your Favorite Genres:</h2>
           <label>
            <input id="tick" type="checkbox" value="Action" onChange={handleGenreChange} /> Action
          </label>
          <label>
            <input id="tick" type="checkbox" value="Adventure" onChange={handleGenreChange} /> Adventure
          </label>
          <label>
            <input id="tick" type="checkbox" value="Animation" onChange={handleGenreChange} /> Animation
          </label>
          <label>
            <input id="tick" type="checkbox" value="Comedy" onChange={handleGenreChange} /> Comedy
          </label>
          <label>
            <input id="tick" type="checkbox" value="Crime" onChange={handleGenreChange} /> Crime
        </label>
        <label>
          <input id="tick" type="checkbox" value="Documentary" onChange={handleGenreChange} /> Documentary
        </label>
        <label>
          <input id="tick" type="checkbox" value="Drama" onChange={handleGenreChange} /> Drama
        </label>
        <label>
          <input id="tick" type="checkbox" value="Family" onChange={handleGenreChange} /> Family
        </label>
        <label>
          <input id="tick" type="checkbox" value="Fantasy" onChange={handleGenreChange} /> Fantasy
        </label>
        <label>
          <input id="tick" type="checkbox" value="History" onChange={handleGenreChange} /> History
        </label>
        <label>
          <input id="tick" type="checkbox" value="Horror" onChange={handleGenreChange} /> Horror
        </label>
        <label>
          <input id="tick" type="checkbox" value="Music" onChange={handleGenreChange} /> Music
        </label>
        <label>
          <input id="tick" type="checkbox" value="Mystery" onChange={handleGenreChange} /> Mystery
        </label>
        <label>
          <input id="tick" type="checkbox" value="Romance" onChange={handleGenreChange} /> Romance
        </label>
        <label>
          <input id="tick" type="checkbox" value="Sci-Fi" onChange={handleGenreChange} /> Sci-Fi
        </label>
        <label>
          <input id="tick" type="checkbox" value="TV Movie" onChange={handleGenreChange} /> TV Movie
        </label>
        <label>
          <input id="tick" type="checkbox" value="Thriller" onChange={handleGenreChange} /> Thriller
        </label>
        <label>
         <input id="tick" type="checkbox" value="War" onChange={handleGenreChange} /> War
       </label>
        <label>
          <input id="tick" type="checkbox" value="Western" onChange={handleGenreChange} /> Western
        </label>
      </div>

        <div id="age-section">
          <h2>Age:</h2>
          <input type="number" value={age} onChange={(e) => setAge(e.target.value)} required />
        </div>

        <div id="gender-section">
          <h2>Gender:</h2>
          <label>
            <input type="radio" value="Male" name="gender" onChange={(e) => setGender(e.target.value)} required /> Male
          </label>
          <label>
            <input type="radio" value="Female" name="gender" onChange={(e) => setGender(e.target.value)} /> Female
          </label>
          <label>
            <input type="radio" value="Other" name="gender" onChange={(e) => setGender(e.target.value)} /> Other
          </label>
        </div>

        <div id="frequency-section">
          <h2>How often do you watch movies?</h2>
          <select value={watchFrequency} onChange={(e) => setWatchFrequency(e.target.value)}>
            <option value="Daily">Daily</option>
            <option value="Weekly">Weekly</option>
            <option value="Monthly">Monthly</option>
            <option value="Rarely">Rarely</option>
          </select>
        </div>

        <div id="actor-section">
          <h2>Favorite Actors:</h2>
          <input className="questionnaire-search-bar" type="text" value={actorInput} onChange={(e) => setActorInput(e.target.value)} />
          <button type="button" className="submit-button"
          onClick={() => {
            if(actorInput.trim() !== "") {
              setFavouriteActors((prevActors) => [...prevActors, actorInput]);
              setActorInput("");
            }
          }}> Add Actor/Actress
          </button>
          <ul>
            {favouriteActors.map((actor, index) => (
              <li key={index}>
                {actor}{""}
                <button type="button" className="remove-button"
                onClick={() => setFavouriteActors((prevActor) => prevActor.filter((a) => a !== actor))}>
                  remove
                </button>
              </li>
            )) }

          </ul>

        </div>

        <button type="submit" className="submit-button">Submit</button>
      </form>
      <div> 
        {message && <p className="message">{message}</p>}
      </div>
    </div>
    <footer>
      <p>&copy; 2024 Suggestify. All rights reserved.</p>
    </footer>
  </div>
  );
}

export default Questionnaire;