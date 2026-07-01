function switchPage(pageId) {
    console.log("HELLO")
    document.querySelectorAll(".page").forEach(page => {
        page.classList.toggle("active", page.id === pageId);
    });

    document.querySelectorAll(".tab-button").forEach(button => {
        button.classList.toggle("active", button.dataset.page === pageId);
    });
}

function setupTabButtons() {
    document.querySelectorAll(".tab-button").forEach(button => {
        button.addEventListener("click", () => {
            switchPage(button.dataset.page)
        });
    });
}

function setupDetailSearchButton() {
    const detailSearchButton = document.getElementById("detail-search-button");

    detailSearchButton.addEventListener("click", async () => {
        const machineNo = document.getElementById("detail-machine-no").value;
        const productionDate = document.getElementById("detail-date").value;

        const imageData = await window.pywebview.api.get_detail_graph_images(
            machineNo,
            productionDate
        );

        console.log(imageData);
        drawBase64ImageToCanvas("state-diagram", imageData.state_diagram);
        drawBase64ImageToCanvas("state-bar-chart", imageData.state_bar_chart);
    });
}

function drawBase64ImageToCanvas(canvasId, base64Text) {
    const canvas = document.getElementById(canvasId);
    const context = canvas.getContext("2d");
    const image = new Image();

    image.onload = () => {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(image, 0, 0, canvas.width, canvas.height);
    };

    image.src = `data:image/png;base64,${base64Text}`;
}


document.addEventListener("DOMContentLoaded", () => {
    setupTabButtons();
});

window.addEventListener("pywebviewready", () => {
    setupDetailSearchButton();
});