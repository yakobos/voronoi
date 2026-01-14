var map = L.map('map').setView([51.5074, -0.1278], 10);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

var markers = [];
var points = initialPoints;
var voronoiLayer = null;
var selectedPolygonIndex = null;
var selectedLayer = null;

var letterColors = {
    'A': '#e6194b', 'B': '#3cb44b', 'C': '#ffe119', 'D': '#4363d8',
    'E': '#f58231', 'F': '#911eb4', 'G': '#46f0f0', 'H': '#f032e6',
    'I': '#bcf60c', 'J': '#fabebe', 'K': '#008080', 'L': '#e6beff',
    'M': '#9a6324', 'N': '#fffac8', 'O': '#800000', 'P': '#aaffc3',
    'Q': '#808000', 'R': '#ffd8b1', 'S': '#000075', 'T': '#808080',
    'U': '#ff6f61', 'V': '#6b5b95', 'W': '#88b04b', 'X': '#f7cac9',
    'Y': '#92a8d1', 'Z': '#955251'
};

var defaultColor = '#999999';

function updateCount() {
    document.getElementById('point-count').textContent = markers.length;
}

function getPolygonColor(category) {
    if (category && letterColors[category.toUpperCase()]) {
        return letterColors[category.toUpperCase()];
    }
    return defaultColor;
}

function updateSelectedInfo() {
    var infoDiv = document.getElementById('selected-info');
    var categorySpan = document.getElementById('selected-category');
    var badge = document.getElementById('category-badge');
    
    if (selectedPolygonIndex !== null && markers[selectedPolygonIndex]) {
        infoDiv.style.display = 'block';
        var cat = markers[selectedPolygonIndex].category || null;
        if (cat) {
            categorySpan.textContent = cat.toUpperCase();
            badge.style.display = 'inline-block';
            badge.textContent = cat.toUpperCase();
            badge.style.backgroundColor = getPolygonColor(cat);
        } else {
            categorySpan.textContent = 'None (gray)';
            badge.style.display = 'none';
        }
    } else {
        infoDiv.style.display = 'none';
    }
}

function selectPolygon(index, layer) {
    if (selectedLayer) {
        selectedLayer.setStyle({ weight: 2, color: '#333' });
    }
    
    selectedPolygonIndex = index;
    selectedLayer = layer;
    
    if (layer) {
        layer.setStyle({ weight: 4, color: '#000' });
    }
    
    updateSelectedInfo();
}

function deselectPolygon() {
    if (selectedLayer) {
        selectedLayer.setStyle({ weight: 2, color: '#333' });
    }
    selectedPolygonIndex = null;
    selectedLayer = null;
    updateSelectedInfo();
}

function updateVoronoi() {
    fetch('/voronoi')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (voronoiLayer) {
                map.removeLayer(voronoiLayer);
            }
            selectedLayer = null;
            
            if (data.geojson) {
                voronoiLayer = L.geoJSON(data.geojson, {
                    style: function(feature) {
                        var cat = feature.properties.category;
                        var isSelected = feature.properties.point_index === selectedPolygonIndex;
                        return {
                            fillColor: getPolygonColor(cat),
                            weight: isSelected ? 4 : 2,
                            opacity: 1,
                            color: isSelected ? '#000' : '#333',
                            fillOpacity: 0.5
                        };
                    },
                    onEachFeature: function(feature, layer) {
                        layer.on('click', function(e) {
                            if (e.originalEvent.shiftKey) {
                                L.DomEvent.stopPropagation(e);
                                var idx = feature.properties.point_index;
                                selectPolygon(idx, layer);
                            }
                        });
                        
                        if (feature.properties.point_index === selectedPolygonIndex) {
                            selectedLayer = layer;
                        }
                    }
                }).addTo(map);
                voronoiLayer.bringToBack();
                updateSelectedInfo();
            }
        })
        .catch(err => console.error('Voronoi fetch error:', err));
}

function addMarker(lat, lng, category, saveToServer) {
    var marker = L.circleMarker([lat, lng], {
        radius: 8,
        fillColor: "#ff4444",
        color: "#aa0000",
        weight: 2,
        fillOpacity: 0.9
    }).addTo(map);
    
    marker.lat = lat;
    marker.lng = lng;
    marker.category = category || null;
    
    marker.on('click', function(e) {
        L.DomEvent.stopPropagation(e);
        map.removeLayer(marker);
        var idx = markers.indexOf(marker);
        if (selectedPolygonIndex === idx) {
            deselectPolygon();
        } else if (selectedPolygonIndex !== null && selectedPolygonIndex > idx) {
            selectedPolygonIndex--;
        }
        markers = markers.filter(m => m !== marker);
        updateCount();
        savePoints();
    });
    
    markers.push(marker);
    marker.bringToFront();
    updateCount();
    
    if (saveToServer) {
        savePoints();
    }
}

function savePoints() {
    var pointData = markers.map(m => ({
        lat: m.lat, 
        lng: m.lng,
        category: m.category
    }));
    fetch('/save_points', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(pointData)
    }).then(() => {
        updateVoronoi();
    });
}

points.forEach(function(p) {
    addMarker(p.lat, p.lng, p.category, false);
});

if (markers.length > 0) {
    var group = L.featureGroup(markers);
    map.fitBounds(group.getBounds().pad(0.1));
}

updateVoronoi();

map.on('click', function(e) {
    if (selectedPolygonIndex !== null) {
        deselectPolygon();
    } else {
        addMarker(e.latlng.lat, e.latlng.lng, null, true);
    }
});

document.addEventListener('keydown', function(e) {
    if (selectedPolygonIndex === null) return;
    
    if (e.key === 'Escape') {
        deselectPolygon();
        return;
    }
    
    var key = e.key.toUpperCase();
    if (key >= 'A' && key <= 'Z' && key.length === 1) {
        markers[selectedPolygonIndex].category = key;
        savePoints();
    }
});
