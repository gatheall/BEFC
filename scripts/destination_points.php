<?php 
header('Content-Type: application/x-javascript');

function check_url($url) {
   $headers = @get_headers($url);
   $headers = (is_array($headers)) ? implode( "\n ", $headers) : $headers;
   //print_r($headers);
   //print $url;
   return (bool)preg_match('#^HTTP/.*\s+[(200|301|302)]+\s#i', $headers);
}

function checkRemoteFile($url)
{
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL,$url);
    // don't download content
    curl_setopt($ch, CURLOPT_NOBODY, 1);
    curl_setopt($ch, CURLOPT_FAILONERROR, 1);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    if(curl_exec($ch)!==FALSE)
    {
        return true;
    }
    else
    {
        return false;
    }
}
print "function initialize() {
        var mapCanvas = document.getElementById('destinations_map');
        var mapOptions = {
          center: new google.maps.LatLng(43.64619827, -70.30930328),
          zoom: 8,
          mapTypeId: google.maps.MapTypeId.HYBRID
        }
        map = new google.maps.Map(mapCanvas, mapOptions);
		";

require("../common.php");

$query = "select distinct dst.airport_ident, ap.name, ap.latitude_deg, ap.longitude_deg, ap.elevation_ft, ap.municipality, ap.wikipedia_link, ap.home_link  from destinations dst
		  join airports ap
		  on ap.ident = dst.airport_ident";

