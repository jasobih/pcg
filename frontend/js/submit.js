document.getElementById('submit-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const title = document.getElementById('title').value;
    const gig_type = document.querySelector('input[name="gig_type"]:checked').value;
    const suburb = document.getElementById('suburb').value;
    const details = document.getElementById('details').value;
    const image = document.getElementById('image').files[0];
    const token = localStorage.getItem('token');

    const formData = new FormData();
    formData.append('title', title);
    formData.append('gig_type', gig_type);
    formData.append('suburb', suburb);
    formData.append('details', details);
    if (image) {
        formData.append('image', image);
    }

    fetch('http://localhost:8000/api/gigs', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`
        },
        body: formData
    })
    .then(response => {
        if (response.status === 201) {
            window.location.href = 'index.html';
        } else {
            alert('Error submitting gig.');
        }
    });
});