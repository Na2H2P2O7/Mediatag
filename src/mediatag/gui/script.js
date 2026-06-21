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
    refreshGlassSnapshot(420);
});

// --- UI HELPERS ---
const gel = (id) => document.getElementById(id);

// --- WEBGL LIQUID GLASS ---
window.glassControls = {
    edgeIntensity: 0.018,
    rimIntensity: 0.08,
    baseIntensity: 0.012,
    edgeDistance: 0.18,
    rimDistance: 0.72,
    baseDistance: 0.12,
    cornerBoost: 0.035,
    rippleEffect: 0.16,
    blurRadius: 4.5,
};

const glassElements = document.querySelectorAll(
    '.glass-btn-main, .btn-manual'
);

const liquidGlassInstances = [];

function setGlassUniforms(instance, values) {
    if (!instance || !instance.gl_refs || !instance.gl_refs.gl) return;

    const refs = instance.gl_refs;
    const gl = refs.gl;
    const map = {
        edgeIntensity: refs.edgeIntensityLoc,
        rimIntensity: refs.rimIntensityLoc,
        baseIntensity: refs.baseIntensityLoc,
        edgeDistance: refs.edgeDistanceLoc,
        rimDistance: refs.rimDistanceLoc,
        baseDistance: refs.baseDistanceLoc,
        cornerBoost: refs.cornerBoostLoc,
        rippleEffect: refs.rippleEffectLoc,
        blurRadius: refs.blurRadiusLoc,
        tintOpacity: refs.tintOpacityLoc,
    };

    Object.entries(values).forEach(([name, value]) => {
        const loc = map[name];
        if (loc) gl.uniform1f(loc, value);
    });

    if (instance.render) instance.render();
}

function mixGlassUniforms(from, to, amount) {
    const t = Math.max(0, Math.min(1, amount));
    const mixed = {};
    Object.keys(from).forEach((key) => {
        mixed[key] = from[key] + ((to[key] ?? from[key]) - from[key]) * t;
    });
    return mixed;
}

function setGlassTarget(instance, values) {
    if (!instance) return;

    instance._glassTarget = { ...values };
    if (!instance._glassCurrent) {
        instance._glassCurrent = { ...values };
        setGlassUniforms(instance, instance._glassCurrent);
        return;
    }

    if (!instance._glassAnimating) {
        instance._glassAnimating = true;
        requestAnimationFrame(() => animateGlassUniforms(instance));
    }
}

function animateGlassUniforms(instance) {
    if (!instance || !instance._glassCurrent || !instance._glassTarget) return;

    let moving = false;
    Object.keys(instance._glassTarget).forEach((key) => {
        const current = instance._glassCurrent[key] ?? instance._glassTarget[key];
        const target = instance._glassTarget[key];
        const next = current + (target - current) * 0.22;
        instance._glassCurrent[key] = Math.abs(next - target) < 0.0008 ? target : next;
        if (instance._glassCurrent[key] !== target) moving = true;
    });

    setGlassUniforms(instance, instance._glassCurrent);

    if (moving) {
        requestAnimationFrame(() => animateGlassUniforms(instance));
    } else {
        instance._glassAnimating = false;
    }
}

function refreshGlassSnapshot(delay = 120) {
    if (typeof Container === 'undefined' || typeof html2canvas === 'undefined') return;

    clearTimeout(refreshGlassSnapshot.timer);
    refreshGlassSnapshot.timer = setTimeout(() => {
        Container.pageSnapshot = null;
        Container.isCapturing = false;
        Container.waitingForSnapshot = [];
        html2canvas(document.body, {
            scale: 1,
            useCORS: true,
            allowTaint: true,
            backgroundColor: null,
            ignoreElements: (element) =>
                element.classList.contains('glass-container') ||
                element.classList.contains('liquid-glass-layer') ||
                element.classList.contains('liquid-glass-content'),
        }).then((snapshot) => {
            Container.pageSnapshot = snapshot;
            liquidGlassInstances.forEach((instance) => instance.initWebGL());
        }).catch((error) => {
            console.warn('Liquid glass snapshot failed:', error);
        });
    }, delay);
}

