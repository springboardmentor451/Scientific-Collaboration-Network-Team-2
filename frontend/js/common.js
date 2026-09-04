/* =========================================================
   SciCollab - Common JavaScript
   ONE COMMON SIDEBAR FOR ALL PAGES

   Used by:
   dashboard.html
   researcher.html
   publication.html
   conference.html
   collaboration.html
   project.html
   analytics.html
   export.html
   settings.html
========================================================= */


const API_BASE_URL = "http://127.0.0.1:8000";

const collaborationTotal = document.getElementById("totalCollaborations");
if (collaborationTotal) {
    collaborationTotal.id = "total_collaborations";
}


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
   CURRENT USER
========================================================= */

async function getCurrentUser() {

    const token = getToken();


    if (!token) {

        window.location.href = "login.html";

        return null;
    }


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
   USER INITIALS
========================================================= */

function getInitials(user) {

    if (!user) {
        return "US";
    }


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

    const initials = getInitials(user);
    const displayName = getUserDisplayName(user);
    const role = getUserRole(user);
    const avatarUrl = user.avatar_url;
    const cacheBuster = "?t=" + (user._t || Date.now());
    const avatarSrc = avatarUrl ? (avatarUrl.startsWith("http") ? avatarUrl : API_BASE_URL + avatarUrl) + cacheBuster : null;

    const escapeHtml = (val) => String(val ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));

    function setAvatarContent(elem) {
        if (!elem) return;
        if (avatarSrc) {
            elem.style.background = "transparent";
            elem.style.padding = "0";
            elem.style.border = "none";
            elem.style.overflow = "hidden";
            elem.innerHTML = `<img src="${escapeHtml(avatarSrc)}" alt="${escapeHtml(displayName)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block;" />`;
        } else {
            elem.innerHTML = "";
            elem.textContent = initials;
            elem.style.background = "#2f65d9";
            elem.style.color = "#ffffff";
        }
        elem.classList.add("profile-trigger-btn");
        elem.title = "View & Edit User Profile";
        elem.style.cursor = "pointer";
    }

    // Header avatars
    const headerAvatars = document.querySelectorAll("#headerAvatar, #profileCircle, .header-avatar, .profile-circle, .avatar");
    headerAvatars.forEach(setAvatarContent);

    // Sidebar avatars
    const sidebarAvatars = document.querySelectorAll("#sidebarAvatar, #userAvatar, .user-avatar");
    sidebarAvatars.forEach(setAvatarContent);

    const sidebarUser = document.querySelector(".sidebar-user");
    if (sidebarUser) {
        sidebarUser.style.cursor = "pointer";
        sidebarUser.title = "View & Edit User Profile";
    }

    // Sidebar & Header user text labels
    const sidebarName = document.getElementById("sidebarName") || document.getElementById("userName");
    if (sidebarName) sidebarName.textContent = displayName;

    const sidebarRole = document.getElementById("sidebarRole");
    if (sidebarRole) sidebarRole.textContent = role;

    const userRole = document.getElementById("userRole");
    if (userRole) userRole.textContent = role;

    const headerUserName = document.getElementById("headerUserName");
    if (headerUserName) headerUserName.textContent = displayName;
}

/* =========================================================
   USER PROFILE MODAL
========================================================= */

