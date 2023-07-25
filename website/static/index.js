// images, css, javascript files go here
// anything that doesn't change
function deleteNote(noteId) {
    // sends post request to delete-note endpoint
  fetch('/delete-note', {
    method: 'POST',
    body: JSON.stringify({noteId: noteId})
  }).then((_res) => {
    window.location.href = '/';
  })
}

function delete_package(pk_id, delete_type = "permanent") {
  // sends post request to delete-note endpoint
fetch('/delete-package', {
  method: 'POST',
  body: JSON.stringify({pk_id: pk_id, delete_type: delete_type})
}).then((_res) => {
  window.location.href = '/';
})
}

function consolidate_package(checked_items) {
  fetch('/consolidate-packages', {
    method: 'POST',
    body: JSON.stringify(checked_items),
  }).then((_res) => {
    console.log('redirect after consolidating');
    window.location.href = '/';
  })
}

function toggleView(packageId) {
  var viewForm = document.getElementById("view-form-" + packageId);
  if (viewForm.style.display === "none") {
    viewForm.style.display = "block";
  } else {
    viewForm.style.display = "none";
  }
}