try 
{ 
	// Execute the query 
	$stmt = $db->prepare($query); 
	$result = $stmt->execute(); 
} 
catch(PDOException $ex) 
{ 
	// Note: On a production website, you should not output $ex->getMessage(). 
	// It may provide an attacker with helpful information about your code.  
	die("Failed to run query: " . $ex->getMessage()); 
}
$rows = $stmt->fetchall();
$marker_count=1;
foreach($rows as $row) {
	
	$flightaware_diagram_link="";
	
	$flightaware_url='http://flightaware.com/resources/airport/'.$row['airport_ident'].'/summary';
	$flightaware_diagram='http://flightaware.com/resources/airport/'.$row['airport_ident'].'/APD/AIRPORT+DIAGRAM/png/1';
	$flightaware_diagram_pdf='http://flightaware.com/resources/airport/'.$row['airport_ident'].'/APD/AIRPORT+DIAGRAM/pdf';
	
	// Airports table holds a "flightaware_checked" field
	// A 0 means we haven't checked flightaware for a valid diagram yet
	// A 1 means we have checked and found a valid flightaware diagram
	// A 2 means we have checked and found there isn't a valid diagram
	
	$query = "select flightaware_checked
		from airports
		where ident = :airport_ident";	
	$query_params = array(
		':airport_ident' => $row['airport_ident']
		);
	try 
	{ 
		// Execute the query 
		$stmt = $db->prepare($query); 
		$result = $stmt->execute($query_params); 
	} 
	catch(PDOException $ex) 
	{ 
		// Note: On a production website, you should not output $ex->getMessage(). 
		// It may provide an attacker with helpful information about your code.  
		die("Failed to run query: " . $ex->getMessage()); 
	}
	$fac = $stmt->fetch();
	
	//print "DEBUG: ".$fac['flightaware_checked'];
	
	if($fac['flightaware_checked'] == 1) {
		//print "DEBUG: got 1 for ".$row['airport_ident'];
		$flightaware_diagram_link="<a href=\"".$flightaware_diagram_pdf."\"><img src=\"".$flightaware_diagram."\" align=\"center\" alt=\"Flightaware Diagram\" width=\"78\" height=\"116\"></a>";
	} elseif($fac['flightaware_checked'] == 0) {
		//print "DEBUG: got 0 for ".$row['airport_ident'];
		if(@getimagesize($flightaware_diagram) == true) {
			$flightaware_diagram_link="<a href=\"".$flightaware_diagram_pdf."\"><img src=\"".$flightaware_diagram."\" align=\"center\" alt=\"Flightaware Diagram\" width=\"78\" height=\"116\"></a>";
			//print "DEBUG: updating 1 for ".$row['airport_ident'];
			$query = "update airports
				set flightaware_checked=1
				where ident = :airport_ident";	
			$query_params = array(
				':airport_ident' => $row['airport_ident']
				);
			try 
			{ 
				// Execute the query 
				$stmt = $db->prepare($query); 
				$result = $stmt->execute($query_params); 
			} 
			catch(PDOException $ex) 
			{ 
				// Note: On a production website, you should not output $ex->getMessage(). 
				// It may provide an attacker with helpful information about your code.  
				die("Failed to run query: " . $ex->getMessage()); 
			}
		} else {
			//print "DEBUG: updating 2 for ".$row['airport_ident'];
			$query = "update airports
				set flightaware_checked=2
				where ident = :airport_ident";	
			$query_params = array(
				':airport_ident' => $row['airport_ident']
				);
			try 
			{ 
				// Execute the query 
				$stmt = $db->prepare($query); 
				$result = $stmt->execute($query_params); 
			} 
			catch(PDOException $ex) 
			{ 
				// Note: On a production website, you should not output $ex->getMessage(). 
				// It may provide an attacker with helpful information about your code.  
				die("Failed to run query: " . $ex->getMessage()); 
			}
		}
	}
	/* if(check_url($url)) {
		$flightaware_url=$url;
	} else {
		$flightaware_url='';
	} */
	$wikilink="";
	if(!empty($row['wikipedia_link'])) {
		$wikilink="'<br><b>Wikipedia:</b>&nbsp;<a href=\"".$row['wikipedia_link']."\">".$row['wikipedia_link']."</a>' +";
	}
	$homelink="";
	if(!empty($row['home_link'])) {
		$homelink="'<br><b>Homepage:</b>&nbsp;<a href=\"".$row['home_link']."\">".$row['home_link']."</a>' +";
	}
	
	$popup_content="var contentString".$marker_count." = '<div id=\"destinations_popup\">' +
		  '<h1>".$row['airport_ident']." - ".$row['name']."</h1><span aligh=\"right\"><a href=\"#\" onClick=\"zoomToMarker(new google.maps.LatLng(".$row['latitude_deg'].", ".$row['longitude_deg']."));\">Zoom in on Destination</a><br>".$flightaware_diagram_link."' +
		  '<hr><b>Municipality:</b>&nbsp;".$row['municipality']."<br><b>Flightaware URL:</b>&nbsp;' +
		  '<a href=\"".$flightaware_url."\">".$flightaware_url."</a>' +
		  ".$wikilink."
		  ".$homelink."
		  '<br><hr><br>' +
		  '<table class=\"destination_popup_table\">' +";
		  
	$query = "select dst.user_id, dst.notes, dst.note_date, us.username from destinations dst
		   join users us 
		   on us.id = dst.user_id
		   where dst.airport_ident = :airport_ident";	
	$query_params = array(
		':airport_ident' => $row['airport_ident']
		);
	try 
	{ 
		// Execute the query 
		$stmt = $db->prepare($query); 
		$result = $stmt->execute($query_params); 
	} 
	catch(PDOException $ex) 
	{ 
		// Note: On a production website, you should not output $ex->getMessage(). 
		// It may provide an attacker with helpful information about your code.  
		die("Failed to run query: " . $ex->getMessage()); 
	}
	$notes_rows = $stmt->fetchall();
	foreach($notes_rows as $notes_row) {
		$popup_content .= "'<tr><td><b>".$notes_row['username'].": </b><br>".$notes_row['note_date']."</td>' +
						   '<td>".str_replace("'", "&lsquo;", $notes_row['notes'])."</td></tr>' +";
	}
	$popup_content .= "'</table></div>';";
	print $popup_content;
	print "var infowindow".$marker_count." = new google.maps.InfoWindow({ content: contentString".$marker_count." });
	";
	print "var dst".$marker_count." = new google.maps.LatLng(".$row['latitude_deg'].", ".$row['longitude_deg'].");
	";
	print "var marker".$marker_count." = new google.maps.Marker({ 
	position: dst".$marker_count.", 
	map: map, 
	title: '".$row['name']."' });
	";
	print "marker".$marker_count.".addListener('click', function() { 
	infowindow".$marker_count.".open(map, marker".$marker_count.");
	});
	";

	$marker_count++;
}
print "

twothreenineAMCircleOneHour = new google.maps.Circle({
		strokeColor: '#FF0000',
		strokeOpacity: 0.6,
		strokeWeight: 2,
		fillColor: '#FF0000',
		fillOpacity: 0.2,
		map: null,
		center: {lat: 43.64619827, lng: -70.30930328},
		radius: 175940,
	});
	
