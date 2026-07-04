function switchPage(pageId) {
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

async function setupMachineNoList() {
    const select = document.getElementById("detail-machine-no");

    const machineList = await window.pywebview.api.get_machine_no_list();

    select.innerHTML = "";

    machineList.forEach(machineNo => {
        const option = document.createElement("option");

        option.value = machineNo;
        option.textContent = machineNo;

        select.appendChild(option);
    });
}

function setupExportEachTimelinePngButton() {
    const button = document.getElementById("export-each-timeline-png-button");

    button.addEventListener("click", async () => {
        const productionDate = document.getElementById("detail-date").value;

        if (!productionDate) {
            alert("日付を選択してください。");
            return;
        }

        try {
            const result = await window.pywebview.api.export_each_machine_timeline_png_to_desktop(
                productionDate
            );

            alert(
                `画像出力が完了しました。\n\n` +
                `保存先:\n${result.output_dir}\n\n` +
                `出力枚数: ${result.file_count}枚`
            );

        } catch (error) {
            alert(`画像出力に失敗しました。\n${error}`);
        }
    });
}


document.addEventListener("DOMContentLoaded", () => {
    setupTabButtons();
    setupDefaultDate();
});

window.addEventListener("pywebviewready", async () => {
    await setupMachineNoList();
    setupDetailSearchButton();
    setupDetailInputEnter();
    setupExportEachTimelinePngButton();
});