function ensureUserProfileModal() {
    if (document.getElementById("scicollabProfileModal")) {
        return;
    }

    const modalHtml = `
    <div id="scicollabProfileModal" class="profile-modal-overlay" aria-hidden="true" style="display:none;">
        <div class="profile-modal-card">
            <div class="profile-modal-header">
                <div class="profile-modal-title">
                    <span class="modal-header-icon">👤</span>
                    <div>
                        <h2>User Profile & Settings</h2>
                        <p>Manage your account details, photo, and security</p>
                    </div>
                </div>
                <button type="button" class="profile-modal-close" id="closeProfileModalBtn" aria-label="Close">&times;</button>
            </div>

            <div class="profile-tabs">
                <button type="button" class="profile-tab active" data-tab="overview">Overview</button>
                <button type="button" class="profile-tab" data-tab="avatar">Upload Picture</button>
                <button type="button" class="profile-tab" data-tab="edit">Edit Profile</button>
                <button type="button" class="profile-tab" data-tab="password">Change Password</button>
            </div>

            <div class="profile-modal-body">
                <div id="profileAlert" class="profile-alert" style="display:none;"></div>

                <!-- OVERVIEW TAB -->
                <div class="profile-tab-content active" data-content="overview">
                    <div class="profile-overview-card">
                        <div class="profile-avatar-big" id="overviewAvatarBig">US</div>
                        <div class="profile-overview-info">
                            <h3 id="overviewName">User Name</h3>
                            <p class="profile-email" id="overviewEmail">user@example.com</p>
                            <span class="profile-role-badge" id="overviewRole">Researcher</span>
                        </div>
                    </div>
                    <div class="profile-details-grid">
                        <div class="detail-item">
                            <span class="detail-label">User ID</span>
                            <span class="detail-val" id="overviewId">#--</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Account Status</span>
                            <span class="detail-val status-active" id="overviewStatus">Active</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Role</span>
                            <span class="detail-val" id="overviewRoleDetail">Researcher</span>
                        </div>
                    </div>
                    <div class="profile-quick-actions">
                        <button type="button" class="btn-secondary" onclick="switchProfileTab('avatar')">📷 Change Picture</button>
                        <button type="button" class="btn-secondary" onclick="switchProfileTab('edit')">✏️ Edit Details</button>
                        <button type="button" class="btn-secondary" onclick="switchProfileTab('password')">🔑 Change Password</button>
                    </div>
                </div>

                <!-- AVATAR UPLOAD TAB -->
                <div class="profile-tab-content" data-content="avatar">
                    <form id="avatarUploadForm" class="profile-form">
                        <div class="avatar-upload-box">
                            <div class="profile-avatar-big" id="uploadAvatarPreview">US</div>
                            <div class="upload-controls">
                                <button type="button" class="btn-upload" id="chooseAvatarFileBtn">Choose Image File</button>
                                <input type="file" id="avatarFileInput" accept="image/jpeg,image/png,image/webp" style="display:none;" />
                                <span class="file-name-display" id="avatarFileName">No file selected</span>
                                <small class="help-text">Supported: JPG, PNG, WebP (Max 5 MB)</small>
                            </div>
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn-primary" id="saveAvatarBtn" disabled>Upload Profile Picture</button>
                        </div>
                    </form>
                </div>

                <!-- EDIT DETAILS TAB -->
                <div class="profile-tab-content" data-content="edit">
                    <form id="editProfileForm" class="profile-form">
                        <div class="form-group-custom">
                            <label for="editFullName">Full Name *</label>
                            <input type="text" id="editFullName" required placeholder="Enter your full name" maxlength="100" />
                        </div>
                        <div class="form-group-custom">
                            <label for="editEmail">Email Address *</label>
                            <input type="email" id="editEmail" required placeholder="name@example.com" maxlength="100" />
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn-primary" id="saveProfileBtn">Save Profile Details</button>
                        </div>
                    </form>
                </div>

                <!-- CHANGE PASSWORD TAB -->
                <div class="profile-tab-content" data-content="password">
                    <form id="changePasswordForm" class="profile-form">
                        <div class="form-group-custom">
                            <label for="currentPassword">Current Password *</label>
                            <input type="password" id="currentPassword" required placeholder="Enter current password" />
                        </div>
                        <div class="form-group-custom">
                            <label for="newPassword">New Password *</label>
                            <input type="password" id="newPassword" required placeholder="At least 6 characters" minlength="6" />
                        </div>
                        <div class="form-group-custom">
                            <label for="confirmPassword">Confirm New Password *</label>
                            <input type="password" id="confirmPassword" required placeholder="Re-enter new password" minlength="6" />
                        </div>
                        <div class="form-actions">
                            <button type="submit" class="btn-primary" id="savePasswordBtn">Update Password</button>
                        </div>
                    </form>
                </div>

            </div>
        </div>
    </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHtml);
    setupProfileModalListeners();
}

function switchProfileTab(tabName) {
    const tabs = document.querySelectorAll(".profile-tab");
    const contents = document.querySelectorAll(".profile-tab-content");
    const alert = document.getElementById("profileAlert");

    if (alert) alert.style.display = "none";

    tabs.forEach(tab => {
        if (tab.dataset.tab === tabName) {
            tab.classList.add("active");
        } else {
            tab.classList.remove("active");
        }
    });

    contents.forEach(content => {
        if (content.dataset.content === tabName) {
            content.classList.add("active");
        } else {
            content.classList.remove("active");
        }
    });
}

function showProfileAlert(message, isError = false) {
    const alert = document.getElementById("profileAlert");
    if (!alert) return;
    alert.textContent = message;
    alert.className = `profile-alert ${isError ? "error" : "success"}`;
    alert.style.display = "block";
}

async function openUserProfileModal() {
    ensureUserProfileModal();
    const modal = document.getElementById("scicollabProfileModal");
    if (!modal) return;

    modal.style.display = "flex";
    modal.setAttribute("aria-hidden", "false");
    switchProfileTab("overview");

    try {
        const res = await apiFetch("/profile/me");
        if (res && res.ok) {
            const freshUser = await readJson(res);
            freshUser._t = Date.now();
            localStorage.setItem("current_user", JSON.stringify(freshUser));
            updateUserProfile(freshUser);
            populateProfileModal(freshUser);
            return;
        }
    } catch (err) {
        console.error("Failed to load fresh user profile:", err);
    }

    const user = await getCurrentUser();
    if (user) {
        populateProfileModal(user);
    }
}

function populateProfileModal(user) {
    const initials = getInitials(user);
    const displayName = getUserDisplayName(user);
    const role = getUserRole(user);
    const avatarUrl = user.avatar_url;
    const cacheBuster = "?t=" + (user._t || Date.now());
    const avatarSrc = avatarUrl ? (avatarUrl.startsWith("http") ? avatarUrl : API_BASE_URL + avatarUrl) + cacheBuster : null;

    const escapeHtml = (val) => String(val ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]));

    function renderBigAvatar(elem) {
        if (!elem) return;
        if (avatarSrc) {
            elem.style.background = "transparent";
            elem.innerHTML = `<img src="${escapeHtml(avatarSrc)}" alt="${escapeHtml(displayName)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block;" />`;
        } else {
            elem.innerHTML = "";
            elem.textContent = initials;
            elem.style.background = "#1f3c88";
            elem.style.color = "#ffffff";
        }
    }

    renderBigAvatar(document.getElementById("overviewAvatarBig"));
    renderBigAvatar(document.getElementById("uploadAvatarPreview"));

    document.getElementById("overviewName").textContent = displayName;
    document.getElementById("overviewEmail").textContent = user.email || "";
    document.getElementById("overviewRole").textContent = role;

    document.getElementById("overviewId").textContent = `#${user.id || "--"}`;
    document.getElementById("overviewStatus").textContent = user.is_active ? "Active" : "Inactive";
    document.getElementById("overviewRoleDetail").textContent = role;

    document.getElementById("editFullName").value = user.full_name || user.name || "";
    document.getElementById("editEmail").value = user.email || "";

    document.getElementById("changePasswordForm").reset();
    document.getElementById("avatarUploadForm").reset();
    const fileNameDisp = document.getElementById("avatarFileName");
    if (fileNameDisp) fileNameDisp.textContent = "No file selected";
    const saveAvBtn = document.getElementById("saveAvatarBtn");
    if (saveAvBtn) saveAvBtn.disabled = true;
}

