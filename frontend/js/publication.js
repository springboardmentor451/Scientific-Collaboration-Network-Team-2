/* =========================================================
   PUBLICATION.JS
   Publication-specific functionality
========================================================= */

let publications = [];


/* =========================================================
   LOAD PUBLICATIONS
========================================================= */

async function loadPublications() {

    const loading =
        document.getElementById("loading");

    const table =
        document.getElementById(
            "publicationTable"
        );


    if (loading) {
        loading.style.display = "block";
    }


    if (table) {
        table.style.display = "none";
    }


    hideError();


    try {

        const response =
            await apiFetch(
                "/publications/"
            );


        if (!response) {
            return;
        }


        const data =
            await readJson(
                response
            );


        console.log(
            "GET /publications/ response:",
            data
        );


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    response.status
                )
            );
        }


        if (Array.isArray(data)) {

            publications = data;

        }
        else if (
            Array.isArray(data.items)
        ) {

            publications = data.items;

        }
        else if (
            Array.isArray(data.publications)
        ) {

            publications =
                data.publications;

        }
        else {

            publications = [];
        }


        console.log(
            "Publications loaded:",
            publications
        );


        updateStatistics();

        populateFilters();

        renderPublications();
    }


    catch (error) {

        console.error(
            "Publication loading error:",
            error
        );


        showError(
            error.message
        );
    }


    finally {

        if (loading) {
            loading.style.display = "none";
        }
    }
}


/* =========================================================
   STATISTICS
========================================================= */

function updateStatistics() {

    const total =
        publications.length;


    const journalCount =
        publications.filter(
            publication => {

                const type =
                    String(
                        publication.publication_type ||
                        publication.type ||
                        ""
                    ).toLowerCase();


                return type.includes(
                    "journal"
                );
            }
        ).length;


    const conferenceCount =
        publications.filter(
            publication => {

                const type =
                    String(
                        publication.publication_type ||
                        publication.type ||
                        ""
                    ).toLowerCase();


                return type.includes(
                    "conference"
                );
            }
        ).length;


    const citations =
        publications.reduce(
            (sum, publication) => {

                return (
                    sum +
                    Number(
                        publication.citation_count ||
                        publication.citations ||
                        0
                    )
                );

            },
            0
        );


    const totalElement =
        document.getElementById(
            "totalPublications"
        );


    const journalElement =
        document.getElementById(
            "journalArticles"
        );


    const conferenceElement =
        document.getElementById(
            "conferencePapers"
        );


    const citationElement =
        document.getElementById(
            "totalCitations"
        );


    if (totalElement) {

        totalElement.textContent =
            total.toLocaleString();
    }


    if (journalElement) {

        journalElement.textContent =
            journalCount.toLocaleString();
    }


    if (conferenceElement) {

        conferenceElement.textContent =
            conferenceCount.toLocaleString();
    }


    if (citationElement) {

        citationElement.textContent =
            citations.toLocaleString();
    }
}


/* =========================================================
   FILTER DROPDOWNS
========================================================= */

function populateFilters() {

    const typeSelect =
        document.getElementById(
            "typeFilter"
        );


    const yearSelect =
        document.getElementById(
            "yearFilter"
        );


    const statusSelect =
        document.getElementById(
            "statusFilter"
        );


    if (!typeSelect ||
        !yearSelect ||
        !statusSelect) {

        return;
    }


    /* TYPES */

    const types = [
        ...new Set(
            publications
                .map(
                    publication =>
                        publication.publication_type ||
                        publication.type
                )
                .filter(Boolean)
        )
    ].sort();


    typeSelect.innerHTML =
        '<option value="all">All Types</option>';


    types.forEach(type => {

        const option =
            document.createElement(
                "option"
            );


        option.value = type;

        option.textContent = type;


        typeSelect.appendChild(
            option
        );
    });


    /* YEARS */

    const years = [
        ...new Set(
            publications
                .map(
                    publication =>
                        getYear(publication)
                )
                .filter(
                    year => year !== 0
                )
        )
    ].sort(
        (a, b) => b - a
    );


    yearSelect.innerHTML =
        '<option value="all">All Years</option>';


    years.forEach(year => {

        const option =
            document.createElement(
                "option"
            );


        option.value = year;

        option.textContent = year;


        yearSelect.appendChild(
            option
        );
    });


    /* STATUS */

    const statuses = [
        ...new Set(
            publications.map(
                publication =>
                    publication.status ||
                    "Published"
            )
        )
    ].sort();


    statusSelect.innerHTML =
        '<option value="all">All Status</option>';


    statuses.forEach(status => {

        const option =
            document.createElement(
                "option"
            );


        option.value = status;

        option.textContent = status;


        statusSelect.appendChild(
            option
        );
    });
}


