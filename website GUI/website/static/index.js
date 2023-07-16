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