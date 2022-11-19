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
function change_importance() {
    var importance = document.getElementById("importance").value;
    var detail = document.getElementById("detail")
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

// If any change is made, then raise the flag
function changed() {
    document.getElementById("changes_made").value = 1;
}

// Prevent a user from leaving site with unsaved changes
function unsaved_changes() {
    if (document.getElementById("changes_made").value > 0)
        return confirm("You have unsaved changes.  Are you sure you wish to exit?");
    else
        return true;
}