document.addEventListener("DOMContentLoaded", function () {
    var southWest = L.latLng(19.0400, 72.8600);
    var northEast = L.latLng(19.1000, 72.9200);
    var bounds = L.latLngBounds(southWest, northEast);

    var map = L.map('map', {
        center: [19.0714, 72.8856],
        zoom: 14,
        minZoom: 14,
        maxZoom: 18,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Hardcoded reports
    var reports = [
        { lat: 19.075, lng: 72.885 },
        { lat: 19.0755, lng: 72.8852 },
        { lat: 19.085, lng: 72.890 },
        { lat: 19.090, lng: 72.885 },
        { lat: 19.0905, lng: 72.8845 },
        { lat: 19.065, lng: 72.880 },
        { lat: 19.0655, lng: 72.8802 },
        { lat: 19.0855, lng: 72.8905 },
        { lat: 19.0856, lng: 72.8906 },
        { lat: 19.0857, lng: 72.8907 }
    ];

    var gridSize = 0.005; // Defines grid cell size

    function getColor(count) {
        if (count >= 7) return 'red';
        if (count >= 5) return 'orange';
        if (count >= 3) return 'yellow';
        if (count >= 1) return 'lightgreen';
        return 'transparent';
    }

    function groupReportsByGrid(reports) {
        var groupedReports = {};

        reports.forEach(function (report) {
            var latIndex = Math.floor(report.lat / gridSize) * gridSize;
            var lngIndex = Math.floor(report.lng / gridSize) * gridSize;

            var gridKey = latIndex.toFixed(3) + "," + lngIndex.toFixed(3); // Rounding for consistency
            if (!groupedReports[gridKey]) {
                groupedReports[gridKey] = 0;
            }
            groupedReports[gridKey]++;
        });

        console.log("Grouped Reports:", groupedReports);
        return groupedReports;
    }

    function drawGrid() {
        var groupedReports = groupReportsByGrid(reports);

        for (var lat = 19.0400; lat < 19.1000; lat += gridSize) {
            for (var lng = 72.8600; lng < 72.9200; lng += gridSize) {
                var gridKey = lat.toFixed(3) + "," + lng.toFixed(3);
                var reportCount = groupedReports[gridKey] ? groupedReports[gridKey] : 0;
                var color = getColor(reportCount);

                L.rectangle([
                    [lat, lng],
                    [lat + gridSize, lng + gridSize]
                ], {
                    color: 'black',
                    weight: 0.2,
                    fillColor: color,
                    fillOpacity: 0.6 // Increased opacity for better visibility
                }).addTo(map);
            }
        }
    }

    drawGrid();
});
