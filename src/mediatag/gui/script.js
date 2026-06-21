// --- THEME ---
const toggle = document.getElementById('themeToggle');
const body = document.body;

toggle.addEventListener('click', () => {
    const isDark = body.getAttribute('data-theme') === 'dark';
    if (isDark) {
        body.removeAttribute('data-theme');
    } else {
        body.setAttribute('data-theme', 'dark');
    }
});

// --- UI HELPERS ---
const gel = (id) => document.getElementById(id);

// Called by Python
window.update_progress = function (current, total, msg_file, pct_file) {
    if (total > 0) {
        gel('barTotal').style.width = (current / total * 100) + '%';
        gel('lblTotal').innerText = `Batch Progress: ${current}/${total}`;
    }

    if (pct_file !== null) {
        gel('barFile').style.width = pct_file + '%';
    }

    if (msg_file) {
        gel('lblFile').innerText = msg_file;
        gel('statusL').innerText = msg_file;
    }
};

window.updateProgress = window.update_progress;

window.append_log = function (text) {
    const log = gel('logArea');
    log.innerText += text;
    log.scrollTop = log.scrollHeight;
};

window.appendLog = window.append_log;

window.set_cover = function (path) {
    const img = gel('coverImg');
    const ph = gel('coverPlaceholder');

    if (path && path.trim() !== "") {
        img.src = path + "?t=" + new Date().getTime();
        img.style.display = 'block';
        ph.style.display = 'none';
    } else {
        img.style.display = 'none';
        ph.style.display = 'block';
    }
};

window.setCover = window.set_cover;

window.set_path_input = function (path) {
    gel('pathText').innerText = path;
};

window.setCoverDir = window.set_path_input;

window.reset_ui = function () {
    gel('barTotal').style.width = '0%';
    gel('barFile').style.width = '0%';
    gel('lblTotal').innerText = 'Batch Progress: 0/0';
    gel('lblFile').innerText = 'Ready';
    gel('logArea').innerText = '';
    window.set_cover('');
};

window.resetUi = window.reset_ui;

// --- INIT ---
window.addEventListener('pywebviewready', async function () {
    console.log('PyWebview Ready');
    const state = await pywebview.api.init_app();
    window.set_path_input(state.coverDir);
});
