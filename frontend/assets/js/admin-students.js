"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const addStudentButton = document.getElementById("add-student-btn");
    const searchInput = document.getElementById("student-search");
    const tableBody = document.getElementById("students-table-body");
    const statusElement = document.getElementById("student-status");

    if (!addStudentButton || !searchInput || !tableBody || !statusElement) {
        console.error("Student Management: Required HTML elements are missing.");
        return;
    }

    // Features remain disabled until their implementation is complete.
    addStudentButton.disabled = false;

    addStudentButton.addEventListener("click", () => {
        window.location.href = "add-student.html";
    });
    searchInput.disabled = true;

    statusElement.textContent =
        "Student Management interface ready. Awaiting feature implementation.";

    console.log("Student Management initialized successfully.");
});

