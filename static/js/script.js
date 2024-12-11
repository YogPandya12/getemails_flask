
function uploadFile(event) {
    event.preventDefault(); 

    const form = document.querySelector('form');
    const fileInput = document.querySelector('#file');
    const statusMessage = document.querySelector('#status');

    statusMessage.classList.remove('error', 'success'); 
    statusMessage.innerHTML = "Fetching email IDs, please wait..."; 

    const formData = new FormData(form);

    fetch('/process', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            return response.blob(); 
        }
        throw new Error('File processing failed');
    })
    .then(blob => {
        const originalFileName = fileInput.files[0].name; 
        const processedFileName = `processed_${originalFileName}`; 

        const downloadLink = document.createElement('a');
        const url = window.URL.createObjectURL(blob);
        downloadLink.href = url;
        downloadLink.download = processedFileName; 

        statusMessage.innerHTML = "File downloaded!";
        statusMessage.classList.add('success');

        downloadLink.click();
    })
    .catch(error => {
        console.error("Error:", error); 
        statusMessage.innerHTML = `Error: ${error.message}`;
        statusMessage.classList.add('error');
    });
}
