/* =========================================================
   SciCollab - Common JavaScript
   Used by:
   dashboard.html
   researcher.html
   publication.html
========================================================= */

/* =========================================================
   AUTHENTICATION
========================================================= */

function getToken() {
    return localStorage.getItem("access_token");
}


function isLoggedIn() {
    return !!getToken();
}


/* =========================================================
   LOGOUT
========================================================= */

function logout() {

    localStorage.removeItem("access_token");

    // Clear optional stored user information
    localStorage.removeItem("current_user");

    window.location.href = "login.html";
}


/* =========================================================
   API FETCH
========================================================= */

async function apiFetch(endpoint, options = {}) {

    const token = getToken();

    if (!token) {
        window.location.href = "login.html";
        return null;
    }

    const headers = {
        "Authorization": "Bearer " + token
    };

    /*
       Add JSON content type only when body exists.
    */
    if (options.body) {
        headers["Content-Type"] = "application/json";
    }

    try {

        const response = await fetch(
            API_BASE_URL + endpoint,
            {
                ...options,

                headers: {
                    ...headers,
                    ...(options.headers || {})
                }
            }
        );


        /*
           Token expired / invalid
        */

        if (response.status === 401) {

            localStorage.removeItem("access_token");
            localStorage.removeItem("current_user");

            window.location.href = "login.html";

            return null;
        }


        return response;

    }

    catch (error) {

        console.error(
            "API connection error:",
            error
        );

        throw error;
    }
}


/* =========================================================
   SAFE JSON
========================================================= */

async function readJson(response) {

    if (!response) {
        return {};
    }

    const text = await response.text();

    if (!text) {
        return {};
    }

    try {

        return JSON.parse(text);

    }

    catch {

        return {
            detail: text
        };
    }
}


/* =========================================================
   GET CURRENT USER
========================================================= */

async function getCurrentUser() {

    const token = getToken();

    if (!token) {

        window.location.href = "login.html";

        return null;
    }


    /*
       Check if user information is already stored.
    */

    const savedUser =
        localStorage.getItem("current_user");


    if (savedUser) {

        try {

            const cachedUser = JSON.parse(savedUser);

            if (cachedUser.full_name) {
                return cachedUser;
            }

        }

        catch {

            localStorage.removeItem("current_user");
        }
    }


    try {

        const response =
            await apiFetch("/auth/me");


        if (!response) {
            return null;
        }


        const data =
            await readJson(response);


        if (!response.ok) {

            console.error(
                "Unable to get current user:",
                data
            );

            return null;
        }


        /*
           Store user information temporarily.
        */

        localStorage.setItem(
            "current_user",
            JSON.stringify(data)
        );


        return data;

    }

    catch (error) {

        console.error(
            "Current user error:",
            error
        );

        return null;
    }
}


/* =========================================================
   INITIALS
========================================================= */

function getInitials(user) {

    if (!user) {
        return "US";
    }


    /*
       If backend provides name
    */

    const name =
        user.full_name ||
        user.name ||
        user.username ||
        "";


    if (name) {

        const parts =
            name.trim().split(/\s+/);


        if (parts.length >= 2) {

            return (
                parts[0][0] +
                parts[parts.length - 1][0]
            ).toUpperCase();
        }


        return name
            .substring(0, 2)
            .toUpperCase();
    }


    /*
       Otherwise use email
    */

    const email =
        user.email || "";


    if (email) {

        return email
            .substring(0, 2)
            .toUpperCase();
    }


    return "US";
}


/* =========================================================
   USER DISPLAY NAME
========================================================= */

function getUserDisplayName(user) {

    if (!user) {
        return "User";
    }


    return (
        user.full_name ||
        user.name ||
        user.username ||
        user.email ||
        "User"
    );
}


/* =========================================================
   USER ROLE
========================================================= */

function getUserRole(user) {

    if (!user) {
        return "User";
    }


    return (
        user.role ||
        user.user_role ||
        "User"
    );
}


/* =========================================================
   UPDATE USER PROFILE
========================================================= */