/* =========================================================
   YEAR
========================================================= */

function getYear(publication) {

    if (!publication.publication_date) {
        return 0;
    }


    const date =
        new Date(
            publication.publication_date
        );


    if (isNaN(date.getTime())) {
        return 0;
    }


    return date.getFullYear();
}


/* =========================================================
   AUTHORS
========================================================= */

function getAuthors(publication) {

    if (
        typeof publication.authors ===
        "string"
    ) {

        return publication.authors;
    }


    if (
        typeof publication.author_names ===
        "string"
    ) {

        return publication.author_names;
    }


    if (
        Array.isArray(
            publication.authors
        )
    ) {

        return publication.authors
            .map(author => {

                if (
                    typeof author ===
                    "string"
                ) {

                    return author;
                }


                return (
                    author.full_name ||
                    author.name ||
                    author.researcher_name ||
                    ""
                );
            })
            .filter(Boolean)
            .join(", ");
    }


    if (
        Array.isArray(
            publication.author_names
        )
    ) {

        return publication.author_names.join(
            ", "
        );
    }


    return "Not available";
}


/* =========================================================
   FILTER PUBLICATIONS
========================================================= */

function getFilteredPublications() {

    let result =
        [...publications];


    const searchElement =
        document.getElementById(
            "publicationSearch"
        );


    const fieldElement =
        document.getElementById(
            "fieldFilter"
        );


    const typeElement =
        document.getElementById(
            "typeFilter"
        );


    const yearElement =
        document.getElementById(
            "yearFilter"
        );


    const statusElement =
        document.getElementById(
            "statusFilter"
        );


    const sortElement =
        document.getElementById(
            "citationSort"
        );


    const search =
        searchElement
            ? searchElement.value
                .trim()
                .toLowerCase()
            : "";


    const field =
        fieldElement
            ? fieldElement.value
            : "all";


    const type =
        typeElement
            ? typeElement.value
            : "all";


    const year =
        yearElement
            ? yearElement.value
            : "all";


    const status =
        statusElement
            ? statusElement.value
            : "all";


    const sort =
        sortElement
            ? sortElement.value
            : "default";


    /* SEARCH */

    if (search) {

        result =
            result.filter(
                publication => {

                    const title =
                        String(
                            publication.title ||
                            ""
                        );


                    const authors =
                        getAuthors(
                            publication
                        );


                    const venue =
                        String(
                            publication.journal_name ||
                            publication.venue ||
                            publication.conference_name ||
                            ""
                        );


                    const researchField =
                        String(
                            publication.field ||
                            publication.research_area ||
                            ""
                        );


                    let text = "";


                    if (
                        field === "all" ||
                        field === "title"
                    ) {

                        text +=
                            " " + title;
                    }


                    if (
                        field === "all" ||
                        field === "author"
                    ) {

                        text +=
                            " " + authors;
                    }


                    if (
                        field === "all" ||
                        field === "venue"
                    ) {

                        text +=
                            " " + venue;
                    }


                    if (
                        field === "all" ||
                        field === "field"
                    ) {

                        text +=
                            " " + researchField;
                    }


                    return text
                        .toLowerCase()
                        .includes(search);
                }
            );
    }


    /* TYPE */

    if (type !== "all") {

        result =
            result.filter(
                publication => {

                    return String(
                        publication.publication_type ||
                        publication.type ||
                        ""
                    ) === type;
                }
            );
    }


    /* YEAR */

    if (year !== "all") {

        result =
            result.filter(
                publication => {

                    return String(
                        getYear(publication)
                    ) === String(year);
                }
            );
    }


    /* STATUS */

    if (status !== "all") {

        result =
            result.filter(
                publication => {

                    return (
                        publication.status ||
                        "Published"
                    ) === status;
                }
            );
    }


    /* SORT */

    result.sort(
        (a, b) => {

            const citationsA =
                Number(
                    a.citation_count ||
                    a.citations ||
                    0
                );


            const citationsB =
                Number(
                    b.citation_count ||
                    b.citations ||
                    0
                );


            switch (sort) {

                case "citations_desc":

                    return (
                        citationsB -
                        citationsA
                    );


                case "citations_asc":

                    return (
                        citationsA -
                        citationsB
                    );


                case "year_desc":

                    return (
                        getYear(b) -
                        getYear(a)
                    );


                case "year_asc":

                    return (
                        getYear(a) -
                        getYear(b)
                    );


                case "title_asc":

                    return String(
                        a.title || ""
                    ).localeCompare(
                        String(
                            b.title || ""
                        )
                    );


                case "title_desc":

                    return String(
                        b.title || ""
                    ).localeCompare(
                        String(
                            a.title || ""
                        )
                    );


                default:

                    return 0;
            }
        }
    );


    return result;
}


