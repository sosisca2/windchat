
function openHiddenPanel(panelId) {
    console.log(panelId)
    const panel = document.getElementById(panelId);
    panel.style.display = "flex";
}

function closeHiddenPanel(panelId) {
    console.log(panelId)
    const panel = document.getElementById(panelId);
    panel.style.display = "none";
}
