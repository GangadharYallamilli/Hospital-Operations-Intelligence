document.addEventListener("DOMContentLoaded", function () {


    // =====================================================
    // PASSWORD SHOW / HIDE
    // =====================================================

    const passwordToggles =
        document.querySelectorAll(".password-toggle");


    passwordToggles.forEach(function (button) {

        button.addEventListener("click", function () {

            const targetId =
                button.getAttribute("data-target");

            const passwordInput =
                document.getElementById(targetId);

            if (!passwordInput) {
                return;
            }


            const eyeOpen =
                button.querySelector(".eye-open");

            const eyeClosed =
                button.querySelector(".eye-closed");


            if (passwordInput.type === "password") {

                passwordInput.type = "text";

                if (eyeOpen) {
                    eyeOpen.style.display = "none";
                }

                if (eyeClosed) {
                    eyeClosed.style.display = "block";
                }

                button.setAttribute(
                    "aria-label",
                    "Hide password"
                );

            } else {

                passwordInput.type = "password";

                if (eyeOpen) {
                    eyeOpen.style.display = "block";
                }

                if (eyeClosed) {
                    eyeClosed.style.display = "none";
                }

                button.setAttribute(
                    "aria-label",
                    "Show password"
                );

            }

        });

    });



    // =====================================================
    // PASSWORD VALIDATION
    // =====================================================

    const registerPassword =
        document.getElementById("registerPassword");


    if (registerPassword) {

        registerPassword.addEventListener(
            "input",
            function () {

                const password =
                    registerPassword.value;


                // At least 8 characters
                const lengthValid =
                    password.length >= 8;


                // At least 2 numbers
                const numberCount =
                    (password.match(/\d/g) || []).length;

                const numberValid =
                    numberCount >= 2;


                // At least 1 special character
                const specialValid =
                    /[^A-Za-z0-9]/.test(password);


                updatePasswordRule(
                    "lengthRequirement",
                    lengthValid
                );


                updatePasswordRule(
                    "numberRequirement",
                    numberValid
                );


                updatePasswordRule(
                    "specialRequirement",
                    specialValid
                );

            }
        );

    }



    // =====================================================
    // LOGIN
    // =====================================================

    const loginForm =
        document.getElementById("loginForm");


    if (loginForm) {

        loginForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                const email =
                    document.getElementById(
                        "loginEmail"
                    ).value.trim();


                const password =
                    document.getElementById(
                        "loginPassword"
                    ).value;


                const status =
                    document.getElementById(
                        "loginStatus"
                    );


                status.textContent =
                    "Signing in...";

                status.className =
                    "auth-status";


                try {

                    const response =
                        await fetch(
                            "/auth/login",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body: JSON.stringify({
                                    email: email,
                                    password: password
                                })
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            "Login failed."
                        );

                    }


                    status.textContent =
                        "Login successful. Redirecting...";

                    status.className =
                        "auth-status success";


                    setTimeout(
                        function () {

                            window.location.href = "/index.html";

                        },
                        500
                    );


                } catch (error) {

                    status.textContent =
                        error.message;

                    status.className =
                        "auth-status error";

                }

            }
        );

    }



    // =====================================================
    // REGISTER
    // =====================================================

    const registerForm =
        document.getElementById(
            "registerForm"
        );


    if (registerForm) {

        registerForm.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();


                const hospitalName =
                    document.getElementById(
                        "hospitalName"
                    ).value.trim();


                const adminName =
                    document.getElementById(
                        "adminName"
                    ).value.trim();


                const email =
                    document.getElementById(
                        "registerEmail"
                    ).value.trim();


                const password =
                    document.getElementById(
                        "registerPassword"
                    ).value;


                const confirmPassword =
                    document.getElementById(
                        "confirmPassword"
                    ).value;


                const status =
                    document.getElementById(
                        "registerStatus"
                    );


                // -----------------------------------------
                // Password length
                // -----------------------------------------

                if (password.length < 8) {

                    showRegisterError(
                        status,
                        "Password must contain at least 8 characters."
                    );

                    return;
                }


                // -----------------------------------------
                // Number validation
                // -----------------------------------------

                const numberCount =
                    (password.match(/\d/g) || []).length;


                if (numberCount < 2) {

                    showRegisterError(
                        status,
                        "Password must contain at least 2 numbers."
                    );

                    return;
                }


                // -----------------------------------------
                // Special character validation
                // -----------------------------------------

                if (!/[^A-Za-z0-9]/.test(password)) {

                    showRegisterError(
                        status,
                        "Password must contain at least 1 special character."
                    );

                    return;
                }


                // -----------------------------------------
                // Confirm password
                // -----------------------------------------

                if (password !== confirmPassword) {

                    showRegisterError(
                        status,
                        "Passwords do not match."
                    );

                    return;
                }


                status.textContent =
                    "Creating account...";

                status.className =
                    "auth-status";


                try {

                    const response =
                        await fetch(
                            "/auth/register",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body: JSON.stringify({

                                    hospital_name:
                                        hospitalName,

                                    admin_name:
                                        adminName,

                                    email:
                                        email,

                                    password:
                                        password

                                })
                            }
                        );


                    const data =
                        await response.json();


                    if (!response.ok) {

                        throw new Error(
                            data.detail ||
                            "Registration failed."
                        );

                    }


                    status.textContent =
                        "Account created successfully. Redirecting...";

                    status.className =
                        "auth-status success";


                    setTimeout(
                        function () {

                            window.location.href =
                                "/login.html";

                        },
                        1000
                    );


                } catch (error) {

                    status.textContent =
                        error.message;

                    status.className =
                        "auth-status error";

                }

            }
        );

    }


});


// =========================================================
// PASSWORD RULE UI
// =========================================================

function updatePasswordRule(
    elementId,
    valid
) {

    const element =
        document.getElementById(
            elementId
        );


    if (!element) {
        return;
    }


    const icon =
        element.querySelector("span");


    if (valid) {

        element.classList.add(
            "valid"
        );

        if (icon) {
            icon.textContent = "✓";
        }

    } else {

        element.classList.remove(
            "valid"
        );

        if (icon) {
            icon.textContent = "○";
        }

    }

}


// =========================================================
// REGISTER ERROR
// =========================================================

function showRegisterError(
    status,
    message
) {

    status.textContent =
        message;

    status.className =
        "auth-status error";

}