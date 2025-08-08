
document.addEventListener('DOMContentLoaded', () => {
    const userProfile = document.getElementById('user-profile');
    const userReviews = document.getElementById('user-reviews');
    const urlParams = new URLSearchParams(window.location.search);
    const userId = urlParams.get('id');

    if (userId) {
        fetch(`/api/users/${userId}`)
            .then(response => response.json())
            .then(user => {
                userProfile.innerHTML = `
                    <h2>${user.username}</h2>
                    <p>${user.bio || 'No bio yet.'}</p>
                `;
            });

        fetch(`http://localhost:8000/api/users/${userId}/reviews`)
            .then(response => response.json())
            .then(reviews => {
                reviews.forEach(review => {
                    const reviewEl = document.createElement('div');
                    reviewEl.className = 'review-card';
                    reviewEl.innerHTML = `
                        <p><strong>Rating:</strong> ${review.rating}/5</p>
                        <p>${review.comment}</p>
                    `;
                    userReviews.appendChild(reviewEl);
                });
            });
    }
});