/* =========================================================
   RENDER PUBLICATIONS
========================================================= */

function renderPublications() {

    const result =
        getFilteredPublications();


    const resultCount =
        document.getElementById(
            "resultCount"
        );


    if (resultCount) {

        resultCount.textContent =
            result.length +
            (
                result.length === 1
                    ? " result"
                    : " results"
            );
    }


    const table =
        document.getElementById(
            "publicationTable"
        );


    const tbody =
        document.getElementById(
            "publicationTableBody"
        );


    if (!table || !tbody) {
        return;
    }


    table.style.display = "table";


    tbody.innerHTML = "";


    if (result.length === 0) {

        tbody.innerHTML = `

            <tr>

                <td colspan="9">

                    <div class="empty">

                        No publications found.

                    </div>

                </td>

            </tr>

        `;

        return;
    }


    result.forEach(publication => {

        const row =
            document.createElement(
                "tr"
            );


        const title =
            publication.title ||
            "Untitled Publication";


        const doi =
            publication.doi ||
            "";


        const authors =
            getAuthors(
                publication
            );


        const venue =
            publication.journal_name ||
            publication.venue ||
            publication.conference_name ||
            "Not available";


        const year =
            getYear(publication) ||
            "—";


        const field =
            publication.field ||
            publication.research_area ||
            "—";


        const type =
            publication.publication_type ||
            publication.type ||
            "Other";


        const citations =
            Number(
                publication.citation_count ||
                publication.citations ||
                0
            );


        const status =
            publication.status ||
            "Published";


        row.innerHTML = `

            <td class="title-cell">

                <div class="publication-title">

                    ${escapeHtml(title)}

                </div>

                ${
                    doi
                        ? `
                            <div class="doi">

                                ${escapeHtml(doi)}

                            </div>
                          `
                        : ""
                }

            </td>


            <td>

                <div class="authors">

                    ${escapeHtml(authors)}

                </div>

            </td>


            <td>

                <span class="venue">

                    ${escapeHtml(venue)}

                </span>

            </td>


            <td class="year">

                ${year}

            </td>


            <td>

                ${escapeHtml(field)}

            </td>


            <td>

                <span
                    class="type-badge ${getTypeClass(type)}">

                    ${escapeHtml(type)}

                </span>

            </td>


            <td>

                <span class="citation-number">

                    ${citations.toLocaleString()}

                </span>

            </td>


            <td>

                <span
                    class="status-badge ${getStatusClass(status)}">

                    ${escapeHtml(status)}

                </span>

            </td>


            <td>

                <button
                    class="view-link"
                    onclick="viewPublication(${Number(publication.id)})">

                    View →

                </button>

            </td>
        `;


        tbody.appendChild(row);
    });
}


/* =========================================================
   TYPE CLASS
========================================================= */

function getTypeClass(type) {

    const value =
        String(type)
            .toLowerCase();


    if (value.includes("journal")) {
        return "type-journal";
    }


    if (value.includes("conference")) {
        return "type-conference";
    }


    if (value.includes("book")) {
        return "type-book";
    }


    return "type-other";
}


