document.addEventListener("DOMContentLoaded", function () {
    // Map initialization with bounds
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
        console.log("Grouped Reports:", groupedReports);
    
        for (var lat = 19.040; lat < 19.100; lat += gridSize) {
            for (var lng = 72.830; lng < 72.970; lng += gridSize) {
                var gridKey = lat.toFixed(3) + "," + lng.toFixed(3);
                var reportCount = groupedReports[gridKey] || 0;
                var color = getColor(reportCount);
    
                var rectangle = L.rectangle([
                    [lat, lng],
                    [lat + gridSize, lng + gridSize]
                ], {
                    color: 'black',
                    weight: 0.2,
                    fillColor: color,
                    fillOpacity: 0.6,
                    crimeCount: reportCount  // Set crime count in options
                }).addTo(map);
    
                rectangle.on({
                    mouseover: highlightFeature,
                    mouseout: resetHighlight,
                    click: zoomToFeature
                });
            }
        }
    }

    fetch('/get_reports')
    .then(response => response.json())
    .then(data => {
        // Sort reports by timestamp in descending order (most recent first)
        data.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        displayReports(data); // Function to display reports on the admin page
    })
    .catch(error => console.error("Error fetching reports:", error));


    fetch('/get_reports')
    .then(response => response.json())
    .then(data => {
        drawGrid(data); // Pass fetched reports
    })
    .catch(error => console.error("Error fetching reports:", error));    

    // Add live location functionality
    var liveLocationMarker = null;
    
    function showLiveLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    var lat = position.coords.latitude;
                    var lng = position.coords.longitude;
                    
                    // Check if location is within bounds
                    if (lat >= southWest.lat && lat <= northEast.lat && 
                        lng >= southWest.lng && lng <= northEast.lng) {
                        
                        // Remove previous marker if exists
                        if (liveLocationMarker) {
                            map.removeLayer(liveLocationMarker);
                        }
                        
                        // Add new marker
                        liveLocationMarker = L.marker([lat, lng], {
                            icon: L.divIcon({
                                className: 'live-location-marker',
                                html: '<div class="pulse"></div>',
                                iconSize: [20, 20]
                            })
                        }).addTo(map);
                        
                        // Center map on location
                        map.setView([lat, lng], 16);
                    } else {
                        alert("Your location is outside the Kurla area.");
                    }
                },
                function(error) {
                    console.error("Error getting location:", error);
                    alert("Could not get your location. Please check your location permissions.");
                }
            );
        } else {
            alert("Geolocation is not supported by your browser.");
        }
    }
    
    // Add live location button
    var liveLocationControl = L.control({position: 'topleft'});
    liveLocationControl.onAdd = function(map) {
        var div = L.DomUtil.create('div', 'live-location-control');
        div.innerHTML = `
            <button id="liveLocationBtn" class="location-btn" title="Show my location">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M8 0a.5.5 0 0 1 .5.5v.518A7 7 0 0 1 14.982 7.5h.518a.5.5 0 0 1 0 1h-.518A7 7 0 0 1 8.5 14.982v.518a.5.5 0 0 1-1 0v-.518A7 7 0 0 1 1.018 8.5H.5a.5.5 0 0 1 0-1h.518A7 7 0 0 1 7.5 1.018V.5A.5.5 0 0 1 8 0zm0 2a6 6 0 1 0 0 12A6 6 0 0 0 8 2z"/>
                    <path d="M8 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6zM6 8a2 2 0 1 1 4 0 2 2 0 0 1-4 0z"/>
                </svg>
            </button>
        `;
        return div;
    };
    liveLocationControl.addTo(map);
    
    // Add event listener to the live location button
    document.getElementById('liveLocationBtn').addEventListener('click', showLiveLocation);

    // News Analysis Layer functionality
    // Initialize news data layer as null
    let newsDataLayer = null;
    let newsLegend = null;

    // Add a toggle button for news data layer
    const newsLayerControl = L.control({position: 'topright'});
    newsLayerControl.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'news-layer-control');
        div.innerHTML = `
            <div style="background-color: white; padding: 8px; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,0.4);">
                <label>
                    <input type="checkbox" id="newsLayerToggle"> Show News Analysis
                </label>
            </div>
        `;
        return div;
    };
    newsLayerControl.addTo(map);

    // Function to load and display news data
    function loadNewsData() {
        // Remove existing layer if it exists
        if (newsDataLayer) {
            map.removeLayer(newsDataLayer);
            newsDataLayer = null;
        }

        // Remove existing legend if it exists
        if (newsLegend) {
            map.removeControl(newsLegend);
            newsLegend = null;
        }

        // Fetch news data
        fetch('/api/safety-data')
            .then(response => {
                if (!response.ok) {
                    throw new Error('News data not available. Run the news analysis first.');
                }
                return response.json();
            })
            .then(data => {
                // Create GeoJSON layer
                newsDataLayer = L.geoJSON(data, {
                    pointToLayer: function(feature, latlng) {
                        // Determine marker color based on safety level
                        let markerColor;
                        switch(feature.properties.safety_level) {
                            case 'green':
                                markerColor = 'green';
                                break;
                            case 'yellow':
                                markerColor = 'yellow';
                                break;
                            case 'red':
                                markerColor = 'red';
                                break;
                            default:
                                markerColor = 'blue';
                        }
                
                        return L.circleMarker(latlng, {
                            radius: 8,
                            fillColor: markerColor,
                            color: '#000',
                            weight: 1,
                            opacity: 1,
                            fillOpacity: 0.8
                        });
                    },
                    onEachFeature: function(feature, layer) {
                        // Add popup with information
                        layer.bindPopup(`
                            <strong>${feature.properties.name}</strong><br>
                            Crime mentions: ${feature.properties.crime_count}<br>
                            Safety level: ${feature.properties.safety_level}
                        `);
                    }
                }).addTo(map);
        
                // Add legend for news data
                newsLegend = L.control({position: 'bottomright'});
                newsLegend.onAdd = function(map) {
                    const div = L.DomUtil.create('div', 'info legend');
                    div.innerHTML = `
                        <div style="background-color: white; padding: 10px; border-radius: 5px;">
                            <h4>Safety Analysis</h4>
                            <div><i style="background: green; width: 15px; height: 15px; display: inline-block;"></i> Safe</div>
                            <div><i style="background: yellow; width: 15px; height: 15px; display: inline-block;"></i> Moderate Risk</div>
                            <div><i style="background: red; width: 15px; height: 15px; display: inline-block;"></i> High Risk</div>
                            <small>Based on news analysis and crime data</small>
                        </div>
                    `;
                    return div;
                };
                newsLegend.addTo(map);
            })
            .catch(error => {
                console.error('Error loading news data:', error);
                alert(error.message || 'Failed to load news data');
            });
    }

    // Toggle news data layer when checkbox is clicked
    document.getElementById('newsLayerToggle').addEventListener('change', function() {
        if (this.checked) {
            loadNewsData();
        } else {
            if (newsDataLayer) {
                map.removeLayer(newsDataLayer);
                newsDataLayer = null;
            }
            if (newsLegend) {
                map.removeControl(newsLegend);
                newsLegend = null;
            }
        }
    });

    // Add some CSS for the live location marker
    const style = document.createElement('style');
    style.textContent = `
        .live-location-marker {
            background: transparent;
        }
        .pulse {
            width: 20px;
            height: 20px;
            background: rgba(0, 128, 255, 0.7);
            border-radius: 50%;
            position: relative;
        }
        .pulse:after {
            content: "";
            position: absolute;
            top: -10px;
            left: -10px;
            width: 40px;
            height: 40px;
            background: rgba(0, 128, 255, 0.3);
            border-radius: 50%;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% {
                transform: scale(0.5);
                opacity: 1;
            }
            100% {
                transform: scale(1.5);
                opacity: 0;
            }
        }
        .location-btn {
            background: white;
            border: 2px solid rgba(0,0,0,0.2);
            border-radius: 4px;
            padding: 5px;
            cursor: pointer;
        }
        .location-btn:hover {
            background:rgb(26, 20, 20);
        }
    `;
    document.head.appendChild(style);

    // Export map object for potential use in other scripts
    window.safeStepsMap = map;
});