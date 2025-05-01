import '../styles/App.css';
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { UserProvider } from "../context/User_Context"; 
import { WatchlistProvider } from "../context/Watchlist_Context";
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
import RecommendationInsights from '../pages/RecommendationInsights';
import DislikedRecommendations from '../components/DislikedRecommendations';

function App() {
  // Routing logic for all pages 
  return (
    <UserProvider>
      <WatchlistProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />}/>
            <Route path="/login" element={<Login />}/>
            <Route path="/signin" element={<Signin />}/>
            <Route path='/homepage' element={<Homepage/>}/>
            <Route path="/profile" element={<Profile_Page/>}/>
            <Route path='/questionnaire' element={<Questionnaire/>}/>
            <Route path="/recommended" element={<RecommendedMovies/>}/>
            <Route path="/watchlist" element={<Watchlist/>}/>
            <Route path="/movies" element={<Movies/>}/>
            <Route path="/movie/:movieId" element={<MovieDetail/>}/>
            <Route path="/recommendation-insights" element={<RecommendationInsights/>}/>
            <Route path="/disliked-recommendations" element={<DislikedRecommendations/>}/>
          </Routes>
        </BrowserRouter>
      </WatchlistProvider>
    </UserProvider>
  );
}

export default App;