/* =========================================================
   STATUS CLASS
========================================================= */

function getStatusClass(status) {

    const value =
        String(status)
            .toLowerCase()
            .replace(/\s+/g, "-");


    if (value === "published") {
        return "status-published";
    }


    if (value === "draft") {
        return "status-draft";
    }


    if (value.includes("review")) {
        return "status-under-review";
    }


    if (value === "rejected") {
        return "status-rejected";
    }


    return "status-published";
}


/* =========================================================
   VIEW PUBLICATION
========================================================= */

function viewPublication(id) {

    const publication =
        publications.find(
            publication =>
                Number(publication.id) ===
                Number(id)
        );


    if (!publication) {

        alert(
            "Publication not found."
        );

        return;
    }


    const authors =
        getAuthors(
            publication
        );


    alert(

        "Publication\n\n" +

        "Title: " +
        (
            publication.title ||
            "—"
        ) +

        "\n\nAuthors: " +
        authors +

        "\n\nVenue: " +

        (
            publication.journal_name ||
            publication.venue ||
            publication.conference_name ||
            "—"
        ) +

        "\n\nYear: " +

        (
            getYear(publication) ||
            "—"
        ) +

        "\n\nField: " +

        (
            publication.field ||
            publication.research_area ||
            "—"
        ) +

        "\n\nType: " +

        (
            publication.publication_type ||
            publication.type ||
            "—"
        ) +

        "\n\nCitations: " +

        Number(
            publication.citation_count ||
            publication.citations ||
            0
        ) +

        "\n\nDOI: " +

        (
            publication.doi ||
            "—"
        )
    );
}


/* =========================================================
   ADD PUBLICATION MODAL
========================================================= */

function openAddPublicationModal() {

    const modal =
        document.getElementById(
            "publicationModal"
        );


    if (!modal) {
        return;
    }


    modal.style.display = "flex";


    const errorBox =
        document.getElementById(
            "modalError"
        );


    if (errorBox) {

        errorBox.style.display =
            "none";

        errorBox.textContent = "";
    }


    const form =
        document.getElementById(
            "publicationForm"
        );


    if (form) {
        form.reset();
    }
}


/* =========================================================
   CLOSE MODAL
========================================================= */

function closeAddPublicationModal() {

    const modal =
        document.getElementById(
            "publicationModal"
        );


    if (modal) {

        modal.style.display =
            "none";
    }
}


/* =========================================================
   SUBMIT PUBLICATION
========================================================= */

async function submitPublication(event) {

    event.preventDefault();


    const button =
        document.getElementById(
            "submitPublicationBtn"
        );


    const errorBox =
        document.getElementById(
            "modalError"
        );


    if (errorBox) {

        errorBox.style.display =
            "none";

        errorBox.textContent = "";
    }


    if (button) {

        button.disabled = true;

        button.textContent =
            "Adding...";
    }


    try {

        const payload = {

            title:
                document
                    .getElementById(
                        "publicationTitle"
                    )
                    .value
                    .trim(),


            abstract:
                document
                    .getElementById(
                        "publicationAbstract"
                    )
                    .value
                    .trim() ||
                null,


            publication_type:
                document
                    .getElementById(
                        "publicationType"
                    )
                    .value,


            journal_name:
                document
                    .getElementById(
                        "journalName"
                    )
                    .value
                    .trim() ||
                null,


            doi:
                document
                    .getElementById(
                        "doi"
                    )
                    .value
                    .trim() ||
                null,


            publication_date:
                document
                    .getElementById(
                        "publicationDate"
                    )
                    .value ||
                null,


            volume:
                document
                    .getElementById(
                        "volume"
                    )
                    .value
                    .trim() ||
                null,


            issue:
                document
                    .getElementById(
                        "issue"
                    )
                    .value
                    .trim() ||
                null,


            pages:
                document
                    .getElementById(
                        "pages"
                    )
                    .value
                    .trim() ||
                null,


            url:
                document
                    .getElementById(
                        "publicationUrl"
                    )
                    .value
                    .trim() ||
                null,


            citation_count:
                Number(
                    document
                        .getElementById(
                            "citationCount"
                        )
                        .value ||
                    0
                )
        };


        console.log(
            "POST /publications/ PAYLOAD:",
            payload
        );


        const response =
            await apiFetch(
                "/publications/",
                {
                    method: "POST",

                    body:
                        JSON.stringify(
                            payload
                        )
                }
            );


        if (!response) {
            return;
        }


        const data =
            await readResponse(
                response
            );


        console.log(
            "POST /publications/ RESPONSE:",
            data
        );


        if (!response.ok) {

            throw new Error(
                getApiErrorMessage(
                    data,
                    response.status
                )
            );
        }


        closeAddPublicationModal();


        await loadPublications();


        alert(
            "Publication added successfully!"
        );
    }


    catch (error) {

        console.error(
            "Add publication error:",
            error
        );


        if (errorBox) {

            errorBox.textContent =
                error.message;

            errorBox.style.display =
                "block";
        }
    }


    finally {

        if (button) {

            button.disabled = false;

            button.textContent =
                "Add Publication";
        }
    }
}


