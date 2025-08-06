
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    const bioForm = document.getElementById('profile-form');
    const bioTextarea = document.getElementById('bio');
    const myGigsList = document.getElementById('my-gigs-list');
    const myMessagesList = document.getElementById('my-messages-list');

    const reviewModal = document.getElementById('review-modal');
    const reviewCloseBtn = reviewModal.querySelector('.close-btn');
    const modalReviewForm = document.getElementById('modal-review-form');
    let currentReviewGigId = null;

    reviewCloseBtn.onclick = function() {
        reviewModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == reviewModal) {
            reviewModal.style.display = "none";
        }
    }

    // Fetch and display user profile
    fetch('/api/users/me', {
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(user => {
        bioTextarea.value = user.bio || '';
    });

    // Update profile
    bioForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const bio = bioTextarea.value;
        fetch('/api/users/me', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ bio })
        })
        .then(response => {
            if (response.ok) {
                alert('Profile updated!');
            } else {
                alert('Error updating profile.');
            }
        });
    });

    // Fetch and display user's gigs
    fetch('/api/gigs/me', { 
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(gigs => {
        gigs.forEach(gig => {
            const gigEl = document.createElement('div');
            gigEl.className = 'gig-card';
            gigEl.innerHTML = `
                <h3>${gig.title}</h3>
                <p>Status: ${gig.status}</p>
            `;
            if (gig.status === 'COMPLETED') {
                gigEl.innerHTML += `<button class="btn leave-review-btn" data-id="${gig.id}">Leave Review</button>`;
            }
            myGigsList.appendChild(gigEl);
        });
    });

    myGigsList.addEventListener('click', (e) => {
        if (e.target.classList.contains('leave-review-btn')) {
            currentReviewGigId = e.target.dataset.id;
            reviewModal.style.display = 'block';
        }
    });

    modalReviewForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());

        fetch(`/api/gigs/${currentReviewGigId}/reviews`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (response.ok) {
                alert('Review submitted!');
                reviewModal.style.display = 'none';
                // Optionally refresh gigs or reviews
            } else {
                alert('Error submitting review.');
            }
        });
    });

    // Fetch and display user's messages (a simplified view)
    // A more robust implementation would group messages by gig
    fetch('/api/messages/me', { 
        headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => response.json())
    .then(messages => {
        messages.forEach(message => {
            const messageEl = document.createElement('div');
            messageEl.textContent = `Message on gig #${message.gig_id}: ${message.content}`;
            myMessagesList.appendChild(messageEl);
        });
    });
});
