import React, { createContext, useContext, useState, useEffect } from "react";


// Creates context for user to hold thier username so other pages can use it :)
const UserContext = createContext();

// the functionaloty to allow components to access the username and profile image
export function UserProvider({ children }) {
  const [username, setUsername] = useState("");
  const [profileImage, setProfileImage] = useState("/images/default-profile.jpg")
  
  // Gets usernamen from local storage so that when the page reloads it doesnt dissapear
  useEffect(() => {
    const storedUsername = localStorage.getItem("username");
    if (storedUsername) {
      setUsername(storedUsername);
    }
  }, [])

  // Gets profile pic from local storage too
  useEffect(() => {
    const storedPicture = localStorage.getItem("profilePicture");
    if (storedPicture){
      setProfileImage(storedPicture)
    }
  },[])

  // handles logout functionality 
  const logout = (navigate) => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setUsername(null)
    navigate("/app")

  };

  return (
    <UserContext.Provider value={{ username, setUsername, profileImage, setProfileImage, logout }}>
      {children}
    </UserContext.Provider>
  );
}

// This is actually what they use to access the username
export function useUser() {
  return useContext(UserContext);
}
