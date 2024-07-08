// Get the form element
const form = document.querySelector('form');

// Add event listener for form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault(); // Prevent default form submission

    // Get the file input element
    const fileInput = document.getElementById('file');

    // Create a FormData object to send the form data
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    try {
        // Send a POST request to the server to upload the file
        const response = await fetch('/import', {
            method: 'POST',
            body: formData
        });

        // Check if the response is successful
        if (response.ok) {
            // Parse the JSON response
            const data = await response.json();

            // Display a success message
            alert('File uploaded successfully!');
        } else {
            // Display an error message
            alert('Error uploading file. Please try again.');
        }
    } catch (error) {
        console.error('Error:', error);
        // Display an error message
        alert('Error uploading file. Please try again.');
    }
});