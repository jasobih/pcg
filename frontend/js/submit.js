
document.getElementById('submit-form').addEventListener('submit', (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const token = localStorage.getItem('token');

    fetch('/api/gigs', {
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
