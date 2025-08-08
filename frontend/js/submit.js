document.getElementById('submit-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const title = document.getElementById('title').value;
    const gig_type = document.querySelector('input[name="gig_type"]:checked').value;
    const suburb = document.getElementById('suburb').value;
    const details = document.getElementById('details').value;
    const image = document.getElementById('image').files[0];
    const token = localStorage.getItem('token');

    const gigData = {
        title,
        gig_type,
        suburb,
        details
    };

    try {
        // Step 1: Create the gig
        const gigResponse = await fetch('http://51.161.134.191/api/gigs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(gigData)
        });

        if (!gigResponse.ok) {
            const errorData = await gigResponse.json();
            throw new Error(`Error creating gig: ${errorData.detail}`);
        }

        const createdGig = await gigResponse.json();

        // Step 2: If there's an image, upload it
        if (image) {
            const formData = new FormData();
            formData.append('image', image);

            const imageResponse = await fetch(`http://51.161.134.191/api/gigs/${createdGig.id}/upload-image`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: formData
            });

            if (!imageResponse.ok) {
                const errorData = await imageResponse.json();
                throw new Error(`Error uploading image: ${errorData.detail}`);
            }
        }

        // Step 3: Redirect to home page
        window.location.href = 'index.html';

    } catch (error) {
        console.error('Submission failed:', error);
        alert(`An error occurred: ${error.message}`);
    }
});
