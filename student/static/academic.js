function showDetail(type) {
    const title = document.getElementById("modalTitle");
    const text = document.getElementById("modalText");
    const modal = document.getElementById("modal");

    switch (type) {
        case "semester":
            title.innerText = "Semester Details";
            text.innerText = "Currently enrolled in Semester 6 (2025–26).";
            break;

        case "attendance":
            title.innerText = "Attendance";
            text.innerText = "Overall attendance is 84%. Eligible for exams.";
            break;

        case "cgpa":
            title.innerText = "CGPA";
            text.innerText = "Cumulative Grade Point Average: 8.0";
            break;

        case "subjects":
            title.innerText = "Subjects";
            text.innerText = "6 subjects registered including labs.";
            break;

        case "backlogs":
            title.innerText = "Backlogs";
            text.innerText = "No pending backlogs. All subjects cleared.";
            break;

        case "status":
            title.innerText = "Academic Status";
            text.innerText = "You are academically eligible.";
            break;
    }

    modal.style.display = "flex";
}

function closeModal() {
    document.getElementById("modal").style.display = "none";
}
