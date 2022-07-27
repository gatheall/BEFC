function initialize() {
        var mapCanvas = document.getElementById('destinations_map');
        var mapOptions = {
          center: new google.maps.LatLng(43.64619827, -70.30930328),
          zoom: 8,
          mapTypeId: google.maps.MapTypeId.ROADMAP
        }
        var map = new google.maps.Map(mapCanvas, mapOptions)
      }
      
$(document).ready(function () {
	google.maps.event.addDomListener(window, 'load', initialize);
});