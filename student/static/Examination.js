function showExamDetail(type) {
    const title = document.getElementById("examTitle");
    const text = document.getElementById("examText");
    const modal = document.getElementById("examModal");

    switch (type) {
        case "registration":
            title.innerText = "Exam Registration";
            text.innerText = "End Semester exam registration completed successfully.";
            break;

        case "schedule":
            title.innerText = "Exam Schedule";
            text.innerText = "Exams start from 10 June 2026. Timetable available.";
            break;

        case "hallticket":
            title.innerText = "Hall Ticket";
            text.innerText = "Hall ticket is available for download.";
            break;

        case "eligibility":
            title.innerText = "Eligibility Status";
            text.innerText = "You are eligible to appear for all exams.";
            break;

        case "results":
            title.innerText = "Examination Results";
            text.innerText = "Results declared. SGPA: 8.1";
            break;

        case "backlogs":
            title.innerText = "Backlogs";
            text.innerText = "No pending backlogs.";
            break;

        case "revaluation":
            title.innerText = "Revaluation Status";
            text.innerText = "Revaluation not applied.";
            break;

        case "supplementary":
            title.innerText = "Supplementary Exam";
            text.innerText = "Not eligible for supplementary exams.";
            break;
    }

    modal.style.display = "flex";
}

function closeExamModal() {
    document.getElementById("examModal").style.display = "none";
}
