"use strict";

document.addEventListener("DOMContentLoaded", () => {

    // Display today's date
    const dateElement = document.getElementById("current-date");

    if (dateElement) {
        const today = new Date();

        dateElement.textContent = today.toLocaleDateString(
            "en-IN",
            {
                day: "numeric",
                month: "long",
                year: "numeric"
            }
        );
    }

    // Dashboard statistics will be loaded from the backend.
    const statisticIds = [
        "total-students",
        "total-teachers",
        "active-classes",
        "today-attendance"
    ];

    statisticIds.forEach((id) => {
        const element = document.getElementById(id);

        if (element) {
            element.textContent = "--";
        }
    });

    console.log("Admin Dashboard initialized successfully.");

});
