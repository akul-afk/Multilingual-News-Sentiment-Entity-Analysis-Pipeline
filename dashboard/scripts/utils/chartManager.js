const _charts = {};

export function registerChart(id, instance) {
    _charts[id] = instance;
}

export function destroyChart(id) {
    if (_charts[id]) {
        _charts[id].destroy();
        delete _charts[id];
    }
}

export function destroyAll() {
    Object.keys(_charts).forEach(destroyChart);
}
