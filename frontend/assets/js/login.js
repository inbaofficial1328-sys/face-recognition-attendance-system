"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".login-card form");
    const username = document.getElementById("username");
    const password = document.getElementById("password");
    const errorMessage = document.getElementById("login-error");
    const loginButton = document.getElementById("login-button");

    if (!form || !username || !password || !errorMessage || !loginButton) {
    console.error("Login form elements not found.");
    return;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.hidden = false;
    }

    function clearError() {
        errorMessage.textContent = "";
        errorMessage.hidden = true;
    }

    function setLoading(isLoading) {
    loginButton.disabled = isLoading;
    loginButton.textContent = isLoading
        ? "Signing In..."
        : "Sign In";
    }

    username.addEventListener("input", clearError);
    password.addEventListener("input", clearError);

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        clearError();

        if (!username.value.trim()) {
            showError("Please enter your username.");
            username.focus();
            return;
        }

        if (!password.value) {
            showError("Please enter your password.");
            password.focus();
            return;
        }

        setLoading(true);

try {
    const result = await authenticateUser(
        username.value.trim(),
        password.value
    );

    console.log("Authentication successful. Role:", result.user.role);

    clearError();
    // Role-based navigation will be added after integration testing.

} catch (error) {
    if (error instanceof TypeError) {
        showError("Cannot connect to the backend server.");
    } else {
        showError(error.message || "Login failed. Please try again.");
    }
} finally {
    setLoading(false);
}
    });

    console.log("Login JavaScript initialized successfully.");
});

async function authenticateUser(loginId, passwordValue) {
    const response = await fetch(
        `${window.APP_CONFIG.API_BASE_URL}/auth/login`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                login_id: loginId,
                password: passwordValue
            })
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.error?.message || "Login failed. Please try again."
        );
    }

    return data;
}