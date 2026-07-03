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

    detailSearchButton.addEventListener("click", updateDetailGraph);
}

async function updateDetailGraph() {
    const machineNo = document.getElementById("detail-machine-no").value;
    const productionDate = document.getElementById("detail-date").value;

    const imageData = await window.pywebview.api.get_detail_graph_images(
        machineNo,
        productionDate
    );

    console.log(imageData);
    drawBase64ImageToCanvas("state-timeline", imageData.state_timeline);
    drawBase64ImageToCanvas("state-bar-chart", imageData.state_bar_chart);
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

function setupDefaultDate() {
    const dateInput = document.getElementById("detail-date");

    const today = new Date();

    // YYYY-MM-DD形式
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");

    dateInput.value = `${yyyy}-${mm}-${dd}`;
}

function setupDetailInputEnter() {
    const inputIds = [
        "detail-machine-no",
        "detail-date"
    ]

    inputIds.forEach(id => {

        document.getElementById(id).addEventListener("keydown", async (event) => {

            if (event.key === "Enter") {
                event.preventDefault();
                await updateDetailGraph();
            }
        });
    });
}



document.addEventListener("DOMContentLoaded", () => {
    setupTabButtons();
    setupDefaultDate();
});

window.addEventListener("pywebviewready", () => {
    setupDetailSearchButton();
    setupDetailInputEnter();
});