function closeUserProfileModal() {
    const modal = document.getElementById("scicollabProfileModal");
    if (modal) {
        modal.style.display = "none";
        modal.setAttribute("aria-hidden", "true");
    }
}

function setupProfileModalListeners() {
    const closeBtn = document.getElementById("closeProfileModalBtn");
    if (closeBtn) {
        closeBtn.addEventListener("click", closeUserProfileModal);
    }

    const modal = document.getElementById("scicollabProfileModal");
    if (modal) {
        modal.addEventListener("click", (e) => {
            if (e.target === modal) closeUserProfileModal();
        });
    }

    const tabs = document.querySelectorAll(".profile-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            switchProfileTab(tab.dataset.tab);
        });
    });

    const chooseBtn = document.getElementById("chooseAvatarFileBtn");
    const avatarInput = document.getElementById("avatarFileInput");
    const avatarFileName = document.getElementById("avatarFileName");
    const saveAvatarBtn = document.getElementById("saveAvatarBtn");
    const uploadPreview = document.getElementById("uploadAvatarPreview");

    if (chooseBtn && avatarInput) {
        chooseBtn.addEventListener("click", (e) => {
            e.preventDefault();
            avatarInput.click();
        });
    }

    if (avatarInput) {
        avatarInput.addEventListener("change", () => {
            const file = avatarInput.files[0];
            if (file) {
                avatarFileName.textContent = file.name;
                saveAvatarBtn.disabled = false;
                const reader = new FileReader();
                reader.onload = (e) => {
                    uploadPreview.style.background = "transparent";
                    uploadPreview.innerHTML = `<img src="${e.target.result}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;display:block;" />`;
                };
                reader.readAsDataURL(file);
            } else {
                avatarFileName.textContent = "No file selected";
                saveAvatarBtn.disabled = true;
            }
        });
    }

    const avatarForm = document.getElementById("avatarUploadForm");
    if (avatarForm) {
        avatarForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const file = avatarInput.files[0];
            if (!file) return;

            saveAvatarBtn.disabled = true;
            saveAvatarBtn.textContent = "Uploading...";

            try {
                const formData = new FormData();
                formData.append("avatar", file);

                const token = getToken();
                const response = await fetch(`${API_BASE_URL}/profile/me/avatar`, {
                    method: "POST",
                    headers: {
                        "Authorization": "Bearer " + token
                    },
                    body: formData
                });

                const data = await readJson(response);
                if (!response.ok) {
                    throw new Error(data.detail || "Failed to upload avatar.");
                }

                // Fetch full fresh profile from /profile/me
                const profRes = await apiFetch("/profile/me");
                let updatedUser = null;
                if (profRes && profRes.ok) {
                    updatedUser = await readJson(profRes);
                    updatedUser._t = Date.now();
                    localStorage.setItem("current_user", JSON.stringify(updatedUser));
                } else {
                    localStorage.removeItem("current_user");
                    updatedUser = await getCurrentUser();
                }

                updateUserProfile(updatedUser);
                populateProfileModal(updatedUser);

                showProfileAlert("Profile picture updated successfully!");
                setTimeout(() => switchProfileTab("overview"), 1000);
            } catch (error) {
                showProfileAlert(error.message, true);
            } finally {
                saveAvatarBtn.disabled = false;
                saveAvatarBtn.textContent = "Upload Profile Picture";
            }
        });
    }

    const editForm = document.getElementById("editProfileForm");
    if (editForm) {
        editForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const saveBtn = document.getElementById("saveProfileBtn");
            saveBtn.disabled = true;
            saveBtn.textContent = "Saving...";

            const fullName = document.getElementById("editFullName").value.trim();
            const email = document.getElementById("editEmail").value.trim();

            try {
                const response = await apiFetch("/profile/me", {
                    method: "PUT",
                    body: JSON.stringify({ full_name: fullName, email: email })
                });

                const data = await readJson(response);
                if (!response || !response.ok) {
                    throw new Error(data.detail || "Failed to update profile.");
                }

                localStorage.setItem("current_user", JSON.stringify(data));
                updateUserProfile(data);
                populateProfileModal(data);

                showProfileAlert("Profile details updated successfully!");
                setTimeout(() => switchProfileTab("overview"), 1000);
            } catch (error) {
                showProfileAlert(error.message, true);
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = "Save Profile Details";
            }
        });
    }

    const passwordForm = document.getElementById("changePasswordForm");
    if (passwordForm) {
        passwordForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const current_password = document.getElementById("currentPassword").value;
            const new_password = document.getElementById("newPassword").value;
            const confirm_password = document.getElementById("confirmPassword").value;

            if (new_password !== confirm_password) {
                showProfileAlert("New password and confirmation do not match.", true);
                return;
            }

            const saveBtn = document.getElementById("savePasswordBtn");
            saveBtn.disabled = true;
            saveBtn.textContent = "Updating...";

            try {
                const response = await apiFetch("/profile/change-password", {
                    method: "PUT",
                    body: JSON.stringify({ current_password, new_password })
                });

                const data = await readJson(response);
                if (!response || !response.ok) {
                    throw new Error(data.detail || "Failed to change password.");
                }

                passwordForm.reset();
                showProfileAlert("Password changed successfully!");
                setTimeout(() => switchProfileTab("overview"), 1200);
            } catch (error) {
                showProfileAlert(error.message, true);
            } finally {
                saveBtn.disabled = false;
                saveBtn.textContent = "Update Password";
            }
        });
    }
}