function updateUserProfile(user) {

    if (!user) {
        return;
    }


    const initials =
        getInitials(user);


    const displayName =
        getUserDisplayName(user);


    const role =
        getUserRole(user);


    /*
       Sidebar avatar
    */

    const sidebarAvatar =
        document.getElementById("sidebarAvatar") ||
        document.getElementById("userAvatar");


    if (sidebarAvatar) {

        sidebarAvatar.textContent =
            initials;
    }


    /*
       Header avatar
    */

    const headerAvatar =
        document.getElementById("headerAvatar") ||
        document.getElementById("profileCircle");


    if (headerAvatar) {

        headerAvatar.textContent =
            initials;
    }


    /*
       Sidebar name
    */

    const sidebarName =
        document.getElementById("sidebarName") ||
        document.getElementById("userName");


    if (sidebarName) {

        sidebarName.textContent =
            displayName;
    }


    /*
       Sidebar role
    */

    const sidebarRole =
        document.getElementById("sidebarRole");


    if (sidebarRole) {

        sidebarRole.textContent =
            role;
    }


    /*
       Older pages may have userRole
    */

    const userRole =
        document.getElementById("userRole");


    if (userRole) {

        userRole.textContent =
            role;
    }


    /*
       Header username if available
    */

    const headerUserName =
        document.getElementById("headerUserName");


    if (headerUserName) {

        headerUserName.textContent =
            displayName;
    }
}


/* =========================================================
   CREATE COMMON SIDEBAR
========================================================= */

function createCommonSidebar() {

    const sidebar =
        document.querySelector(".sidebar");


    if (!sidebar) {
        return;
    }


    /*
       We replace only the sidebar contents.
       The existing .sidebar CSS remains active.
    */

    sidebar.innerHTML = `

        <!-- LOGO -->

        <div class="logo-section">

            <div class="logo">

                <div class="logo-icon">
                    ◈
                </div>

                <div class="logo-text">

                    <h2>SciCollab</h2>

                    <p>Network Analyzer</p>

                </div>

            </div>

        </div>


        <!-- NAVIGATION -->

        <div class="navigation-title">
            NAVIGATION
        </div>


        <ul class="sidebar-menu">

            <li>
                <a href="dashboard.html"
                   data-page="dashboard">

                    <span class="menu-icon">⬡</span>

                    <span>Dashboard</span>

                </a>
            </li>


            <li>
                <a href="researcher.html"
                   data-page="researcher">

                    <span class="menu-icon">👥</span>

                    <span>Researchers</span>

                </a>
            </li>


            <li>
                <a href="publication.html"
                   data-page="publication">

                    <span class="menu-icon">📄</span>

                    <span>Publications</span>

                </a>
            </li>


            <li>
                <a href="conference.html"
                   data-page="conference">

                    <span class="menu-icon">🎓</span>

                    <span>Conferences</span>

                </a>
            </li>


            <li>
                <a href="collaboration.html"
                   data-page="collaboration">

                    <span class="menu-icon">🔗</span>

                    <span>Collaborations</span>

                </a>
            </li>


            <li>
                <a href="project.html"
                   data-page="project">

                    <span class="menu-icon">▣</span>

                    <span>Projects</span>

                </a>
            </li>

        </ul>


        <!-- TOOLS -->

        <div class="tools-title">
            TOOLS
        </div>


        <ul class="sidebar-menu">

            <li>
                <a href="analytics.html"
                   data-page="analytics">

                    <span class="menu-icon">📊</span>

                    <span>Analytics</span>

                </a>
            </li>


            <li>
                <a href="export.html"
                   data-page="export">

                    <span class="menu-icon">↓</span>

                    <span>Export Data</span>

                </a>
            </li>


            <li>
                <a href="settings.html"
                   data-page="settings">

                    <span class="menu-icon">⚙</span>

                    <span>Settings</span>

                </a>
            </li>

        </ul>


        <!-- USER -->

        <div class="sidebar-user">

            <div
                class="user-avatar"
                id="sidebarAvatar">

                US

            </div>


            <div class="user-info">

                <strong id="sidebarName">
                    Loading...
                </strong>

                <span id="sidebarRole">
                    User
                </span>

            </div>


            <button
                class="logout-btn"
                id="logoutButton"
                type="button"
                title="Logout"
            >
                ⇥ Logout
            </button>

        </div>

    `;

}


