import '../styles/App.css';
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { UserProvider } from "../context/User_Context"; 
import Login from "../pages/Login";
import Signin from "../pages/Signin";
import Homepage from '../pages/Homepage';
import Profile_Page from '../pages/Profile_Page';
import Questionnaire from '../pages/Questionnaire';
import RecommendedMovies from '../pages/Recommended_movies';
import LandingPage from '../pages/LandingPage';
import Watchlist from '../pages/Watchlist';
import Movies from '../pages/Movies';
import MovieDetail from '../pages/MovieDetails';

function Home() {
  return (
    /* Basic Structure for homepage for authenticated users */   
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
        <div className="auth">
          {/* Login and Sign up buttons */}
          <Link to="/Login" className="login-button">Login</Link>
          <Link to="/signin" className="signup-button">Sign Up</Link>
        </div>
      </header>
  
      <section className="main">
        <div className="main-content">
          <h1>Discover Your Next Favorite Movie</h1>
          {/* Search Bar */}
          <input
            type="text"
            className="search-bar"
            placeholder="Search for movies..."
          />
        </div>
      </section>
  
      {/* Basic layout for both recommended and trending movies */}
      <section id="recommended" className="movies-section">
        <h2>Recommended For You</h2>
        <div className="movie-grid">
          <div className="movie">Movie 1</div>
          <div className="movie">Movie 2</div>
          <div className="movie">Movie 3</div>
          <div className="movie">Movie 4</div>
        </div>
      </section>
  
      <section id="trending" className="movies-section">
        <h2>Trending Movies</h2>
        <div className="movie-grid">
          <div className="movie">Movie 5</div>
          <div className="movie">Movie 6</div>
          <div className="movie">Movie 7</div>
          <div className="movie">Movie 8</div>
        </div>
      </section>
  
      <footer>
        <p>&copy; 2024 Suggestify. All rights reserved.</p>
      </footer>
    </div>
  );
}

function App() {
  // Routing logic for homepage, login, and sign up pages
  return (
    <UserProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />}/>
          <Route path="/app" element={<Home />}/>
          <Route path="/login" element={<Login />}/>
          <Route path="/signin" element={<Signin />}/>
          <Route path='/homepage' element={<Homepage/>}/>
          <Route path="/profile" element={<Profile_Page/>}/>
          <Route path='/questionnaire' element={<Questionnaire/>}/>
          <Route path="/recommended" element={<RecommendedMovies/>}/>
          <Route path="/watchlist" element={<Watchlist/>}/>
          <Route path="/movies" element={<Movies/>}/>
          <Route path="/movie/:movieId" element={<MovieDetail/>}/>
        </Routes>
      </BrowserRouter>
    </UserProvider>
  );
}

export default App;