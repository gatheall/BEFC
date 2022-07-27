function checkPasswordMatch() {
    var password = $("#pass1").val();
    var confirmPassword = $("#pass2").val();
	var submitButton = document.getElementById('submitButton');

    if (password != confirmPassword) {
        document.getElementById("pass2").style.color = "red";
		submitButton.disabled=true;
    } else { 
        document.getElementById("pass2").style.color = "green";
		submitButton.disabled=false;
	}
}

function checkLoginFields() {
    var password = $("#passlogin").val();
    var username = $("#username").val();
	var submitButton = document.getElementById('submitButton');

    if (password.length > 0 && username.length > 0) {
		submitButton.disabled=false;
		//console.log("Enabling button");
		//console.log(username.length);
		//console.log(password.length);
    } else {
		submitButton.disabled=true;
		//console.log("Disabling button");
		//console.log(username.length);
		//console.log(password.length);
	}
}

function airportNameSearch() {
	var searchterm = $('#airport_name_search').val();
	$.get("./ajax/airport_name_search.php?airport_name="+searchterm, function(data, status){
		var options=data.split('|');
		var airport_names = document.getElementById("airport_names");
		for (var i=0; i < options.length; i++) {
			var option = document.createElement("option");
			option.text = options[i];
			airport_names.add(option);
		}
	});
};
	
function updateWbMoment() {
	   // 'this' is the field the user is typing in
	   // so find the tr that it belongs to
	   var $row = $(this).closest("tr"),
	   moment = 0,
	   // get the value for the current row:
		arm = $row.find(".wb-arm").val();
		weight = $row.find(".wb-weight-input").val();
		moment = arm*+weight || 0;
		$row.find(".wb-moment").val(moment);
};

function isPointInPoly(poly, pt){
    for(var c = false, i = -1, l = poly.length, j = l - 1; ++i < l; j = i)
        ((poly[i].y <= pt.y && pt.y < poly[j].y) || (poly[j].y <= pt.y && pt.y < poly[i].y))
        && (pt.x < (poly[j].x - poly[i].x) * (pt.y - poly[i].y) / (poly[j].y - poly[i].y) + poly[i].x)
        && (c = !c);
    return c;
}

