var footprints_layer_style = {
    "color": "#0000ff",
    "weight": 1,
    "opacity": 0.5,
    "fillOpacity": 0.1,
};

function add_geojson_geometries(map) {
    var geoms = document.getElementsByClassName("geometry_ref");
    for (var i = 0; i < geoms.length; i++) {
        var jsonTest = new L.GeoJSON.AJAX(
        "geometry/" + geoms.item(i).id,
        {style: footprints_layer_style}).addTo(map);
    };
};

function map_init_callback(e){
    var detail = e.detail;
    add_geojson_geometries(detail.map)
};

window.addEventListener("map:init", map_init_callback, false);
