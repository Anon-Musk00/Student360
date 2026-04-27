document.addEventListener("DOMContentLoaded", function () {

    const form = document.querySelector("form");
    const statusSection = document.getElementById("statusSection");

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const regId = document.querySelector("input").value.trim();

        if (regId === "") {
            alert("Please enter Registration ID");
            return;
        }

        // Simple validation (more flexible)
        if (!regId.startsWith("STU-")) {
            alert("Registration ID must start with STU-");
            return;
        }

        // Show status section
        statusSection.style.display = "block";
    });
});

function openCard(type) {
    if (type === "admission") {
        window.location.href = "admission.html";
    } 
    else if (type === "academic") {
        window.location.href = "academic.html";
    } 
    else if (type === "exam") {
        window.location.href = "exam.html";
    } 
    else if (type === "library") {
        window.location.href = "library.html";
    } 
    else if (type === "account") {
        window.location.href = "account.html";
    }
}

