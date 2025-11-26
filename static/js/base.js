// Update clock live
function updateClock() {
  const now = new Date();
  document.getElementById("clock").innerText =
    now.getHours().toString().padStart(2, '0') + ":" +
    now.getMinutes().toString().padStart(2, '0') + ":" +
    now.getSeconds().toString().padStart(2, '0');
}

document.addEventListener("DOMContentLoaded", function() {
  updateClock();
  setInterval(updateClock, 1000);
});