function installLiquidGlassHost(host, options = {}) {
    if (!host) return null;

    if (typeof Container === 'undefined' || typeof html2canvas === 'undefined') {
        host.classList.add('liquid-glass-fallback');
        return null;
    }

    const content = document.createElement('div');
    content.className = 'liquid-glass-content';
    while (host.firstChild) {
        content.appendChild(host.firstChild);
    }

    const instance = new Container({
        borderRadius: options.borderRadius || 16,
        type: 'rounded',
        tintOpacity: options.tintOpacity ?? 0.08,
    });

    instance.warp = options.warp ?? true;
    instance.element.classList.add('liquid-glass-layer');
    instance.element.style.borderRadius = `${options.borderRadius || 16}px`;
    instance.canvas.style.borderRadius = `${options.borderRadius || 16}px`;
    instance.canvas.style.boxShadow = 'none';

    host.classList.add('liquid-glass-host');
    host.prepend(instance.element);
    host.appendChild(content);
    liquidGlassInstances.push(instance);

    let idle = {
        edgeIntensity: 0.018,
        rimIntensity: 0.08,
        baseIntensity: 0.012,
        cornerBoost: 0.035,
        rippleEffect: 0.14,
        blurRadius: 4.5,
        tintOpacity: options.tintOpacity ?? 0.08,
    };
    let hover = {
        edgeIntensity: 0.052,
        rimIntensity: 0.15,
        baseIntensity: 0.024,
        cornerBoost: 0.072,
        rippleEffect: 0.28,
        blurRadius: 5.5,
        tintOpacity: options.tintOpacityHover ?? 0.11,
    };
    let press = {
        edgeIntensity: 0.075,
        rimIntensity: 0.19,
        baseIntensity: 0.035,
        cornerBoost: 0.09,
        rippleEffect: 0.34,
        blurRadius: 6.0,
        tintOpacity: options.tintOpacityPress ?? 0.13,
    };

    const refractionScale = options.refractionScale ?? 1;
    if (refractionScale !== 1) {
        const scaleRefraction = (state) => ({
            ...state,
            edgeIntensity: state.edgeIntensity * refractionScale,
            rimIntensity: state.rimIntensity * refractionScale,
            baseIntensity: state.baseIntensity * refractionScale,
            cornerBoost: state.cornerBoost * refractionScale,
            rippleEffect: state.rippleEffect * refractionScale,
        });
        idle = scaleRefraction(idle);
        hover = scaleRefraction(hover);
        press = scaleRefraction(press);
    }

    host._liquidGlass = {
        instance,
        idle,
        hover,
        press,
        pressed: false,
    };

    host.addEventListener('pointerenter', () => {
        host.classList.add('glass-hot');
    });
    host.addEventListener('pointerleave', () => {
        host.classList.remove('glass-hot', 'glass-pressed');
        host._liquidGlass.pressed = false;
        setGlassTarget(instance, idle);
        host.style.setProperty('--elastic-x', '0px');
        host.style.setProperty('--elastic-y', '0px');
    });
    host.addEventListener('pointerdown', () => {
        host.classList.add('glass-pressed');
        host._liquidGlass.pressed = true;
    });
    host.addEventListener('pointerup', () => {
        host.classList.remove('glass-pressed');
        host._liquidGlass.pressed = false;
    });
    host.addEventListener('pointercancel', () => {
        host.classList.remove('glass-pressed');
        host._liquidGlass.pressed = false;
        setGlassTarget(instance, idle);
    });

    requestAnimationFrame(() => {
        instance.updateSizeFromDOM();
        setGlassTarget(instance, idle);
    });

    return instance;
}

installLiquidGlassHost(document.querySelector('.glass-btn-main'), {
    borderRadius: 16,
    tintOpacity: 0.06,
    tintOpacityHover: 0.09,
    tintOpacityPress: 0.11,
});

glassElements.forEach((el) => {
    if (!el) return;
    el.addEventListener('transitionend', () => {
        liquidGlassInstances.forEach((instance) => {
            instance.updateSizeFromDOM();
            if (instance.render) instance.render();
        });
    });
});

window.addEventListener('pointermove', (event) => {
    body.style.setProperty('--mx', `${event.clientX}px`);
    body.style.setProperty('--my', `${event.clientY}px`);

    glassElements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width) * 100;
        const y = ((event.clientY - rect.top) / rect.height) * 100;
        const dx = event.clientX - (rect.left + rect.width / 2);
        const dy = event.clientY - (rect.top + rect.height / 2);
        const distance = Math.hypot(dx, dy);
        const pull = Math.max(0, 1 - distance / 260);
        const inside = x >= 0 && x <= 100 && y >= 0 && y <= 100;
        const normalizedDistance = distance / Math.max(rect.width, rect.height, 1);
        const centerPull = Math.max(0, 1 - normalizedDistance * 1.55);
        const edgePull = inside ? Math.max(
            0,
            1 - Math.min(x, y, 100 - x, 100 - y) / 34
        ) : 0;
        const glassAmount = inside
            ? Math.max(0.22, Math.min(1, centerPull * 0.72 + edgePull * 0.28))
            : 0;

        el.style.setProperty('--local-mx', `${Math.max(0, Math.min(100, x))}%`);
        el.style.setProperty('--local-my', `${Math.max(0, Math.min(100, y))}%`);
        el.style.setProperty('--elastic-x', `${(dx * pull * 0.012).toFixed(2)}px`);
        el.style.setProperty('--elastic-y', `${(dy * pull * 0.012).toFixed(2)}px`);
        el.style.setProperty('--glass-shine', `${0.08 + glassAmount * 0.20}`);
        el.style.setProperty('--glass-rim', `${0.50 + glassAmount * 0.26}`);

        if (el._liquidGlass) {
            const state = el._liquidGlass;
            const hoverTarget = mixGlassUniforms(state.idle, state.hover, glassAmount);
            const pressTarget = mixGlassUniforms(hoverTarget, state.press, state.pressed ? 0.78 : 0);
            setGlassTarget(state.instance, pressTarget);
        }
    });
});

window.addEventListener('pointerleave', () => {
    glassElements.forEach((el) => {
        el.style.setProperty('--elastic-x', '0px');
        el.style.setProperty('--elastic-y', '0px');
        el.style.setProperty('--glass-shine', '0.08');
        el.style.setProperty('--glass-rim', '0.50');

        if (el._liquidGlass) {
            el._liquidGlass.pressed = false;
            setGlassTarget(el._liquidGlass.instance, el._liquidGlass.idle);
        }
    });
});

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
