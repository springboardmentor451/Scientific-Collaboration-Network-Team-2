import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "./index.css";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { ProfilePictureProvider } from "./context/ProfilePictureContext";

ReactDOM.createRoot(document.getElementById("root")).render(
  <ThemeProvider><BrowserRouter><AuthProvider><ProfilePictureProvider><App /></ProfilePictureProvider></AuthProvider></BrowserRouter></ThemeProvider>
);
