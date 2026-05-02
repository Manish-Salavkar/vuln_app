const params = new URLSearchParams(window.location.search);
const q = params.get("q");

const output = document.getElementById("output");

if (q) {
    output.textContent = `You searched for: ${q}`;
}