async function updateHeaderNotifications() {
    const notification = document.querySelector(".notification");

    if (!notification) {
        return;
    }

    try {
        const response = await apiFetch("/notifications");
        const data = await readJson(response);

        if (!response || !response.ok) {
            return;
        }

        const count = Number(data.unread_count || 0);
        notification.title = count
            ? `${count} unread notification${count === 1 ? "" : "s"}`
            : "No new notifications";
        notification.setAttribute("aria-label", notification.title);
        notification.dataset.unreadCount = String(count);

        const dot = notification.querySelector(".notification-dot");
        if (dot) {
            dot.style.display = count ? "block" : "none";
        }
    } catch (error) {
        console.error("Unable to load notifications:", error);
    }
}


/* =========================================================
   FIXED SIDEBAR ICONS
   THESE ICONS NEVER CHANGE
========================================================= */

const SIDEBAR_ICONS = {

    dashboard: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M3 10.5L12 3L21 10.5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"/>
            <path
                d="M5.5 9.5V20H18.5V9.5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"/>
            <path
                d="M9.5 20V14H14.5V20"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"/>
        </svg>
    `,


    researcher: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <circle
                cx="12"
                cy="8"
                r="3"
                stroke="currentColor"
                stroke-width="1.8"/>
            <path
                d="M6.5 20C6.5 16.7 8.8 14.5 12 14.5C15.2 14.5 17.5 16.7 17.5 20"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <circle
                cx="5"
                cy="11"
                r="2"
                stroke="currentColor"
                stroke-width="1.5"/>
            <circle
                cx="19"
                cy="11"
                r="2"
                stroke="currentColor"
                stroke-width="1.5"/>
        </svg>
    `,


    publication: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M6 3H15L19 7V21H6V3Z"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"/>
            <path
                d="M14 3V8H19"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"/>
            <path
                d="M9 12H16"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"/>
            <path
                d="M9 16H16"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"/>
        </svg>
    `,


    conference: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M3 9L12 4L21 9L12 14L3 9Z"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"/>
            <path
                d="M7 11.5V15.5C7 17.2 9.2 19 12 19C14.8 19 17 17.2 17 15.5V11.5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linejoin="round"/>
            <path
                d="M21 9V15"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
        </svg>
    `,


    collaboration: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M10 13.5L14 9.5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <path
                d="M8.5 17H7C4.8 17 3 15.2 3 13C3 10.8 4.8 9 7 9H10"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <path
                d="M15.5 7H17C19.2 7 21 8.8 21 11C21 13.2 19.2 15 17 15H14"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
        </svg>
    `,


    project: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <rect
                x="4"
                y="5"
                width="16"
                height="15"
                rx="2"
                stroke="currentColor"
                stroke-width="1.8"/>
            <path
                d="M9 5V3H15V5"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <path
                d="M8 10H16"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"/>
            <path
                d="M8 14H13"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"/>
        </svg>
    `,


    analytics: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M4 20V4"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <path
                d="M4 20H21"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <rect
                x="7"
                y="12"
                width="2.5"
                height="6"
                rx="0.5"
                fill="currentColor"/>
            <rect
                x="11.5"
                y="9"
                width="2.5"
                height="9"
                rx="0.5"
                fill="currentColor"/>
            <rect
                x="16"
                y="6"
                width="2.5"
                height="12"
                rx="0.5"
                fill="currentColor"/>
        </svg>
    `,


    export: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M12 3V15"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
            <path
                d="M7 11L12 16L17 11"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"/>
            <path
                d="M5 20H19"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"/>
        </svg>
    `,


    settings: `
        <svg viewBox="0 0 24 24"
             fill="none"
             xmlns="http://www.w3.org/2000/svg"
             aria-hidden="true">
            <path
                d="M12 8.5C10.1 8.5 8.5 10.1 8.5 12C8.5 13.9 10.1 15.5 12 15.5C13.9 15.5 15.5 13.9 15.5 12C15.5 10.1 13.9 8.5 12 8.5Z"
                stroke="currentColor"
                stroke-width="1.8"/>
            <path
                d="M19 13.2L20.5 14.4L18.5 17.8L16.7 17.1C16.1 17.6 15.4 18 14.6 18.2L14.3 20H9.7L9.4 18.2C8.6 18 7.9 17.6 7.3 17.1L5.5 17.8L3.5 14.4L5 13.2C4.9 12.8 4.8 12.4 5 10.8L3.5 9.6L5.5 6.2L7.3 6.9C7.9 6.4 8.6 6 9.4 5.8L9.7 4H14.3L14.6 5.8C15.4 6 16.1 6.4 16.7 6.9L18.5 6.2L20.5 9.6L19 10.8C19.1 11.2 19.2 11.6 19.2 12C19.2 12.4 19.1 12.8 19 13.2Z"
                stroke="currentColor"
                stroke-width="1.4"
                stroke-linejoin="round"/>
        </svg>
    `
};


