function login() {
    let email = document.getElementById('loginEmail').value;
    let password = document.getElementById('loginPassword').value;
    let type = document.getElementById('problemType').value;

    if (email && password && type) {
        alert(`Logged in for ${type} issues`);
        // Redirect based on selection
        if (type === "hardware") {
            window.location.href = "hardware_dashboard.html";
        } else {
            window.location.href = "software_dashboard.html";
        }
    } else {
        alert("Please fill all fields.");
    }
}

function signup() {
    let name = document.getElementById('signupUsername').value;
    let email = document.getElementById('signupEmail').value;
    let password = document.getElementById('signupPassword').value;

    if (name && email && password) {
        alert("Account created! Please log in.");
        window.location.href = "index.html";
    } else {
        alert("Please fill all fields.");
    }
}
