import Navbar from "../components/Navbar";
import Sidebar from "../components/Sidebar";
import Assistant from "../components/Assistant";
import { LayoutContext, useAppShell } from "./LayoutContext";
import "../styles/DashboardLayout.css";

function DashboardLayout({ children }) {
  const isInsidePersistentShell = useAppShell();

  // Individual page components used this layout before routes were nested.  When
  // rendered below ProtectedLayout, return only their page content so the shell
  // is not unmounted and recreated whenever the route changes.
  if (isInsidePersistentShell) return children;

  return (
    <LayoutContext.Provider value={true}>
      <div className="dashboard-container">
        <Sidebar />

        <div className="main-content">
          <Navbar />

          <main id="dashboard-main-content" className="page-content">
            {children}
          </main>
          <Assistant />
        </div>
      </div>
    </LayoutContext.Provider>
  );
}

export default DashboardLayout;