$(document).ready(function () {
	//console.log("Loading password keyup");
   $("#pass2").keyup(checkPasswordMatch);
   //console.log("Loading passlogin keyup");
   $("#passlogin").keyup(checkLoginFields);
   $("#username").keyup(checkLoginFields);
   //console.log("Loading w&b keyup");
   $("input").change(function(e) {
	   //console.log("Caught keyup");
	   var $row = $(this).closest("tr"),
	   moment = 0,
		arm = parseFloat($row.find("#wb-arm").html());
		var weight = parseFloat($row.find("#wb-weight-input").val());
		if ( $row.find('td:eq(0)').text() == 'Fuel (gals)' ) {
		//var gallons = parseFloat($row.find("#wb-fuel-input").val());
			console.log("Found gallons row");
			moment = arm * (weight * 6.01);
		} else {
			moment = arm * weight;
		}
		//fuelweight = gallons * 6.01;
		//fuelmoment = arm * fuelweight;
		console.log(arm, weight, moment);
		$row.find("#wb-moment").html(moment.toFixed(2));
		//$row.find("#wb-fuel-moment").html(fuelmoment.toFixed(2));
		var totalweight = 0;
		var totalmoment = 0;
		$(".wb-weight-input").each(function() {
			var value = $(this).val();
			if ( $(this).closest("tr").find('td:eq(0)').text() == 'Fuel (gals)' ) {
				totalweight += parseFloat(value * 6.01);
				console.log("incrementing by fuel");
			} else {			
				totalweight += parseFloat(value);
				console.log("incrementing by val");
			}
			//console.log("incrementing by "+value);
		});
		if ( $row.find('td:eq(0)').text() == 'Fuel (gals)' ) {
			if ( weight > 50 ) {
				alert("You appear to have entered the fuel weight,\n not the number of gallons.\n\nPlease enter fuel in gallons.");
			} else {
				fuelweight = weight * 6.01;
				//totalweight += parseFloat(fuelweight);
				$("#FuelWeight").html(parseFloat(fuelweight).toFixed(2));
			}
		}
		$("#TotalWeight").html(parseFloat(totalweight).toFixed(2));
		$(".wb-moment").each(function() {
			var value = $(this).html();
			totalmoment += parseFloat(value);
			//console.log("incrementing by "+value);
		});
		//totalmoment += parseFloat(fuelmoment);
		var cg = parseFloat(totalmoment / totalweight).toFixed(2);
		$("#CenterOfGravity").html(cg);
		// plot dot on canvas
		var maxweight = $("#MaxWeight").html();
		$("#RemainingLoad").html(parseFloat(maxweight - totalweight).toFixed(2));
		var canvas = document.getElementById("wbCanvas");
		var ctx = canvas.getContext("2d");
		ctx.clearRect(0, 0, canvas.width, canvas.height);
		ctx.beginPath();
		var airplane = window.location.href.split("=")[1];
		switch (airplane) {
			case 'N4818D':
				// these are the x,y coordinate calcs for the WB image canvas for N4818D
				var width = 600;
				var height = 440;
				var x = ((cg - 34) * 35) + 80;
				var y = 400 - (((totalweight - 1500) / 100) * 35);
				if( x > width ) {
					x = width;
				}
				if( x < 0 ) {
					x = 0;
				}
				if( y > height ) {
					y = height;
				}
				if( y < 0 ) {
					y = 0;
				}	
				var poly = [
				{x: 115, y: 400},
				{x: 115, y: 240},
				{x: 326, y: 30},
				{x: 546, y: 30},
				{x: 546, y: 400},
				{x: 115, y: 400}
				];
				if (isPointInPoly(poly, {x: x, y: y})) {
					ctx.arc(x,y,4,0,2*Math.PI);
					ctx.fillStyle = 'green';
					ctx.fill();
					ctx.stroke();
					ctx.moveTo(x, 0);
					ctx.lineTo(x, height);
					ctx.strokeStyle = '#00ff00';
					ctx.stroke();
					ctx.moveTo(0, y);
					ctx.lineTo(width, y);
					ctx.stroke();
				} else {
					ctx.arc(x,y,4,0,2*Math.PI);
					ctx.fillStyle = 'red';
					ctx.fill();
					ctx.stroke();
					ctx.moveTo(x, 0);
					ctx.lineTo(x, height);
					ctx.strokeStyle = '#ff0000';
					ctx.stroke();
					ctx.moveTo(0, y);
					ctx.lineTo(width, y);
					ctx.stroke();
					ctx.font = "72px Arial Bold";
					ctx.textAlign = "center";
					ctx.fillText("DO NOT FLY", width/2, height/2);
					ctx.stroke();
				}
				break;
				
			case 'N239AM': 
				if (totalweight > 1608) { 
					var fuel_before_landing = parseFloat((totalweight - 1608) / 6.01).toFixed(2);
					console.log("Calculating fuel burn before land");
				} else {
					var fuel_before_landing = 0;
				}
				$("#fuelbeforeland").html(fuel_before_landing);
				// these are the x,y coordinate calcs for the WB image canvas for N239AM
				var width = 600;
				var height = 440;
				var x = ((cg - 9) * 45) + 90;
				var y = 405 - (((totalweight - 1100) / 100) * 45);
				if( x > width ) {
					x = width;
				}
				if( x < 0 ) {
					x = 0;
				}
				if( y > height ) {
					y = height;
				}
				if( y < 0 ) {
					y = 0;
				}	
				var poly = [
				{x: 250, y: 404},
				{x: 250, y: 239},
				{x: 337, y: 138},
				{x: 454, y: 138},
				{x: 454, y: 404},
				{x: 250, y: 404}
				];
				if (isPointInPoly(poly, {x: x, y: y})) {
					ctx.arc(x,y,4,0,2*Math.PI);
					ctx.fillStyle = 'green';
					ctx.fill();
					ctx.stroke();
					ctx.moveTo(x, 0);
					ctx.lineTo(x, height);
					ctx.strokeStyle = '#00ff00';
					ctx.stroke();
					ctx.moveTo(0, y);
					ctx.lineTo(width, y);
					ctx.stroke();
				} else {
					ctx.arc(x,y,4,0,2*Math.PI);
					ctx.fillStyle = 'red';
					ctx.fill();
					ctx.stroke();
					ctx.moveTo(x, 0);
					ctx.lineTo(x, height);
					ctx.strokeStyle = '#ff0000';
					ctx.stroke();
					ctx.moveTo(0, y);
					ctx.lineTo(width, y);
					ctx.stroke();
					ctx.font = "72px Arial Bold";
					ctx.textAlign = "center";
					ctx.fillText("DO NOT FLY", width/2, height/2);
					ctx.stroke();
				}
				break;
				
			case 'N99265':
				// these are the x,y coordinate calcs for the WB image canvas for N99265
				console.log('Processing N99265');
				var width = 600;
				var height = 440;
				var x = ((cg - 34) * 35) + 80;
				var y = 400 - (((totalweight - 1500) / 100) * 35);
				if( x > width ) {
					x = width;
				}
				if( x < 0 ) {
					x = 0;
				}
				if( y > height ) {
					y = height;
				}
				if( y < 0 ) {
					y = 0;
				}	
				var poly = [
				{x: 115, y: 400},
				{x: 115, y: 240},
				{x: 326, y: 30},
				{x: 546, y: 30},
				{x: 546, y: 400},
				{x: 115, y: 400}
				];
				if (isPointInPoly(poly, {x: x, y: y})) {
					ctx.arc(x,y,4,0,2*Math.PI);
					ctx.fillStyle = 'green';
					ctx.fill();
					ctx.stroke();
					ctx.moveTo(x, 0);
					ctx.lineTo(x, height);
					ctx.strokeStyle = '#00ff00';
					ctx.stroke();
					ctx.moveTo(0, y);
					ctx.lineTo(width, y);
					ctx.stroke();
				} else {
					ctx.arc(x,y,4,0,2*Math.PI);
					ctx.fillStyle = 'red';
					ctx.fill();
					ctx.stroke();
					ctx.moveTo(x, 0);
					ctx.lineTo(x, height);
					ctx.strokeStyle = '#ff0000';
					ctx.stroke();
					ctx.moveTo(0, y);
					ctx.lineTo(width, y);
					ctx.stroke();
					ctx.font = "72px Arial Bold";
					ctx.textAlign = "center";
					ctx.fillText("DO NOT FLY", width/2, height/2);
					ctx.stroke();
				}
				break;
		}
		
   });
});

/* $(document).ready(function() {
    //autocomplete
    $(".auto").autocomplete({
        source: "./ajax/airport_name_search.php",
        minLength: 1
    });    
});  */
