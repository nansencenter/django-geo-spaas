var footprints_layer_style = {
    "color": "#0000ff",
    "weight": 1,
    "opacity": 0.9,
    "fillOpacity": 0.1,
};

var polygons = {};

$(document).ready(function(){
  $(".dataset_row").each(function(){
    polygons[$(this).attr("ajax_url")] = new L.GeoJSON.AJAX(
        $(this).attr("ajax_url"),
        {style: footprints_layer_style}).addTo(window.maps[0]);
  });

  $(".dataset_row").hover(
  function(){
    $(this).css("background-color", "#ffeeee");
    polygons[$(this).attr("ajax_url")].setStyle({color: '#ff0000'});
   },
  function(){
    $(this).css("background-color", "#ffffff");
    polygons[$(this).attr("ajax_url")].setStyle({color: '#0000ff'});
  },
  );
});