twothreenineAMCircleTwoHour = new google.maps.Circle({
		strokeColor: '#FF0000',
		strokeOpacity: 0.6,
		strokeWeight: 2,
		fillColor: '#FF0000',
		fillOpacity: 0.2,
		map: null,
		center: {lat: 43.64619827, lng: -70.30930328},
		radius: 351880,
	});

foureightoneeightDCircleOneHour = new google.maps.Circle({
		strokeColor: '#0000FF',
		strokeOpacity: 0.6,
		strokeWeight: 2,
		fillColor: '#0000FF',
		fillOpacity: 0.2,
		map: null,
		center: {lat: 43.64619827, lng: -70.30930328},
		radius: 203720,
	});
	
foureightoneeightDCircleTwoHour = new google.maps.Circle({
		strokeColor: '#0000FF',
		strokeOpacity: 0.6,
		strokeWeight: 2,
		fillColor: '#0000FF',
		fillOpacity: 0.2,
		map: null,
		center: {lat: 43.64619827, lng: -70.30930328},
		radius: 407440,
	});
	
nineninetwosixfiveCircleOneHour = new google.maps.Circle({
		strokeColor: '#00FF00',
		strokeOpacity: 0.6,
		strokeWeight: 2,
		fillColor: '#00FF00',
		fillOpacity: 0.2,
		map: null,
		center: {lat: 43.64619827, lng: -70.30930328},
		radius: 203720,
	});
	
nineninetwosixfiveCircleTwoHour = new google.maps.Circle({
		strokeColor: '#00FF00',
		strokeOpacity: 0.6,
		strokeWeight: 2,
		fillColor: '#00FF00',
		fillOpacity: 0.2,
		map: null,
		center: {lat: 43.64619827, lng: -70.30930328},
		radius: 407440,
	});
}";

print "

function zoomToMarker(markerLatLon) {
	map.setCenter(markerLatLon);
	map.setZoom(15);
}";

print "

function goToMarker(markerLatLon) {
	map.setCenter(markerLatLon);
	map.setZoom(8);
}";

print "

function show239AMRadius() {
	twothreenineAMCircleOneHour.setMap(map);
	twothreenineAMCircleTwoHour.setMap(map);
	document.getElementById('239AMRadius').setAttribute('onClick', 'hide239AMRadius();');
	document.getElementById('239AMRadius').firstChild.data = 'Hide 239AM Travel Radius';
}

function hide239AMRadius() {
	twothreenineAMCircleOneHour.setMap(null);
	twothreenineAMCircleTwoHour.setMap(null);
	document.getElementById('239AMRadius').setAttribute('onClick', 'show239AMRadius();');
	document.getElementById('239AMRadius').firstChild.data = 'Show 239AM Travel Radius';
}

function show4818DRadius() {
	foureightoneeightDCircleOneHour.setMap(map);
	foureightoneeightDCircleTwoHour.setMap(map);
	document.getElementById('4818DRadius').setAttribute('onClick', 'hide4818DRadius();');
	document.getElementById('4818DRadius').firstChild.data = 'Hide 4818D Travel Radius';
}

function hide4818DRadius() {
	foureightoneeightDCircleOneHour.setMap(null);
	foureightoneeightDCircleTwoHour.setMap(null);
	document.getElementById('4818DRadius').setAttribute('onClick', 'show4818DRadius();');
	document.getElementById('4818DRadius').firstChild.data = 'Show 4818D Travel Radius';
}

function show99265Radius() {
	nineninetwosixfiveCircleOneHour.setMap(map);
	nineninetwosixfiveCircleTwoHour.setMap(map);
	document.getElementById('99265Radius').setAttribute('onClick', 'hide99265Radius();');
	document.getElementById('99265Radius').firstChild.data = 'Hide 99265 Travel Radius';
}

function hide99265Radius() {
	nineninetwosixfiveCircleOneHour.setMap(null);
	nineninetwosixfiveCircleTwoHour.setMap(null);
	document.getElementById('99265Radius').setAttribute('onClick', 'show99265Radius();');
	document.getElementById('99265Radius').firstChild.data = 'Show 99265 Travel Radius';
}
";

print "

$(document).ready(function () {
	google.maps.event.addDomListener(window, 'load', initialize);
});";
?>