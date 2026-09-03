const collaborationState = { rows: [] };

const collabId = (id) => document.getElementById(id);
const collabEscape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;"
}[char]));

function showCollabError(message) {
    const element = collabId("errorMessage");
    if (element) {
        element.textContent = message;
        element.classList.add("show");
    }
}

async function loadCollabStats() {
    const response = await apiFetch("/collaborations/stats");
    if (!response) throw new Error("Please log in to view collaborations.");
    const data = await readJson(response);
    if (!response.ok) throw new Error(data.detail || `Statistics request failed (${response.status}).`);

    const values = {
        totalCollaborations: data.total_collaborations,
        active: data.active,
        completed: data.completed,
        pending: data.pending
    };
    Object.entries(values).forEach(([id, value]) => {
        const element = collabId(id);
        if (element) element.textContent = value ?? 0;
    });
}

function renderCollaborations() {
    const table = collabId("collaborationRows");
    if (!table) return;
    table.innerHTML = collaborationState.rows.length
        ? collaborationState.rows.map((row) => `<tr>
            <td>${collabEscape(row.researcher_1_name || `Researcher #${row.researcher_id_1}`)}</td>
            <td>${collabEscape(row.researcher_2_name || `Researcher #${row.researcher_id_2}`)}</td>
            <td>${collabEscape(row.institution_1 || "-")} x ${collabEscape(row.institution_2 || "-")}</td>
            <td>${collabEscape(row.description || "-")}</td>
            <td>${collabEscape(row.collaboration_type || "-")}</td>
            <td>${row.start_date || "-"}</td>
            <td>${collabEscape(row.status || "Pending")}</td>
            <td><button class="details" data-view="${row.id}">View -></button></td>
        </tr>`).join("")
        : '<tr><td colspan="8" class="empty">No collaborations match these filters.</td></tr>';
    const count = collabId("resultCount");
    if (count) count.textContent = `${collaborationState.rows.length} result${collaborationState.rows.length === 1 ? "" : "s"}`;
}

async function loadCollaborations() {
    const params = new URLSearchParams();
    const search = collabId("search")?.value.trim();
    const type = collabId("type")?.value;
    const status = collabId("status")?.value;
    if (search) params.set("search", search);
    if (type && type !== "all") params.set("collaboration_type", type);
    if (status && status !== "all") params.set("status", status);
    params.set("sort", collabId("sort")?.value || "date_desc");
    const response = await apiFetch(`/collaborations/?${params}`);
    if (!response) throw new Error("Please log in to view collaborations.");
    const data = await readJson(response);
    if (!response.ok) throw new Error(data.detail || `Collaborations request failed (${response.status}).`);
    collaborationState.rows = Array.isArray(data) ? data : [];
    renderCollaborations();
}

async function initCollaborationPage() {
    try {
        const user = await getCurrentUser();
        updateUserProfile(user);
        await loadResearchers();
        await loadCollaborations();
        populateTypes();
        await loadCollabStats();
    } catch (error) {
        showCollabError(error.message);
    }
}

async function loadResearchers() {
    const response = await apiFetch("/researchers/");
    if (!response) throw new Error("Please log in to select researchers.");
    const data = await readJson(response);
    if (!response.ok) throw new Error(data.detail || `Researchers request failed (${response.status}).`);

    ["researcher_id_1", "researcher_id_2"].forEach((id) => {
        const select = collabId(id) || document.querySelector(`[name="${id}"]`);
        if (!select) return;
        select.id = id;
        select.innerHTML = '<option value="">Select researcher</option>' + (Array.isArray(data) ? data : []).map((researcher) => {
            const name = researcher.full_name || researcher.name || `Researcher #${researcher.id}`;
            return `<option value="${researcher.id}">${collabEscape(name)}</option>`;
        }).join("");
    });
    addInstitutionFields(Array.isArray(data) ? data : []);
}

function addInstitutionFields(researchers) {
    const form = collabId("collaborationForm");
    if (!form || collabId("institution_1_display")) return;

    ["1", "2"].forEach((number) => {
        const researcherSelect = collabId(`researcher_id_${number}`) || document.querySelector(`[name="researcher_id_${number}"]`);
        if (!researcherSelect) return;
        const label = document.createElement("label");
        label.textContent = `Institution ${number}`;
        const input = document.createElement("input");
        input.type = "text";
        input.id = `institution_${number}_display`;
        input.name = `institution_${number}_name`;
        input.maxLength = 200;
        input.placeholder = "Enter institution name";
        input.required = true;
        label.appendChild(input);
        researcherSelect.closest("label")?.after(label);
    });
}

function populateTypes() {
    const select = collabId("type");
    if (!select) return;
    const types = [...new Set(["Researcher", "Co-authorship", ...collaborationState.rows.map((row) => row.collaboration_type).filter(Boolean)])].sort();
    select.innerHTML = '<option value="all">All Types</option>' + types.map((type) => `<option value="${collabEscape(type)}">${collabEscape(type)}</option>`).join("");
}

["search", "type", "status", "sort"].forEach((id) => collabId(id)?.addEventListener("input", loadCollaborations));
collabId("globalSearch")?.addEventListener("input", () => {
    collabId("search").value = collabId("globalSearch").value;
    loadCollaborations();
});

initCollaborationPage();

collabId("addCollaboration")?.addEventListener("click", () => {
    collabId("collaborationDialog")?.showModal();
});

document.querySelector("[data-close]")?.addEventListener("click", () => {
    collabId("collaborationDialog")?.close();
});

collabId("collaborationForm")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = new FormData(event.target);
    const payload = Object.fromEntries(form.entries());
    ["researcher_id_1", "researcher_id_2"].forEach((key) => {
        if (payload[key]) payload[key] = Number(payload[key]);
    });
    try {
        const response = await apiFetch("/collaborations/", { method: "POST", body: JSON.stringify(payload) });
        const data = await readJson(response);
        if (!response.ok) throw new Error(data.detail || "Unable to create collaboration.");
        collabId("collaborationDialog")?.close();
        event.target.reset();
        await loadCollaborations();
        populateTypes();
        await loadCollabStats();
    } catch (error) {
        const formError = collabId("formError");
        if (formError) {
            formError.textContent = error.message;
            formError.classList.add("show");
        } else {
            showCollabError(error.message);
        }
    }
});