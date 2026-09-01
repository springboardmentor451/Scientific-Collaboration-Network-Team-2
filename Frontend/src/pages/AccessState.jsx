import { Link } from "react-router-dom";

export function Unauthorized() {
  return <main className="ui-empty-state"><div><h1>Access denied</h1><p>Your role does not have permission to open this page.</p><Link className="ui-button ui-button--primary" to="/dashboard">Return to dashboard</Link></div></main>;
}

export function NotFound() {
  return <main className="ui-empty-state"><div><h1>Page not found</h1><p>The page you requested does not exist or has moved.</p><Link className="ui-button ui-button--primary" to="/dashboard">Go to dashboard</Link></div></main>;
}
