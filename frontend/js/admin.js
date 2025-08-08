
document.addEventListener('DOMContentLoaded', () => {
    const apiKey = prompt('Enter Admin API Key:');
    if (!apiKey) return;

    const flaggedGigs = document.getElementById('flagged-gigs');

    fetch('/api/admin/flagged', { headers: { 'X-API-KEY': apiKey } })
        .then(response => response.json())
        .then(gigs => {
            gigs.forEach(gig => {
                const card = document.createElement('div');
                card.className = 'gig-card';
                card.innerHTML = `
                    <h3>${gig.title}</h3>
                    <p><strong>Suburb:</strong> ${gig.suburb}</p>
                    <p><strong>Reports:</strong> ${gig.report_count}</p>
                    <button class="btn approve-btn" data-id="${gig.id}">Approve</button>
                    <button class="btn delete-btn" data-id="${gig.id}">Delete</button>
                `;
                flaggedGigs.appendChild(card);
            });
        });

    flaggedGigs.addEventListener('click', (e) => {
        const gigId = e.target.dataset.id;
        if (e.target.classList.contains('approve-btn')) {
            fetch(`/api/admin/gigs/${gigId}/approve`, { 
                method: 'POST',
                headers: { 'X-API-KEY': apiKey }
            }).then(() => e.target.closest('.gig-card').remove());
        }
        if (e.target.classList.contains('delete-btn')) {
            fetch(`http://localhost:8000/api/admin/gigs/${gigId}`, { 
                method: 'DELETE',
                headers: { 'X-API-KEY': apiKey }
            }).then(() => e.target.closest('.gig-card').remove());
        }
    });
});