/* =========================================================
   SIDEBAR NAVIGATION DATA

   DO NOT CHANGE ICONS HERE.
========================================================= */

const SIDEBAR_NAVIGATION = [

    {
        name: "Dashboard",
        href: "dashboard.html",
        page: "dashboard",
        icon: "dashboard"
    },

    {
        name: "Researchers",
        href: "researcher.html",
        page: "researcher",
        icon: "researcher"
    },

    {
        name: "Publications",
        href: "publication.html",
        page: "publication",
        icon: "publication"
    },

    {
        name: "Conferences",
        href: "conference.html",
        page: "conference",
        icon: "conference"
    },

    {
        name: "Collaborations",
        href: "collaboration.html",
        page: "collaboration",
        icon: "collaboration"
    },

    {
        name: "Projects",
        href: "project.html",
        page: "project",
        icon: "project"
    }

];


const SIDEBAR_TOOLS = [

    {
        name: "Analytics",
        href: "analytics.html",
        page: "analytics",
        icon: "analytics"
    },

    {
        name: "Export Data",
        href: "export.html",
        page: "export",
        icon: "export"
    },

    {
        name: "Settings",
        href: "settings.html",
        page: "settings",
        icon: "settings"
    }

];


/* =========================================================
   CREATE NAVIGATION ITEM
========================================================= */

