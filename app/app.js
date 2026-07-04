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
    const button = document.getElementById("detail-search-button");

    button.addEventListener("click",  async () => {
        await runButtonTask(button, updateDetailGraph);
    });
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

    const button = document.getElementById("detail-search-button");

    inputIds.forEach(id => {

        document.getElementById(id).addEventListener("keydown", async (event) => {

            if (event.key === "Enter") {
                event.preventDefault();
                await runButtonTask(button, updateDetailGraph);
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
        await runButtonTask(button, exportEachTimelinePng);
    });

}

async function exportEachTimelinePng() {

    if (!confirm(
        "設備タイムライン画像をデスクトップへ出力します。\n\n続行しますか？"
    )) {
        return;
    }

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
}

function setupTrendDefaultInputs() {
    const dateInput = document.getElementById("trend-base-date");
    const daysInput = document.getElementById("trend-display-days");

    const today = new Date();

    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    dateInput.value = `${yyyy}-${mm}-${dd}`;
    daysInput.value = 30;
}

async function setupTrendMachineNoList() {
    const select = document.getElementById("trend-machine-no");

    const machineList = await window.pywebview.api.get_machine_no_list();
    
    select.innerHTML = "";

    machineList.forEach(machineNo => {
        const option = document.createElement("option");

        option.value = machineNo;
        option.textContent = machineNo;

        select.appendChild(option);
    });
}

function setupTrendSearchButton() {
    const button = document.getElementById("trend-search-button");

    button.addEventListener("click", async () => {
        await runButtonTask(button, updateTrendGraph);
    });
}

async function updateTrendGraph() {
    const machineNo = document.getElementById("trend-machine-no").value;
    const baseDate = document.getElementById("trend-base-date").value;
    const displayDays = document.getElementById("trend-display-days").value;

    const imageData = await window.pywebview.api.get_machine_trend_graph_images(
      machineNo,
      baseDate,
      displayDays  
    );

    drawBase64ImageToCanvas(
        "trend-actual-count-chart",
        imageData.actual_count
    );

    drawBase64ImageToCanvas(
        "trend-alarm-count-chart",
        imageData.alarm_count
    );
}

function setupTrendInputEnter() {
    const inputIds = [
        "trend-machine-no",
        "trend-base-date",
        "trend-display-days"
    ];

    const button = document.getElementById("trend-search-button");

    inputIds.forEach(id => {
        document.getElementById(id).addEventListener("keydown", async (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                await runButtonTask(button, updateTrendGraph);
            }
        });
    });
}

async function runButtonTask(button, task) {
    const originalText = button.textContent;

    button.disabled = true;
    button.textContent = "処理中...";

    try {
        await task();
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    setupTabButtons();
    setupDefaultDate();
    setupTrendDefaultInputs();
});

window.addEventListener("pywebviewready", async () => {
    await setupMachineNoList();
    await setupTrendMachineNoList();

    setupDetailSearchButton();
    setupDetailInputEnter();
    setupExportEachTimelinePngButton();

    setupTrendSearchButton();
    setupTrendInputEnter();
});