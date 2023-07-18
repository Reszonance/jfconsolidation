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

function delete_package(pk_id) {
  // sends post request to delete-note endpoint
fetch('/delete-package', {
  method: 'POST',
  body: JSON.stringify({pk_id: pk_id})
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