function initialize() {
    var mapOptions = {
        zoom: 16,
        center: new google.maps.LatLng(51.068858, 13.716050)
    };

    //ICONS
    var icondevday = "http://maps.google.com/mapfiles/kml/paddle/red-circle.png";
    var iconpark = "http://maps.google.com/mapfiles/kml/shapes/parking_lot_maps.png";



    //Der Marker für die Messe
    var iconBase = "http://maps.google.com/mapfiles/kml/paddle/";

    var map = new google.maps.Map(document.getElementById('map-div'),
                      mapOptions);
    new google.maps.Marker({
        position: new google.maps.LatLng(51.068858, 13.716060),
        map: map,
        icon: icondevday,
        title: "Dev Day 2015 \nDresden Messering 6"

    });

    //der Marker für den Parkplatz
    new google.maps.Marker({
        position: new google.maps.LatLng(51.067566, 13.719582),
        map: map,
        icon: iconpark
    });

    //Legende
    var legende = $("<div id='legende' style='background:#FFFFFF; position:absolute'></div>");

    var divs = [document.createElement('div'), document.createElement('div')];
    divs[0].innerHTML = "<img width='20em' height='20em' src='"+icondevday+"'> Dev Day";
    divs[1].innerHTML = "<img width='20em' height='20em' src='"+iconpark+"'> Parkplatz";
    legende[0].appendChild(divs[0]);
    legende[0].appendChild(divs[1]);

    map.controls[google.maps.ControlPosition.RIGHT_BOTTOM].push(legende[0]);


}

function loadScript() {
    var script = document.createElement('script');
    script.type = 'text/javascript';
    script.src = 'https://maps.googleapis.com/maps/api/js?v=3.exp' +
                  '&signed_in=true&callback=initialize';
    document.body.appendChild(script);
}

$(function () {
    if ($("#navButton").length == 0) {
        loadScript();
    }
    else {
        $("#map-link").show();
        $("#map-div").hide();
    }
});

