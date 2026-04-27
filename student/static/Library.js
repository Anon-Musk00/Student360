function showLibraryDetail(type) {
    const title = document.getElementById("libraryTitle");
    const text = document.getElementById("libraryText");
    const modal = document.getElementById("libraryModal");

    switch (type) {
        case "issued":
            title.innerText = "Issued Books";
            text.innerText = "You have 2 books issued. Due dates available.";
            break;

        case "due":
            title.innerText = "Due Dates";
            text.innerText = "1 book is due on 20 June 2026.";
            break;

        case "fine":
            title.innerText = "Fine Status";
            text.innerText = "No pending fine.";
            break;

        case "reservation":
            title.innerText = "Reservations";
            text.innerText = "No active book reservations.";
            break;

        case "membership":
            title.innerText = "Library Membership";
            text.innerText = "Membership is active till March 2027.";
            break;

        case "digital":
            title.innerText = "Digital Library";
            text.innerText = "Access e-books, journals, and research databases.";
            break;

        case "search":
            title.innerText = "Book Search";
            text.innerText = "Search books by title, author, or subject.";
            break;

        case "notices":
            title.innerText = "Library Notices";
            text.innerText = "New books added. Library open till 6 PM.";
            break;
    }

    modal.style.display = "flex";
}

function closeLibraryModal() {
    document.getElementById("libraryModal").style.display = "none";
}
