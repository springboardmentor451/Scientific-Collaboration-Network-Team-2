import { FaMoon, FaSun } from "react-icons/fa";
import { useTheme } from "../context/ThemeContext";

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const dark = theme === "dark";
  return <button type="button" className="navbar-icon-button theme-toggle" onClick={toggleTheme} title={dark ? "Switch to day theme" : "Switch to night theme"} aria-label={dark ? "Switch to day theme" : "Switch to night theme"}>{dark ? <FaSun /> : <FaMoon />}</button>;
}
export default ThemeToggle;
