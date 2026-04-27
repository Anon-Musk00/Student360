// Dynamic Admission Data (can come from backend later)
const admissionData = {
    name: "Rahul Kumar",
    appId: "ADM2026_1045",
    course: "B.Tech Computer Science",
    year: "2025-2029",
    status: "Under Verification",
    lastUpdated: "15-Jan-2026",
    nextAction: "Please upload pending documents and wait for verification."
};

// Insert data into UI
document.getElementById("name").innerText = admissionData.name;
document.getElementById("appId").innerText = admissionData.appId;
document.getElementById("course").innerText = admissionData.course;
document.getElementById("year").innerText = admissionData.year;
document.getElementById("status").innerText = admissionData.status;
document.getElementById("date").innerText = admissionData.lastUpdated;
document.getElementById("actionText").innerText = admissionData.nextAction;

// Change status color dynamically
const statusElement = document.getElementById("status");

if (admissionData.status === "Approved") {
    statusElement.style.color = "green";
} else if (admissionData.status === "Rejected") {
    statusElement.style.color = "red";
} else {
    statusElement.style.color = "orange";
}