/* =========================================================
   ACTIVE SIDEBAR PAGE
========================================================= */

function setActiveSidebarPage() {

    const links =
        document.querySelectorAll(
            ".sidebar-menu a[data-page]"
        );


    const currentFile =
        window.location.pathname
            .split("/")
            .pop()
            .toLowerCase();


    links.forEach(link => {

        link.classList.remove("active");


        const href =
            link.getAttribute("href")
                .toLowerCase();


        if (href === currentFile) {

            link.classList.add("active");
        }

    });
}


/* =========================================================
   LOGOUT BUTTON
========================================================= */

function setupLogoutButton() {

    const button =
        document.getElementById(
            "logoutButton"
        );


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        logout
    );
}


/* =========================================================
   AUTH CHECK
========================================================= */

async function checkAuthentication() {

    const token =
        getToken();


    if (!token) {

        window.location.href =
            "login.html";

        return false;
    }


    return true;
}


/* =========================================================
   INITIALIZE COMMON PAGE
========================================================= */

async function initializeCommon() {

    /*
       1. Check token
    */

    const authenticated =
        await checkAuthentication();


    if (!authenticated) {
        return;
    }


    /*
       2. Build common sidebar
    */

    createCommonSidebar();


    /*
       3. Highlight current page
    */

    setActiveSidebarPage();


    /*
       4. Setup logout
    */

    setupLogoutButton();


    /*
       5. Load logged-in user
    */

    const user =
        await getCurrentUser();


    if (user) {

        updateUserProfile(user);
    }
}


/* =========================================================
   AUTO START
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeCommon
);


/* =========================================================
   RESEARCHER DIRECTORY
========================================================= */

const researcherDirectory = {
    rows: [],
    institutions: [],
    view: "table"
};


