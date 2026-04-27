function showAccountDetail(type) {
    const title = document.getElementById("accountTitle");
    const text = document.getElementById("accountText");
    const modal = document.getElementById("accountModal");

    switch (type) {
        case "summary":
            title.innerText = "Fee Summary";
            text.innerText = "Total Fee: ₹1,20,000 | Paid: ₹90,000 | Pending: ₹30,000";
            break;

        case "payment":
            title.innerText = "Payment Status";
            text.innerText = "Current semester fee is pending. Due date: 30 June 2026.";
            break;

        case "history":
            title.innerText = "Payment History";
            text.innerText = "Last payment of ₹45,000 made via UPI on 12 Jan 2026.";
            break;

        case "pay":
            title.innerText = "Pay Fees";
            text.innerText = "Pay fees securely using UPI, Debit Card, or Net Banking.";
            break;

        case "fine":
            title.innerText = "Fines & Penalties";
            text.innerText = "No fines or penalties pending.";
            break;

        case "scholarship":
            title.innerText = "Scholarship Status";
            text.innerText = "Post-Matric Scholarship applied. Approval pending.";
            break;

        case "refund":
            title.innerText = "Refund Status";
            text.innerText = "No refunds initiated.";
            break;

        case "nodues":
            title.innerText = "No Dues Status";
            text.innerText = "No-dues certificate will be available after fee clearance.";
            break;

        case "notices":
            title.innerText = "Accounts Notices";
            text.innerText = "Fee payment deadline extended till 30 June 2026.";
            break;
    }

    modal.style.display = "flex";
}

function closeAccountModal() {
    document.getElementById("accountModal").style.display = "none";
}
