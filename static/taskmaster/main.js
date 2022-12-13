// Hide or unhide details (and change plus/minus controls)
function expand(id) {
    var details = document.getElementById("details" + id);
    var edit = document.getElementById("edit" + id);
    var label = document.getElementById("label" + id);
    if (details.style.display == "block") {
        details.style.display = "none";
        edit.style.display = "none";
        label.innerHTML = "&#8862; " + label.getAttribute("data-value");
    }
    else {
        details.style.display = "block";
        edit.style.display = "block";
        label.innerHTML = "&#8863; " + label.getAttribute("data-value");
    }
}

// Change the color of the background with the importance selector
function change_importance(id) {
    var importance = document.getElementById("importance" + id).value;
    var detail = document.getElementById("detail" + id)
    detail.classList.remove("low");
    detail.classList.remove("medium");
    detail.classList.remove("high");
    if (importance == 0)
        detail.classList.add("low");
    else if (importance == 1)
        detail.classList.add("medium");
    else
        detail.classList.add("high");
}

function show_new() {
    window.scrollTo(0, 0);
    document.getElementById('new_task').style.display = "block";
    document.body.style.overflow = "hidden";
}

function show_task(id) {
    window.scrollTo(0, 0);
    document.getElementById(id).style.display = "block";
    document.body.style.overflow = "hidden";
}

function hide() {
    location.reload();
}