function createSidebarItem(item) {

    return `

        <li>

            <a
                href="${item.href}"
                data-page="${item.page}"
            >

                <span class="menu-icon">
                    ${SIDEBAR_ICONS[item.icon]}
                </span>

                <span class="menu-text">
                    ${item.name}
                </span>

            </a>

        </li>

    `;
}


/* =========================================================
   CREATE COMMON SIDEBAR
========================================================= */

function createCommonSidebar() {

    const sidebar =
        document.querySelector(".sidebar");


    if (!sidebar) {

        console.error(
            "SciCollab ERROR: .sidebar element not found."
        );

        return;
    }


    /*
       IMPORTANT:

       Every page gets the EXACT SAME HTML
       generated from this function.

       No emoji icons.
       No page-specific icons.
       No duplicate navigation.
    */

    sidebar.innerHTML = `

        <!-- =================================================
             LOGO
        ================================================== -->

        <div class="logo-section">

            <div class="logo">

                <div class="logo-icon">

                    <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                    >

                        <path
                            d="M12 3L20 12L12 21L4 12L12 3Z"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linejoin="round"
                        />

                        <path
                            d="M12 8L16 12L12 16L8 12L12 8Z"
                            stroke="currentColor"
                            stroke-width="2"
                            stroke-linejoin="round"
                        />

                    </svg>

                </div>


                <div class="logo-text">

                    <h2>SciCollab</h2>

                    <p>
                        Network Analyzer
                    </p>

                </div>

            </div>

        </div>


        <!-- =================================================
             NAVIGATION
        ================================================== -->

        <div class="navigation-title">
            NAVIGATION
        </div>


        <ul class="sidebar-menu">

            ${SIDEBAR_NAVIGATION
                .map(createSidebarItem)
                .join("")}

        </ul>


        <!-- =================================================
             TOOLS
        ================================================== -->

        <div class="tools-title">
            TOOLS
        </div>


        <ul class="sidebar-menu">

            ${SIDEBAR_TOOLS
                .map(createSidebarItem)
                .join("")}

        </ul>


        <!-- =================================================
             USER
        ================================================== -->

        <div class="sidebar-user">

            <div
                class="user-avatar"
                id="sidebarAvatar"
            >
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
                aria-label="Logout"
            >
                <span aria-hidden="true">⇥</span>
                <span>Logout</span>
            </button>

        </div>

    `;


    /*
       Force the same icon sizing on every page.
    */

    const styleId =
        "scicollab-common-sidebar-icon-style";


    if (!document.getElementById(styleId)) {

        const style =
            document.createElement("style");


        style.id = styleId;


        style.textContent = `

            .sidebar .menu-icon {

                width: 24px !important;
                min-width: 24px !important;
                height: 24px !important;

                display: inline-flex !important;

                align-items: center !important;
                justify-content: center !important;

                flex-shrink: 0 !important;

                font-size: 0 !important;
            }


            .sidebar .menu-icon svg {

                width: 22px !important;
                height: 22px !important;

                display: block !important;

                flex-shrink: 0 !important;
            }


            .sidebar .sidebar-menu a {

                display: flex !important;

                align-items: center !important;
            }


            .sidebar .menu-text {

                display: inline-block !important;
            }


            .sidebar {

                overflow: hidden !important;
            }


            .sidebar .project-card {

                position: absolute !important;
                left: 15px !important;
                right: 15px !important;
                bottom: 86px !important;
                margin: 0 !important;
            }


            .sidebar .sidebar-user {

                z-index: 2 !important;
                background: #23418f !important;
            }


            .sidebar .logout-btn {

                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 5px !important;
                min-width: 64px !important;
                padding: 7px 8px !important;
                border: 1px solid #ffffff55 !important;
                border-radius: 7px !important;
                color: #ffffff !important;
                font: 600 11px Arial, sans-serif !important;
                white-space: nowrap !important;
            }


            .sidebar .logout-btn:hover {

                background: #ffffff1c !important;
            }

        `;


        document.head.appendChild(style);
    }

    /*
       VERIFICATION: Log all sidebar items and their icons
       This confirms every page uses identical icons.
    */

    console.log(
        "✓ SciCollab Sidebar Initialized:",
        SIDEBAR_NAVIGATION.map(item => ({
            name: item.name,
            icon: item.icon,
            page: item.page
        }))
    );
}


/* =========================================================
   ACTIVE SIDEBAR PAGE
========================================================= */

function setActiveSidebarPage() {

    const links =
        document.querySelectorAll(
            ".sidebar .sidebar-menu a[data-page]"
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
   INITIALIZE COMMON
========================================================= */

async function initializeCommon() {

    /*
       1. Authentication
    */

    const authenticated =
        await checkAuthentication();


    if (!authenticated) {
        return;
    }


    /*
       2. Create ONE common sidebar
    */

    createCommonSidebar();


    /*
       3. Set active page
    */

    setActiveSidebarPage();


    /*
       4. Logout
    */

    setupLogoutButton();


    /*
       5. User information
    */

    const user =
        await getCurrentUser();


    if (user) {

        updateUserProfile(user);
    }

    await updateHeaderNotifications();

    document.addEventListener("click", (e) => {
        const trigger = e.target.closest("#headerAvatar, #profileCircle, .profile-trigger-btn, .header-avatar-btn, .sidebar-user, .user-avatar");
        if (trigger && !e.target.closest("#logoutButton") && !e.target.closest(".logout-btn")) {
            e.preventDefault();
            openUserProfileModal();
        }
    });

}



/* =========================================================
   START
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializeCommon
);