document.addEventListener("DOMContentLoaded", function () {
    var map = L.map('map', {
        center: [19.0714, 72.8856],
        zoom: 14,
        minZoom: 14,
        maxZoom: 18
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    // Function to locate the user
    function locateUser() {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        navigator.geolocation.getCurrentPosition(function (position) {
            var userLat = position.coords.latitude;
            var userLng = position.coords.longitude;

            var userMarker = L.marker([userLat, userLng], {
                title: "Your Location",
                icon: L.icon({
                    iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34]
                })
            }).addTo(map);

            userMarker.bindPopup("<b>You are here</b>").openPopup();
            map.setView([userLat, userLng], 16); // Zoom in to user's location
        }, function () {
            alert("Unable to retrieve your location.");
        });
    }

    // Add a button to find current location
    var locateButton = L.control({ position: "topright" });

    locateButton.onAdd = function () {
        var button = L.DomUtil.create("button", "locate-button");
        button.innerHTML = "📍 Find My Location";
        button.style.backgroundColor = "white";
        button.style.padding = "8px";
        button.style.cursor = "pointer";
        button.style.border = "1px solid black";
        button.style.borderRadius = "5px";
        button.onclick = locateUser;
        return button;
    };

    locateButton.addTo(map);

    var gridSize = 0.005;
    var gridLayers = [];

    function getColor(count) {
        if (count >= 7) return 'red';
        if (count >= 5) return 'orange';
        if (count >= 3) return 'yellow';
        if (count >= 1) return 'lightgreen';
        return 'transparent';
    }

    function groupReportsByGrid(reports) {
        var groupedReports = {};
        reports.forEach(report => {
            var latIndex = Math.floor(report.lat / gridSize) * gridSize;
            var lngIndex = Math.floor(report.lng / gridSize) * gridSize;
            var gridKey = latIndex.toFixed(3) + "," + lngIndex.toFixed(3);
            if (!groupedReports[gridKey]) groupedReports[gridKey] = 0;
            groupedReports[gridKey]++;
        });
        return groupedReports;
    }

    function highlightFeature(e) {
        var layer = e.target;
        layer.setStyle({
            weight: 2,
            color: '#666',
            fillOpacity: 0.9
        });

        // Show popup with crime count
        var popup = L.popup()
            .setLatLng(layer.getBounds().getCenter())
            .setContent("Crimes reported: " + layer.options.crimeCount)
            .openOn(map);
    }

    function resetHighlight(e) {
        e.target.setStyle({
            weight: 0.2,
            color: 'black',
            fillOpacity: 0.7
        });
        map.closePopup(); // Close popup when mouse leaves
    }

    function zoomToFeature(e) {
        map.fitBounds(e.target.getBounds());
    }

    function drawGrid(reports) {
        var groupedReports = groupReportsByGrid(reports);
<<<<<<< HEAD
    
        // Ensure the grid is drawn even if there are no reports
=======
>>>>>>> 470bb8e79e590cb9ea6c711203ca151d06c904b4
        for (var lat = 19.0300; lat < 19.1100; lat += gridSize) {
            for (var lng = 72.8500; lng < 72.9300; lng += gridSize) {
                var gridKey = lat.toFixed(3) + "," + lng.toFixed(3);
                var reportCount = groupedReports[gridKey] ? groupedReports[gridKey] : 0;
                var color = getColor(reportCount);
<<<<<<< HEAD
    
=======

>>>>>>> 470bb8e79e590cb9ea6c711203ca151d06c904b4
                var rectangle = L.rectangle([
                    [lat, lng],
                    [lat + gridSize, lng + gridSize]
                ], {
                    color: 'black',
                    weight: 0.2,
                    fillColor: color,
                    fillOpacity: 0.7,
                    crimeCount: reportCount
                }).addTo(map);
<<<<<<< HEAD
    
=======

>>>>>>> 470bb8e79e590cb9ea6c711203ca151d06c904b4
                rectangle.on({
                    mouseover: highlightFeature,
                    mouseout: resetHighlight,
                    click: zoomToFeature
                });
<<<<<<< HEAD
    
=======

>>>>>>> 470bb8e79e590cb9ea6c711203ca151d06c904b4
                gridLayers.push(rectangle);
            }
        }
    }
    

<<<<<<< HEAD
    // Fetch the reports from the backend and then draw the grid
    fetch('/get_reports')
        .then(response => response.json())
        .then(data => {
            console.log("Fetched reports:", data);  // Check if data is received
            drawGrid(data);  // Pass the data to drawGrid
        })
        .catch(error => console.error("Error fetching reports:", error));
=======
    fetch('/get_reports')
        .then(response => response.json())
        .then(data => drawGrid(data))
        .catch(error => console.error("Error fetching reports:", error));

    drawGrid();
>>>>>>> 470bb8e79e590cb9ea6c711203ca151d06c904b4
});