/* =========================================================
   ESCAPE HTML
========================================================= */

function escapeHtml(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }


    return String(value)

        .replace(
            /&/g,
            "&amp;"
        )

        .replace(
            /</g,
            "&lt;"
        )

        .replace(
            />/g,
            "&gt;"
        )

        .replace(
            /"/g,
            "&quot;"
        )

        .replace(
            /'/g,
            "&#039;"
        );
}


/* =========================================================
   ERROR
========================================================= */

function showError(message) {

    const box =
        document.getElementById(
            "errorMessage"
        );


    if (!box) {
        return;
    }


    box.textContent =
        message;


    box.style.display =
        "block";
}


/* =========================================================
   HIDE ERROR
========================================================= */

function hideError() {

    const box =
        document.getElementById(
            "errorMessage"
        );


    if (!box) {
        return;
    }


    box.style.display =
        "none";
}


/* =========================================================
   INITIALIZE PUBLICATION PAGE
========================================================= */

function initializePublicationPage() {

    if (!getToken()) {

        window.location.href =
            "login.html";

        return;
    }


    loadPublications();


    /* SEARCH */

    const publicationSearch =
        document.getElementById(
            "publicationSearch"
        );


    if (publicationSearch) {

        publicationSearch.addEventListener(
            "input",
            renderPublications
        );
    }


    /* FIELD */

    const fieldFilter =
        document.getElementById(
            "fieldFilter"
        );


    if (fieldFilter) {

        fieldFilter.addEventListener(
            "change",
            renderPublications
        );
    }


    /* TYPE */

    const typeFilter =
        document.getElementById(
            "typeFilter"
        );


    if (typeFilter) {

        typeFilter.addEventListener(
            "change",
            renderPublications
        );
    }


    /* YEAR */

    const yearFilter =
        document.getElementById(
            "yearFilter"
        );


    if (yearFilter) {

        yearFilter.addEventListener(
            "change",
            renderPublications
        );
    }


    /* STATUS */

    const statusFilter =
        document.getElementById(
            "statusFilter"
        );


    if (statusFilter) {

        statusFilter.addEventListener(
            "change",
            renderPublications
        );
    }


    /* CITATION SORT */

    const citationSort =
        document.getElementById(
            "citationSort"
        );


    if (citationSort) {

        citationSort.addEventListener(
            "change",
            renderPublications
        );
    }


    /* GLOBAL SEARCH */

    const globalSearch =
        document.getElementById(
            "globalSearch"
        );


    if (globalSearch) {

        globalSearch.addEventListener(
            "input",
            function() {

                if (publicationSearch) {

                    publicationSearch.value =
                        this.value;
                }


                renderPublications();
            }
        );
    }


    /* MODAL OUTSIDE CLICK */

    const modal =
        document.getElementById(
            "publicationModal"
        );


    if (modal) {

        modal.addEventListener(
            "click",
            function(event) {

                if (
                    event.target === this
                ) {

                    closeAddPublicationModal();
                }
            }
        );
    }
}


/* =========================================================
   START
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    initializePublicationPage
);