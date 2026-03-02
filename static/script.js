// 🔴 DOM XSS
const params = new URLSearchParams(window.location.search);
const q = params.get("q");

if (q) {
    document.getElementById("output").innerHTML = q;  // Dangerous
}