function researcherText(value) {
    return String(value || "").replace(/[&<>"']/g, character => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    }[character]));
}


function researcherInitials(name) {
    return String(name || "R")
        .split(/\s+/)
        .slice(0, 2)
        .map(part => part[0])
        .join("")
        .toUpperCase();
}


function showResearcherError(message) {
    const error = document.getElementById("errorMessage");

    if (!error) {
        return;
    }

    error.textContent = message;
    error.style.display = "block";
}


function getResearcherSearchValue(researcher) {
    return [
        researcher.full_name,
        researcher.email,
        researcher.institution_name,
        researcher.country,
        researcher.research_area
    ].join(" ");
}


function filteredResearchers() {
    const search = document
        .getElementById("researcherSearch")
        .value
        .trim()
        .toLowerCase();
    const country = document.getElementById("countryFilter").value;
    const field = document.getElementById("fieldFilter").value;
    const sort = document.getElementById("sortFilter").value;

    const rows = researcherDirectory.rows.filter(researcher => {
        const searchable = getResearcherSearchValue(researcher)
            .toLowerCase();
        const matchesSearch = !search || searchable.includes(search);
        const matchesCountry = country === "all"
            || researcher.country === country;
        const matchesField = field === "all"
            || researcher.research_area === field;

        return matchesSearch && matchesCountry && matchesField;
    });

    rows.sort((left, right) => {
        if (sort === "name_asc" || sort === "name_desc") {
            const direction = sort === "name_asc" ? 1 : -1;
            return direction * String(left.full_name || "")
                .localeCompare(String(right.full_name || ""));
        }

        const fields = {
            h_desc: "h_index",
            h_asc: "h_index",
            papers_desc: "papers",
            citations_desc: "citations"
        };
        const field = fields[sort] || "h_index";
        const direction = sort === "h_asc" ? 1 : -1;

        return direction * ((right[field] || 0) - (left[field] || 0));
    });

    return rows;
}


function researcherStatus(value) {
    const status = String(value || "Active");
    const className = status.toLowerCase().replace(/\s+/g, "-");

    return `<span class="status status-${className}">${researcherText(status)}</span>`;
}


function renderResearcherTable(rows) {
    const table = document.getElementById("researcherTable");
    const loading = document.getElementById("loading");
    const body = document.getElementById("researcherTableBody");

    loading.style.display = "none";
    table.style.display = "table";
    body.innerHTML = rows.length
        ? rows.map(researcher => `<tr>
            <td><div class="researcher-cell"><span class="researcher-avatar">${researcherInitials(researcher.full_name)}</span><div><div class="researcher-name">${researcherText(researcher.full_name || "Unnamed researcher")}</div><div class="researcher-email">${researcherText(researcher.email || "")}</div></div></div></td>
            <td>${researcherText(researcher.institution_name || "Not assigned")}</td>
            <td>${researcherText(researcher.country || "Not assigned")}</td>
            <td class="research-area">${researcherText(researcher.research_area || "Not specified")}</td>
            <td class="number-value">${researcher.h_index || 0}</td>
            <td>${researcher.papers || 0}</td>
            <td>${researcher.citations || 0}</td>
            <td>${researcher.collaborators || 0}</td>
            <td>${researcherStatus(researcher.status)}</td>
            <td><button class="action-btn" type="button" data-researcher-id="${researcher.id}">View</button></td>
        </tr>`).join("")
        : `<tr><td colspan="10" class="empty">No researchers match these filters.</td></tr>`;
}


function renderResearcherGrid(rows) {
    const grid = document.getElementById("gridContainer");

    grid.innerHTML = rows.length
        ? rows.map(researcher => `<article class="researcher-card"><div class="card-top"><span class="researcher-avatar">${researcherInitials(researcher.full_name)}</span><div><div class="card-name">${researcherText(researcher.full_name || "Unnamed researcher")}</div><div class="card-email">${researcherText(researcher.email || "")}</div></div></div><div class="card-research">${researcherText(researcher.research_area || "Research area not specified")}</div><div class="card-info"><div class="card-stat"><div class="card-stat-label">Institution</div><div class="card-stat-value">${researcherText(researcher.institution_name || "Not assigned")}</div></div><div class="card-stat"><div class="card-stat-label">H-Index</div><div class="card-stat-value">${researcher.h_index || 0}</div></div><div class="card-stat"><div class="card-stat-label">Papers</div><div class="card-stat-value">${researcher.papers || 0}</div></div><div class="card-stat"><div class="card-stat-label">Status</div><div class="card-stat-value">${researcherStatus(researcher.status)}</div></div></div></article>`).join("")
        : `<div class="empty">No researchers match these filters.</div>`;
}


function renderResearchers() {
    const rows = filteredResearchers();

    document.getElementById("resultCount").textContent = `${rows.length} result${rows.length === 1 ? "" : "s"}`;
    renderResearcherTable(rows);
    renderResearcherGrid(rows);
}


function setView(view) {
    researcherDirectory.view = view;
    document.getElementById("tableContainer").style.display = view === "table" ? "block" : "none";
    document.getElementById("gridContainer").style.display = view === "grid" ? "grid" : "none";
    document.getElementById("tableViewBtn").classList.toggle("active", view === "table");
    document.getElementById("gridViewBtn").classList.toggle("active", view === "grid");
    renderResearchers();
}


async function loadResearchersFromDatabase() {
    try {
        const response = await apiFetch("/researchers/");
        const data = await readJson(response);

        if (!response || !response.ok) {
            throw new Error(data.detail || "Unable to load researchers from the database.");
        }

        researcherDirectory.rows = Array.isArray(data) ? data : [];

        const fields = [...new Set(
            researcherDirectory.rows
                .map(researcher => researcher.research_area)
                .filter(Boolean)
        )].sort();

        document.getElementById("fieldFilter").insertAdjacentHTML(
            "beforeend",
            fields.map(field => `<option value="${researcherText(field)}">${researcherText(field)}</option>`).join("")
        );

        renderResearchers();
    } catch (error) {
        document.getElementById("loading").textContent = "Unable to load researchers.";
        showResearcherError(error.message);
    }
}


async function loadResearcherCountries() {
    const response = await apiFetch("/researchers/countries");
    const data = await readJson(response);

    if (!response || !response.ok) {
        throw new Error(data.detail || "Unable to load countries.");
    }

    document.getElementById("countryFilter").insertAdjacentHTML(
        "beforeend",
        data.map(country => `<option value="${researcherText(country)}">${researcherText(country)}</option>`).join("")
    );
}


async function refreshResearcherHeader() {
    const user = await getCurrentUser();

    if (user) {
        updateUserProfile(user);
    }

    if (typeof updateHeaderNotifications === "function") {
        await updateHeaderNotifications();
    }
}


function openAddResearcherModal() {
    const modal = document.getElementById("addResearcherModal");
    const error = document.getElementById("modalError");

    error.textContent = "";
    error.style.display = "none";
    modal.style.display = "flex";
}


function closeAddResearcherModal() {
    document.getElementById("addResearcherModal").style.display = "none";
}


function updateInstitutionCountry() {
    const institution = researcherDirectory.institutions.find(
        item => String(item.id) === document.getElementById("institutionId").value
    );

    document.getElementById("country").value = institution?.country || "";
}


async function loadResearcherInstitutions() {
    const response = await apiFetch("/researchers/institutions");
    const data = await readJson(response);

    if (!response || !response.ok) {
        throw new Error(data.detail || "Unable to load institutions.");
    }

    researcherDirectory.institutions = Array.isArray(data) ? data : [];
    document.getElementById("institutionId").insertAdjacentHTML(
        "beforeend",
        researcherDirectory.institutions.map(institution => `<option value="${institution.id}">${researcherText(institution.name)}${institution.country ? ` (${researcherText(institution.country)})` : ""}</option>`).join("")
    );
}


async function submitResearcher(event) {
    event.preventDefault();

    const button = document.getElementById("submitResearcherBtn");
    const error = document.getElementById("modalError");
    const payload = {
        full_name: document.getElementById("fullName").value.trim(),
        email: document.getElementById("email").value.trim(),
        password: document.getElementById("password").value,
        institution_id: document.getElementById("institutionId").value
            ? Number(document.getElementById("institutionId").value)
            : null,
        research_area: document.getElementById("researchArea").value.trim() || null,
        biography: document.getElementById("biography").value.trim() || null,
        profile_url: document.getElementById("profileUrl").value.trim() || null,
        status: document.getElementById("status").value
    };

    button.disabled = true;
    error.style.display = "none";

    try {
        const response = await apiFetch("/researchers/admin", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        const data = await readJson(response);

        if (!response || !response.ok) {
            throw new Error(data.detail || "Unable to add researcher.");
        }

        closeAddResearcherModal();
        document.getElementById("addResearcherForm").reset();
        updateInstitutionCountry();
        await loadResearchersFromDatabase();
    } catch (submissionError) {
        error.textContent = submissionError.message;
        error.style.display = "block";
    } finally {
        button.disabled = false;
    }
}


function initializeResearcherDirectory() {
    ["researcherSearch", "fieldFilter", "countryFilter", "sortFilter"]
        .forEach(id => document.getElementById(id).addEventListener("input", renderResearchers));

    document.getElementById("globalSearch").addEventListener("input", event => {
        document.getElementById("researcherSearch").value = event.target.value;
        renderResearchers();
    });

    document.getElementById("institutionId")
        .addEventListener("change", updateInstitutionCountry);

    Promise.all([
        loadResearchersFromDatabase(),
        loadResearcherInstitutions(),
        loadResearcherCountries(),
        refreshResearcherHeader()
    ]).catch(error => showResearcherError(error.message));
}


document.addEventListener(
    "DOMContentLoaded",
    initializeResearcherDirectory
);

