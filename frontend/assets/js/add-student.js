"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("add-student-form");
    const message = document.getElementById("form-message");
    const saveButton = document.getElementById("save-student-btn");

    if (!form || !message || !saveButton) {
        console.error("Add Student: Required HTML elements are missing.");
        return;
    }

    const fields = {
        collegeId: document.getElementById("college-id"),
        registrationNumber: document.getElementById("registration-number"),
        umisNumber: document.getElementById("umis-number"),
        fullName: document.getElementById("student-name"),
        dateOfBirth: document.getElementById("date-of-birth"),
        bloodGroup: document.getElementById("blood-group"),
        phoneNumber: document.getElementById("phone-number"),
        department: document.getElementById("department"),
        studentClass: document.getElementById("student-class")
    };

    if (Object.values(fields).some(field => !field)) {
        console.error("Add Student: One or more form fields are missing.");
        return;
    }

    function validateForm() {
        const requiredFields = [
            fields.collegeId,
            fields.registrationNumber,
            fields.umisNumber,
            fields.fullName,
            fields.dateOfBirth,
            fields.bloodGroup,
            fields.phoneNumber,
            fields.department,
            fields.studentClass
        ];

        const missingField = requiredFields.find(
            field => !field.value.trim()
        );

        if (missingField) {
            return "Please complete all required fields.";
        }

        if (!/^[0-9]{10}$/.test(fields.phoneNumber.value.trim())) {
            return "Enter a valid 10-digit phone number.";
        }

        const selectedDate = new Date(
            fields.dateOfBirth.value + "T00:00:00"
        );

        console.log("DOB input:", fields.dateOfBirth.value);
        console.log("Parsed DOB:", selectedDate);
        console.log("Current date:", new Date());

        if (
            Number.isNaN(selectedDate.getTime()) ||
            selectedDate > new Date()
        ) {
            return "Enter a valid date of birth.";
        }

        return "";
    }

    form.addEventListener("input", () => {
        message.textContent = "";
    });

    form.addEventListener("change", () => {
        message.textContent = "";
    });

    form.addEventListener("submit", event => {
        event.preventDefault();

        const error = validateForm();

        if (error) {
            message.textContent = error;
            return;
        }

        message.textContent =
            "Validation passed. Backend registration is not connected yet.";
    });

    // Registration remains disabled until backend integration.
    saveButton.disabled = true;

    console.log("Add Student form initialized successfully.");
});
