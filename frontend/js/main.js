
document.addEventListener('DOMContentLoaded', () => {
    const gigList = document.getElementById('gig-list');
    const authNav = document.getElementById('auth-nav');
    const postGigBtn = document.getElementById('post-gig-btn');
    const logoutBtn = document.getElementById('logout-btn');
    const token = localStorage.getItem('token');

    const dashboardBtn = document.getElementById('dashboard-btn');

    if (token) {
        authNav.style.display = 'none';
        postGigBtn.style.display = 'inline-block';
        dashboardBtn.style.display = 'inline-block';
        logoutBtn.style.display = 'inline-block';
    }

    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.reload();
    });

    const searchBar = document.getElementById('search-bar');
    const gigTypeFilter = document.getElementById('gig-type-filter');
    const suburbFilter = document.getElementById('suburb-filter');

    function fetchGigs() {
        const searchTerm = searchBar.value;
        const gigType = gigTypeFilter.value;
        const suburb = suburbFilter.value;

        let url = '/api/gigs?';
        if (searchTerm) url += `search=${searchTerm}&`;
        if (gigType) url += `gig_type=${gigType}&`;
        if (suburb) url += `suburb=${suburb}`;

        fetch(url)
            .then(response => response.json())
            .then(gigs => {
                gigList.innerHTML = '';
                gigs.forEach(gig => {
                    const card = document.createElement('div');
                    card.className = 'gig-card';
                    card.innerHTML = `
                        <h3><a href="profile.html?id=${gig.owner_id}">${gig.title}</a></h3>
                        <p><strong>Suburb:</strong> ${gig.suburb}</p>
                        <p><strong>Type:</strong> ${gig.gig_type}</p>
                        ${gig.image_url ? `<img src="${gig.image_url}" alt="${gig.title}" style="max-width: 100%;">` : ''}
                        <p>${gig.details}</p>
                        <button class="btn report-btn" data-id="${gig.id}">Report</button>
                        <button class="btn contact-btn" data-id="${gig.id}">Contact Poster</button>
                    `;
                    if (token) {
                        const decodedToken = JSON.parse(atob(token.split('.')[1]));
                        if (decodedToken.sub === gig.owner_username) { 
                            card.innerHTML += `<button class="btn complete-btn" data-id="${gig.id}">Mark as Complete</button>`;
                        }
                    }
                    gigList.appendChild(card);
                });
            });
    }

    searchBar.addEventListener('input', fetchGigs);
    gigTypeFilter.addEventListener('change', fetchGigs);
    suburbFilter.addEventListener('input', fetchGigs);

    fetchGigs();

    gigList.addEventListener('click', (e) => {
        if (e.target.classList.contains('report-btn')) {
            const gigId = e.target.dataset.id;
            fetch(`/api/gigs/${gigId}/report`, { method: 'POST' })
                .then(response => {
                    if (response.ok) {
                        alert('Gig reported!');
                    } else {
                        alert('Error reporting gig.');
                    }
                });
        }
        if (e.target.classList.contains('contact-btn')) {
            const gigId = e.target.dataset.id;
            openMessageModal(gigId);
        }
    });

    const messageModal = document.getElementById('message-modal');
    const closeBtn = document.querySelector('.close-btn');
    const messageHistory = document.getElementById('message-history');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    let currentGigId = null;

    function openMessageModal(gigId) {
        currentGigId = gigId;
        messageModal.style.display = 'block';
        loadMessages(gigId);
    }

    function loadMessages(gigId) {
        const token = localStorage.getItem('token');
        fetch(`/api/gigs/${gigId}/messages`, {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => response.json())
        .then(messages => {
            messageHistory.innerHTML = '';
            messages.forEach(msg => {
                const messageEl = document.createElement('div');
                messageEl.textContent = msg.content;
                messageHistory.appendChild(messageEl);
            });
        });
    }

    messageForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const content = messageInput.value;
        const token = localStorage.getItem('token');

        fetch(`/api/gigs/${currentGigId}/messages`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ content })
        })
        .then(() => {
            messageInput.value = '';
            loadMessages(currentGigId);
        });
    });

    closeBtn.onclick = function() {
        messageModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == messageModal) {
            messageModal.style.display = "none";
        }
    }
});
