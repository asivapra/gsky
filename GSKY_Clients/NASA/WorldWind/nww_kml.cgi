#!/usr/bin/env perl
# Created on 31 Mar, 2019
# Last edit: 26 Jun, 2019
# By Dr. Arapaut V. Sivaprasad
=pod
This CGI is for creating the KMLs for displaying the GSKY layers via Google Earth Web.
See http://www.webgenie.com/WebGoogleEarth/
=cut
# -----------------------------------
require "/var/www/cgi-bin/common.pl";
use XML::Hash;
my $xml_converter = XML::Hash->new();
use XML::DOM;
my $parser = new XML::DOM::Parser;
sub reformat
{
  local($tmp) = $_[0] ;
  $tmp =~ s/\+/ /g ;
  while ($tmp =~ /%([0-9A-Fa-f][0-9A-Fa-f])/)
  {
   $num = $1;
   $dec = hex($num);
   $chr = pack("c",$dec);
   $chr =~ s/&/and/g;  # Replace if it is the & char.
   $tmp =~ s/%$num/$chr/g;
  }
  return($tmp);
}
sub debugEnv
{
   print "Content-type:text/html\n\n";
   print "<Pre>\n";
   foreach $item (%ENV)
   {
      print "$item\n";
   }
   exit;
}
sub debug
{
  $line = $_[0];
  $exit = $_[1];
  if (!$headerAdded) { print "Content-type: text/html\n\n"; $headerAdded = 1; }
  print "$line<br>\n";
  if ($exit) { exit; }
}
sub d
{
  $line = $_[0]; if (!$line) { $line = "OK"; }
  $exit = $_[1];
  if (!$headerAdded) { print "Content-type: text/html\n\n"; $headerAdded = 1; }
  print "$line<br>\n";
  if ($exit) { exit; }
}
sub Get_fields
{
   my @pquery = split(/\&/, $pquery);
   for my $item (@pquery)
   {
           if ($item =~ /(.*)=(.*)/i)
           {
                $$1 = $2; 
           }
   }
}
sub GroundOverlay
{
# The $lookAt is used for the active overlays
	my $x = ($east+$west)/2.0;
	my $y = ($north+$south)/2.0;
	my $eye = abs($south - $north)*120*1000;
	my $eye1 = abs($east - $west)*120*1000;
	if ($eye1 > $eye) { $eye = $eye1; } 
	$lookAt = "<LookAt>
				<longitude>$x</longitude>
				<latitude>$y</latitude>
				<altitude>$eye</altitude>
			</LookAt>";
	$groundOverlay .= "
		<GroundOverlay>
			<name>$title</name>
			<visibility>$visibility</visibility>
			<Icon>
				<href>
					$gskyUrl?SERVICE=WMS&amp;BBOX=$west,$south,$east,$north&amp;$time&amp;VERSION=1.1.1&amp;REQUEST=GetMap&amp;SRS=EPSG:4326&amp;WIDTH=512&amp;HEIGHT=512&amp;LAYERS=$layer&amp;STYLES=default&amp;TRANSPARENT=TRUE&amp;FORMAT=image/png
				</href>
			</Icon>
			<LatLonBox>
				<west>$west</west>
				<south>$south</south>
				<east>$east</east>
				<north>$north</north>
			</LatLonBox>
		</GroundOverlay>
	";
}
sub CreateSingleKML
{
=pod	
# The $lookAt is not used anywhere
	my $x = ($east+$west)/2.0;
	my $y = ($north+$south)/2.0;
	my $eye = abs($south - $north)*120*1000;
	my $eye1 = abs($east - $west)*120*1000;
	if ($eye1 > $eye) { $eye = $eye1; } 
	$lookAt = "<LookAt>
				<longitude>$x</longitude>
				<latitude>$y</latitude>
				<altitude>$eye</altitude>
			</LookAt>";
=cut			
	$groundOverlay .= "		<GroundOverlay>
			<name>$title</name>
			<visibility>1</visibility>
			<Icon>
				<href>
					$gskyUrl?SERVICE=WMS&amp;VERSION=1.1.1&amp;REQUEST=GetMap&amp;SRS=EPSG:4326&amp;WIDTH=512&amp;HEIGHT=512&amp;LAYERS=$layer&amp;STYLES=default&amp;TRANSPARENT=TRUE&amp;FORMAT=image/png&amp;BBOX=$west,$south,$east,$north&amp;$time
				</href>
			</Icon>
			<LatLonBox>
				<north>$north</north>
				<south>$south</south>
				<east>$east</east>
				<west>$west</west>
			</LatLonBox>
		</GroundOverlay>
	";
}

sub CreateMultipleKML
{
	# For the GEOGLAM Tiles. Called from geoglam.html as below.
	# <input type="button" value="Create KML" style="color:blue" onclick="ValidateInput(document.forms.google_earth,1);">
	$visibility = 1; # Set this to 0 after the first layer. 
	my @times = split(/,/, $time);
	my $len = $#times;
	for (my $j=0; $j <= $len; $j++)
	{
		$date = $times[$j];
		$date =~ s/T.*Z//gi;
#		$title = $region . "_" . $basetitle . " " . $date;
		$title = $date;
		$time = "";
		if($times[$j]) { $time="TIME=$times[$j]"; }
		GroundOverlay;
		$visibility = 0; # Subsequent layers are set as visibility=0
	}
	Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
	$groundOverlay .= "\n\t<!-- End of GroundOverlays -->";
	$kml = $groundOverlay;
}
sub GetPlacemark
{
	my $filename = $_[0];
	open (INP, "<$filename");
	my @filecontent = <INP>;
	close(INP);
	@filecontent = split(/<Placemark>/, $filecontent[0]);
	my $len = $#filecontent;
	my $placemark = "";
	for (my $j=1; $j < $len; $j++)
	{
		my $polygon = "";
		if ($filecontent[$j] =~ /<Polygon>(.*)<\/Polygon>/i)
		{
			$polygon = $1;
		}
		my $tempfile = "$tmpdir/placemark.tmp"; 
		open(OUT, ">$tempfile");
		print OUT "<Placemark>$filecontent[$j]\n";
		close(OUT);
		my $xml_doc = $parser->parsefile ($tempfile);
		$xml_hash = $xml_converter->fromDOMtoHash($xml_doc);
		my $name = $blank_name;
		if ($shownames && $xml_hash->{Placemark}->{ExtendedData}->{Data}[0]->{name} eq "name")
		{
			$name = $xml_hash->{Placemark}->{ExtendedData}->{Data}[0]->{value}->{text};	
		}
		if ($include_named_only && $name eq $blank_name) { next; }
		if ($include_unnamed_only && $name ne $blank_name) { next; }
		if ($polygon)
		{
			$nplacemark++;
			$placemark .= "\t<Placemark>\n" . 
				"\t\t\t\t<name>$name</name>\n" . 
				"\t\t\t\t<visibility>1</visibility>\n" .
				"\t\t\t\t<Style><LineStyle><color>$outline</color></LineStyle><PolyStyle><fill>1</fill></PolyStyle></Style>\n" . 
				"\t\t\t\t<MultiGeometry><Polygon>$polygon</Polygon></MultiGeometry>\n" . 
				"\t\t\t</Placemark>\n\t\t";
		}
	}
	$placemark =~ s/\n\t\t$//gi;
	return $placemark;
}
sub GetAndCreatePlacemarks
{
=pod
Sub to prepare the 'osm-script' and retrieve the overlay data.

	Key/Value pairs ($kv) comes from the web page. These are sent, one at a time
	to the Overpass API to get the data in OSM format. 
	
	The osm-script is sent to the API using wget:
		`wget --post-file=$txtfile http://overpass-api.de/api/interpreter --output-document=$osmfile`;
	
	The data is first converted into 'geojson' format by the 'osmtogeojson' program.	
		see https://www.npmjs.com/package/osmtogeojson to install.
		
	The saved file, '*.geojson', is converted into KML by 'tokml'
		see https://github.com/mapbox/tokml to install

	The placemarks in the KML file are extracted and inserted into '$overlay'
		$placemark = GetPlacemark($kmlfile);
		
=cut
	my $kv = $_[0];
	my $overlay_name = $kv;
	$overlay_name =~ s/\|/_/g;
	my @kv = split(/_/, $kv);
	my $key = $kv[0];
	my $value = $kv[1];
	my @fields = split(/,/,$bbox);
	my $west = $fields[0];
	my $south = $fields[1];
	my $east = $fields[2];
	my $north = $fields[3];
	my $osm_script = "
<osm-script output=\"xml\" timeout=\"300\">
    <union>
        <query type=\"node\">
            <has-kv k=\"$key\" v=\"$value\"/>
            <bbox-query e=\"$east\" n=\"$north\" s=\"$south\" w=\"$west\"/>
        </query>
        <query type=\"way\">
            <has-kv k=\"$key\" v=\"$value\"/>
            <bbox-query e=\"$east\" n=\"$north\" s=\"$south\" w=\"$west\"/>
        </query>
        <query type=\"relation\">
            <has-kv k=\"$key\" v=\"$value\"/>
            <bbox-query e=\"$east\" n=\"$north\" s=\"$south\" w=\"$west\"/>
        </query>
    </union>
    <union>
        <item/>
        <recurse type=\"down\"/>
    </union>
    <print mode=\"body\"/>
</osm-script>
";
	my $txtfile = "$tmpdir/Tmp.txt";
	my $osmfile = "$tmpdir/Tmp.osm";
	my $geojsonfile = "$tmpdir/Tmp.geojson";
	my $kmlfile = "$tmpdir/Tmp.kml";
	open (OUT, ">$txtfile");
	print OUT $osm_script;
	close(OUT);
	`wget --post-file=$txtfile http://overpass-api.de/api/interpreter --output-document=$osmfile`;
	`osmtogeojson $osmfile > $geojsonfile`;
	`tokml $geojsonfile > $kmlfile`;
	$nplacemark = 0;
	$placemark = GetPlacemark($kmlfile);
	if ($placemark)
	{
		if (!$visibleOverlay)
		{
			if (!$layerTitleAdded)
			{
				$layerTitle1 = "\t<!-- Start of Overpass Overlays -->
	<Folder>
		<name>__Dates &amp; Overlays_____</name>";
				$layerTitleAdded = 1;
			}
		 $overlay .= "
$layerTitle1
		<Folder>
			<name>$overlay_name: $nplacemark</name>
			<visibility>1</visibility>
			$lookAt
			$placemark
		</Folder>";
		$visibleOverlay++;
		}
		else
		{
		 $overlay .= "
		 
		<Folder>
			<name>$overlay_name: $nplacemark</name>
			<visibility>1</visibility>
			$lookAt
			$placemark
		</Folder>";
		$visibleOverlay++;
		}
	}
	else
	{
		if (!$unavailableOverlay)
		{
			if (!$layerTitleAdded)
			{
				$layerTitle2 = "\t<!-- Start of Overpass Overlays -->
	<Folder>
		<name>__Dates &amp; Overlays_____</name>";
				$layerTitleAdded = 1;
			}
		 $overlay .= "
$layerTitle2 
		<Folder>
			<name>$overlay_name: $nplacemark</name>
			<visibility>0</visibility>
		</Folder>";
		$unavailableOverlay++;
		}
		else
		{
		 $overlay .= "
		 
		<Folder>
			<name>$overlay_name: $nplacemark</name>
			<visibility>0</visibility>
		</Folder>";
		$unavailableOverlay++;
		}
	}
	
}
sub GetTheOverlays
{
=pod
	Key/Value pairs ($kv) comes from the web page. These are sent, one at a time
	to the Overpass API to build the '$overlay'
=cut
	my @key_value_pairs = split(/;/, $key_value_pairs);
	my $len = $#key_value_pairs;
	for ($j=0; $j <= $len; $j++)
	{
		$outline = $outlines[$j];
		GetAndCreatePlacemarks($key_value_pairs[$j]);
	}
	if ($overlay)
	{
		$polygons = "		<Folder>
			<name>__Polygons___________</name>
		</Folder>
	</Folder>
";
	}
	else
	{
		$polygons = "	<Folder>
		<name>__Dates___________</name>
	</Folder>
";
	}
	my $xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\">
<Document>
	<name>__GSKY Layers________</name>
	$groundOverlay
$overlay
$polygons
</Document>
</kml>
	";
	open(OUT, ">$nww_kml");
	print OUT "$xml\n";
	close(OUT);
}
sub GetGSKYcookie
{
   my $name = "GSKY-NWW-GEOGLAM";
   @words = ();
   $cookies  = $ENV{'HTTP_COOKIE'};
   if (!$cookies) { return; }

   @cookiesArray = split (/;/, "$cookies");
   foreach $cookieItem (@cookiesArray)
   {
      if ($cookieItem =~ /$name/)
      {
         @words = split (/=/, "$cookieItem");
      }
   }
   $value = $words[1];
   return $value;
}

sub do_main
{
	# Kill a runaway CGI, if any.
	my $psline = `ps -ef | grep google_earth.cgi | grep -v grep`;
	my @fields = split (/\s/, $psline);
	$pid = $fields[1];
	my $thispid = $$;
	if ($pid && $pid ne $thispid) { `kill $pid`; }

	my $cl = $ENV{'CONTENT_LENGTH'}; # Method=POST will have a non-zero value.
	$cl //= 0; # Set the value as 0 if $cl is undefined. It won't happen on a well built Apache server.
	if ($cl > 0)
	{
		read(STDIN, $_, $cl);
		$_ .= "&"; # Append an & char so that the last item is not ignored
		$pquery = &reformat($_);
		print "Content-type: text/html\n\n"; $headerAdded = 1;
	}
	else
	{
=pod
		The form input values are sent as a URI by 'ajax.js'. 
			url = cgi + "?createKML+" + ran_number + "+" + pquery;
		The first item is generally the action required. However, in this CGI it is not used.
		Item #2 is a random number to ensure that the URI is not cached.
		Item #3 is the GET string to be parsed.
=cut
		$sc_action = $ARGV[0];
		if (!$sc_action)
		{
			$dumb = 1; # This is a dumb URL with &BBOX=0,0,0,0 added at the end.
			$request_string = $ENV{QUERY_STRING};
			@fields = split (/\&/, $request_string);
			$sc_action = $fields[0];
			@fields = split (/\+/, $sc_action);
			$sc_action = $fields[0];
			if ($sc_action eq "PNG")
			{
				$west = $fields[1];
				$south = $fields[2];
				$east = $fields[3];
				$north = $fields[4];
				$time = $fields[5];
				$res = $fields[6];
			}
			if ($sc_action eq "WMS")
			{
				$layer = $fields[1];
				$bbox = $fields[2];
				$time = $fields[3];
				$r = $fields[4];
				$create_tiles = $fields[5];
			}
		}
		sub GetLargeHash # Make a hash of the 3x3 tiles within the bbox
		{
			my $filename = $_[0];
			my $rl = $_[1];
			my $r = $_[2];
			%tilesHash = {};
			@bbox = split (/_/, $filename);
			$m = int(1/$r);
			my $w = int($bbox[0]) * $m;
			my $s = int($bbox[1]) * $m;
			my $e = (int($bbox[2]) - $r) * $m;
			my $n = (int($bbox[3]) - $r) * $m;
			for (my $j0 = $w; $j0 < $e; $j0++)
			{
				$j = $j0/$m;
				for (my $k0 = $s; $k0 < $n; $k0++)
				{
					$fin = 0;
					$k = $k0/$m;
					my $w1 = sprintf("%.1f", $j); 
					my $s1 = sprintf("%.1f", $k);
					my $e1 = sprintf("%.1f", $j+$r);
					my $n1 = sprintf("%.1f", $k+$r);
					$sub_tile = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1;
					if ($rl == 3) 
					{ 
						$ii++;
						$tilesHash{$sub_tile} = 0; 
					}
					if ($rl == $resolution) 
					{ 
						$ii++;
						$tilesHash{$sub_tile} = 1; 
					}
				}
			}
		}
		sub GetHash # Make a hash of the 0.1x0.1 tiles within the bbox
		{
			my $filename = $_[0];
			my $rl = $_[1];
			my $r = $_[2];
			my @bbox = split (/_/, $filename);
			my $m = int(1/$r);
			my $w = int($bbox[0] * $m);
			my $s = int($bbox[1] * $m);
			my $ee = int($bbox[2] * $m);
			my $n = int($bbox[3] * $m);
			for (my $j0 = $w; $j0 < $ee; $j0++)
			{
				my $j = $j0/$m;
				for (my $k0 = $s; $k0 < $n; $k0++)
				{
					my $k = $k0/$m;
					my $w1 = sprintf("%.2f", $j); 
					my $s1 = sprintf("%.2f", $k);
					my $e1 = sprintf("%.2f", $j+$r);
					my $n1 = sprintf("%.2f", $k+$r);
					my $sub_tile = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1;
					$tilesHash{$sub_tile} = 1; 
					if($n1 >= $n) { last; }
				}
			}
		}
		sub GetTheLargeTile
		{
			my $i = 3; # The tile res
			my $r = $_[4];  
			my $m = int(1/$r);
			my $w = int($_[0]/$m);
			my $s = int($_[1]/$m);
			my $e = int($_[2]/$m);
			my $n = int($_[3]/$m);

			$w -= ($w % $i);
			$s -= ($s % $i);
			$e -= ($e % $i);
			$n -= ($n % $i);
			$ii = 0;
			for (my $j = $w; $j < $e; $j+=$i)
			{
				for (my $k = $s; $k < $n; $k+=$i)
				{
					$w1 = sprintf("%.1f", $j); 
					$s1 = sprintf("%.1f", $k);
					$e1 = sprintf("%.1f", $j+$i);
					$n1 = sprintf("%.1f", $k+$i);
					$tile_filename = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_$r" . ".png";
					$tile_file = "$basedir/$layer/$time/$r/$tile_filename";
					GetLargeHash($tile_filename,3,$r);
					$tileurl = "http://$domain/GEWeb/DEA_Layers/$layer/$time/3/" . $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_3" . ".png";
					if($n1 >= $n) { last; }
				}
			}
		}
		sub CountTheTiles 
		{
			# To count the high res tiles enclosed in the BBox
			my $w = $_[0];
			my $s = $_[1];
			my $e = $_[2];
			my $n = $_[3];
			my $r = $resolution;
			my $m = int(1/$r);
			GetTheLargeTile($w,$s,$e,$n,$r); # Find the 3x3 tile that covers this bbox
			my $n_tiles = 0;
			for (my $j0 = $w; $j0 < $e; $j0++)
			{
				$j = $j0/$m;
				for (my $k0 = $s; $k0 < $n; $k0++)
				{
					$fin = 0;
					my $k = $k0/$m;
					my $w1 = sprintf("%.2f", $j); 
					my $s1 = sprintf("%.2f", $k);
					my $e1 = sprintf("%.2f", $j+$r);
					my $n1 = sprintf("%.2f", $k+$r);
					my $this_tile = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1;
					my $tile_filename = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_$r" . ".png";
					GetHash($tile_filename,$resolution,$r);
					if ($tilesHash{$this_tile}) # %tilesHash is global
					{
						$n_tiles++;
					}
				}
			}
			&debug("Number of tiles: <big>$n_tiles</big>");
			if ($n_tiles <= 0)
			{
				&debug("<font style=\"color:red; font-size:12px\">B. No tiles in the selected region. Please choose another region.</font>");
			}
			
			if ($n_tiles > 125)
			{
				&debug("<font style=\"color:red; font-size:12px\">Too many tiles to be fetched. A smaller BBox is required for high resolution.</font>");
				&debug("<font style=\"color:#008000; font-size:12px\">Giving Up!</font>");
				exit;
			}
		}
=pod		
		sub CreateMultipleKML_DEA
		{
			# For the GEOGLAM Tiles. Called from geoglam.html as below.
			# <input type="button" value="Create KML" style="color:blue" onclick="ValidateInput(document.forms.google_earth,1);">
			@bbox = split(/,/, $bbox); # $bbox is global, coming from the HTML page
			my $w = int($bbox[0]);
			my $s = int($bbox[1]);
			my $e = int($bbox[2]);
			my $n = int($bbox[3]);
			my $i=$resolution; # Number of degrees for tile axis
			$visibility = 1; # Set this to 0 after the first layer. 
			my @fields = split (/\|/, $layer);
			my $layer = $fields[0];
			my $title = $fields[1];
			my $basetitle = $title;
			my @times = split(/,/, $time);
			my $len = $#times;
			for (my $j=0; $j <= $len; $j++)
			{
				CountTheTilesLow($w,$s,$e,$n,$i,$layer,$times[$j]);
				$date = $times[$j];
				$date =~ s/T.*Z//gi;
				$title = $region . "_" . $basetitle . " " . $date;
				$time = "";
				if($times[$j]) { $time="TIME=$times[$j]"; }
				GroundOverlayTiles($n_tiles,$title);
				$visibility = 0; # Subsequent layers are set as visibility=0
			}
			$kml = $groundOverlay;
		}
=cut
		sub GroundOverlayTiles
		{
#			my @fields = split(/,/,$bbox);
#			my $west = $fields[0];
#			my $south = $fields[1];
#			my $east = $fields[2];
#			my $north = $fields[3];
			my $x = ($east+$west)/2.0;
			my $y = ($north+$south)/2.0;
			my $eye = abs($south - $north)*120*1000;
			my $eye1 = abs($east - $west)*120*1000;
			if ($eye1 > $eye) { $eye = $eye1; } 
	$lookAt = "
	<LookAt>
		<longitude>$x</longitude>
		<latitude>$y</latitude>
		<altitude>$eye</altitude>
	</LookAt>
	";
			# To create the multi "GroundOverlay" KML for displaying the DEA tiles
			my $n_tiles = $_[0];
			my $title = $_[1];
			$groundOverlay .= "
<!-- $n_tiles -->
<GroundOverlay>
	<name>$title</name>
	<visibility>1</visibility>
	<Icon>
		<href>
			$tileUrl
		</href>
		<viewRefreshMode>onStop</viewRefreshMode>
		<viewBoundScale>0.75</viewBoundScale>
	</Icon>
	$lookAt
	<LatLonBox>
		<west>$west</west>
		<south>$south</south>
		<east>$east</east>
		<north>$north</north>
	</LatLonBox>
</GroundOverlay>
";
		}
		sub Folder_groundOverlay
		{
			my $action = $_[0];
			my $title = $_[1];
			my $bbox0 = $_[2];
			if($bbox0) { $bbox = $bbox0; }
			if ($action == 1)
			{
				my @fields = split(/,/,$bbox);
				my $west = $fields[0];
				my $south = $fields[1];
				my $east = $fields[2];
				my $north = $fields[3];
				my $x = ($east+$west)/2.0;
				my $y = ($north+$south)/2.0;
				my $eye = abs($south - $north)*120*1000;
				my $eye1 = abs($east - $west)*120*1000;
				if ($eye1 > $eye) { $eye = $eye1; } 
				$groundOverlay .= "<Folder>
		<visibility>$visibility</visibility>
		<name>$title</name>
		<LookAt>
			<longitude>$x</longitude>
			<latitude>$y</latitude>
			<altitude>$eye</altitude>
		</LookAt>
";
			}
			if ($action == 2)
			{
				$groundOverlay .= "</Folder>";
			}
		}
		sub DEA_High
		{
			my $layer = $_[0];
			my $title = $_[1];
#			if (!$time) { $time = "2013-03-17"; } # $time is global, coming from the HTML page
			if (!$time)
			{
				&debug("No \$time specified. Exitting!",1);
			}
			my @bbox = split(/,/, $bbox);
			my $r = $resolution;
			my $m = int(1/$r);
			my $w = int($bbox[0] * $m);
			my $s = int($bbox[1] * $m);
			my $e = int($bbox[2] * $m);
			my $n = int($bbox[3] * $m);
			my $w1 = sprintf("%.1f", $w/$m); 
			my $s1 = sprintf("%.1f", $s/$m);
			my $e1 = sprintf("%.1f", $e/$m);
			my $n1 = sprintf("%.1f", $n/$m);
			my $ct0 = time();
			CountTheTiles($w,$s,$e,$n);
			my @keys = sort keys %tilesHash;
			my $n_tiles = 0;
			$bbox0 = "$w1,$s1,$e1,$n1"; # Recalculatd bbox for the tiles.
			Folder_groundOverlay(1,$title); # Start of grouping the "GroundOverlays" in a Folder
			foreach my $key (@keys)
			{
				if($tilesHash{$key})
				{
					my $tile = $key;
					$tile =~ s/_/,/g;
					my @bbox = split(/,/,$tile);
					$west = $bbox[0];
					$south = $bbox[1];
					$east = $bbox[2];
					$north = $bbox[3];
					$tile_file = "$localdir/GEWeb/DEA_Layers/$layer/$time/$r/$west" . "_" . $south . "_" . $east . "_" . $north . "_" . $time . "_" . $r . ".png";
					if (!-f $tile_file)
					{
						my $gskyFetchUrl = "http://$domain/cgi-bin/google_earth.cgi?WMS+$layer+$tile+$time+$r&BBOX=0,0,0,0";
						`curl '$gskyFetchUrl'`; # Fetch and write the PNG file
					}
					my $size = -s $tile_file;
					if ($size == 2132) { next; } # This is an empty tile image
					$n_tiles++;
		            $gskyUrl = "http://$domain/GEWeb/DEA_Layers/$layer/$time/$r/$west" . "_" . $south . "_" . $east . "_" . $north . "_" . $time . "_" . $r . ".png";
					if ($callGsky)
					{
						$tileUrl = $gskyUrl;
						$tileUrl =~ s/&/&amp;/gi;
					}
					$title = "$time: $west,$south";
					GroundOverlayTiles($n_tiles,$title);
					$placemark = ""; # Blank this for next round
				}
			}
			Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
			my $ct1 = time();
			$kml = "$groundOverlay";
			if ($n_tiles)
			{
				my @fields = split(/,/,$bbox);
				$west = $fields[0];
				$south = $fields[1];
				$east = $fields[2];
				$north = $fields[3];
				print "<small>Fetched the DEA tiles.</small><br>\n";
				GetTheOverlays; # This is to get the OSM layers from Overpass
				if ($nplacemark) 
				{
					print "<small>Fetched the overlays for: <font style=\"color:red; font-size:12px\">$key_value_pairs</font></small><br>\n";
				}
			}
			else
			{
				print "DO NOT SHOW LAYERS";
			}
			exit;

			$outfile = "DEA_" . $layer . "_" . $time . "_" . $$ . ".kml";
			$outfile =~ s/ /_/gi;
			if ($create_tiles) 
			{ 
				close(OUT); # curl.sh
			}
			open (OUT, ">$docroot/NASA/WorldWind/data/nww/$outfile");
			print OUT $kml;
			close(OUT);

			# Calculate the actual time
			my $et = $ct1 - $ct0;
			$etime = "$et sec.";
			if ($et > 60) 
			{ 
				$etmin = int($et/60); 
				my $etsec =$et % 60; 
				if ($etsec < 10) { $etsec = "0$etsec"; }
				$etime = "$etmin:$etsec min."; 
			}
			my $elapsed_time = "Elapsed Time: $etime";

			print "$elapsed_time<br>\n";
			print "<small><a href=\"$url/$outfile?$$\">$outfile</a></small>";
			exit;
		}
		sub CountTheTilesLow 
		{
			my $w = $_[0];
			my $s = $_[1];
			my $e = $_[2];
			my $n = $_[3];
			my $r = $_[4];
			my $layer = $_[5];
			my $time = $_[6];
			$time =~ s/T.*$//gi;
			my $i=$resolution; # Number of degrees for tile axis
			$w -= $w % $i; # e.g. 11%3 = 2. 11-2=9; 9%3 = 0
			$s -= $s % $i; 
			$e -= $e % $i; 
			$n -= $n % $i; 
			if ($w == $e) { $e+=$i; }
			if ($s == $n) { $n+=$i; }
			for (my $j = $w; $j < $e; $j+=$r)
			{
				for (my $k = $s; $k < $n; $k+=$r)
				{
					$w1 = sprintf("%.1f", $j); 
					$s1 = sprintf("%.1f", $k);
					$e1 = sprintf("%.1f", $j+$r);
					$n1 = sprintf("%.1f", $k+$r);
					$tile_filename = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_$r" . ".png";
					$tile_file = "$basedir/$layer/$time/$r/$tile_filename";
					$tileurl = "http://$domain/GEWeb/DEA_Layers/$layer/$time/$r/" . $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_$r" . ".png";
					if (!-f $tile_file)
					{
						if (!$create_tiles)
						{
							next;
						}
					}
					$n_tiles++;
					if($n1 >= $n) { last; }
				}
			}
		}
		if ($sc_action eq "DEA")
		{
			$nww_kml = "$datadir/nww.kml";
			$value = GetGSKYcookie;
			if ($value)
			{
				$nww_kml = "$datadir/nww_$value\.kml";
			}
			# To create the DEA tiles. Called from dea.html as below.
			# <input type="button" value="Create KML" style="color:blue" onclick="ValidateInput(document.forms.google_earth,2);">
			print "Content-type: text/html\n\n"; $headerAdded = 1;
			$pquery = reformat($ARGV[2]);
			$pquery =~ s/\\//gi;
			Get_fields;	# Parse the $pquery to get all form input values
			my $r = $resolution;
			my @fields = split (/\|/, $layer);
			my $layer = $fields[0];
			my $title = $fields[1];
			my $basetitle = $title;
			my $i=$resolution; # Number of degrees for tile axis
			if ($i < 1)
			{
				DEA_High($layer, $title);
			}
			@bbox = split(/,/, $bbox); # $bbox is global, coming from the HTML page
			my $w = int($bbox[0]);
			my $s = int($bbox[1]);
			my $e = int($bbox[2]);
			my $n = int($bbox[3]);
			# The w,s,e,n values must match the tiles created for this resolution
			# The Lon/Lat values must be divisible with the value of resolution.
			# For example, the 2x2 degree tiles will use even numbers for both Lon and Lat. e.g. 110,-44,112,-42; 112,-42,114,-40;
			# The 3x3 tiles will use multiples of 3. e.g. 111,-45,114,-42; 111,-42,114,-39
			$w -= $w % $i; # e.g. 11%3 = 2. 11-2=9; 9%3 = 0
			$s -= $s % $i; 
			$e -= $e % $i; 
			$n -= $n % $i; 
			if ($w == $e) { $e+=$i; }
			if ($s == $n) { $n+=$i; }
			$bbox0 = "$w,$s,$e,$n"; # Recalculatd bbox for the tiles.
			$visibility = 1;
			Folder_groundOverlay(1,$title); # Start of grouping the "GroundOverlays" in a Folder
			$n_tiles = 0;
			my @times = split(/,/,$time);
			foreach $time(@times)
			{
				$time =~ s/T.*$//gi;
				CountTheTilesLow($w,$s,$e,$n,$i,$layer,$time);
				Folder_groundOverlay(1,$time); # Start of grouping the "GroundOverlays" in a Folder
				for (my $j = $w; $j < $e; $j+=$i)
				{
					for (my $k = $s; $k < $n; $k+=$i)
					{
						$w1 = sprintf("%.1f", $j); 
						$s1 = sprintf("%.1f", $k);
						$e1 = sprintf("%.1f", $j+$i);
						$n1 = sprintf("%.1f", $k+$i);
						$tile_filename = $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_$r" . ".png";
						$tile_file = "$basedir/$layer/$time/$r/$tile_filename";
						if (!$create_tiles && !-f $tile_file)
						{
							next;
						}
						$tileUrl = "$cgi?PNG+$w1+$s1+$e1+$n1+$time+$i";
						$west = $w1;
						$south = $s1;
						$east = $e1;
						$north = $n1;
						$gskyUrl = "http://$domain/GEWeb/DEA_Layers/$layer/$time/$r/$west" . "_" . $south . "_" . $east . "_" . $north . "_" . $time . "_" . $r . ".png";
						if ($callGsky)
						{
							$tileUrl = $gskyUrl;
							$tileUrl =~ s/&/&amp;/gi;
						}
						$title = "$time: $w1,$s1";
						$n_tiles++;
						GroundOverlayTiles($n_tiles,$title);
						$visibility = 0;
						if($n1 == $n) { last; }
					}
				}
#				Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
			}
			&debug("Number of tiles: <big>$n_tiles</big>");
			if ($n_tiles <= 0)
			{
				&debug("<font style=\"color:red; font-size:12px\">No tiles in the selected region. Please choose another region.</font>");
			}
				$groundOverlay .= "
<Folder>
	<name>______Polygons______</name>
</Folder>
";

			Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
			$kml = "$groundOverlay";
			$outfile = "DEA_" . $layer . "_" . $time . "_" . $$ . ".kml";
			$outfile =~ s/ /_/gi;
			if ($n_tiles)
			{
				print "<small>Fetched the DEA tiles.</small><br>\n";
				GetTheOverlays; # This is to get the OSM layers from Overpass
				if ($nplacemark) 
				{
					print "<small>Fetched the overlays for: <font style=\"color:red; font-size:12px\">$key_value_pairs</font></small><br>\n";
				}
			}
			else
			{
				print "DO NOT SHOW LAYERS";
			}
			exit;
		}
		if ($sc_action eq "GEOGLAM")
		{
			$nww_kml = "$datadir/nww.kml";
			$value = GetGSKYcookie;
			if ($value)
			{
				$nww_kml = "$datadir/nww_$value\.kml";
			}
=pod
	For GEOGLAM the call from geoglam.html will create a KML with GSKY call as..
         http://130.56.242.15/ows/ge?SERVICE=WMS&amp;VERSION=1.1.1&amp;REQUEST=GetMap&amp;SRS=EPSG:4326&amp;WIDTH=512&amp;HEIGHT=512&amp;LAYERS=global:c6:frac_cover&amp;STYLES=default&amp;TRANSPARENT=TRUE&amp;FORMAT=image/png&amp;BBOX=112.324219,-44.087585,153.984375,-10.919618&amp;

    The BBox values specified in the above call will be used to generate the PNG
    file on the flye as in the case of a GetMap request to the GSKY server.
	
=cut
			
			print "Content-type: text/html\n\n"; $headerAdded = 1;
			$pquery = reformat($ARGV[2]);
			$pquery =~ s/\\//gi;
			Get_fields;	# Parse the $pquery to get all form input values
			@fields = split (/\|/, $layer);
			$layer = $fields[0];
			$title = $fields[1];
			$basetitle = $title;
			$visibility = 1;
			$groundOverlay = "<!-- Start of GroundOverlays -->\n\t";
			Folder_groundOverlay(1,$title); # Start of grouping the "GroundOverlays" in a Folder
			if ($time =~ /,/)
			{
				# This is a multiple time selection
				CreateMultipleKML;
				print "<small>Fetched the GEOGLAM layer for multiple dates.</small><br>\n";
				GetTheOverlays; # This is to get the OSM layers from Overpass
				if ($nplacemark) 
				{
					print "<small>Fetched the overlays for: <font style=\"color:red; font-size:12px\">$key_value_pairs</font></small><br>\n";
				}
				exit;
			}
			else
			{
				if ($time)
				{
					$date = $time;
					$date =~ s/T.*Z//gi;
					$time="TIME=$time";
				}
#				$title = $basetitle . " " . $date;
				$title = $date;
				CreateSingleKML;
				Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
				$groundOverlay .= "\n\t<!-- End of GroundOverlays -->";
				print "<small>Fetched the GEOGLAM layer for a single date.</small><br>\n";
				GetTheOverlays; # This is to get the OSM layers from Overpass
				if ($nplacemark) 
				{
					print "<small>Fetched the overlays for: <font style=\"color:red; font-size:12px\">$key_value_pairs</font></small><br>\n";
				}
			}
			Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
			exit;
		}
		if ($sc_action eq "Help") # Help to create the tiles. Out of date.
		{
			print "To create tiles:\n";
			print "
			<ul>
				<li>Stop the Apache server on http://130.56.242.19: '<b>service httpd stop</b>'</li>
				<li>Start the GSKY server: '<b>source /home/900/avs900/short_build.sh</b></li>
				<li>Execute: '<b>source /var/www/html/WebGoogleEarth/Tiles/curl.sh</b>'</li>
				<li>Stop the GSKY server on http://130.56.242.19:
				<ul>
					<li>
				       <b>pid=`ps -ef | grep gsky | grep -v grep | awk '{split(\$0,a,\" \"); print a[2]}'`</b>
				    </li>
					<li>
						<b>kill \$pid</b>
				    </li>
				</ul>
				</li>
				<li>Start the Apache server: '<b>service httpd start</b>'</li>
			</ul>
			</span>
			";
		}
		sub ElapsedTime
		{
			my $n = $_[0];
			$ct1 = time();
			$et = $ct1 - $ct0;
			&debug ("$n. $et sec.");
			$ct0 = $ct1;
		}
		if ($sc_action eq "Kill")
		{
			# Kill previous CGI
			$pquery = reformat($ARGV[2]);
			$pquery =~ s/\\//gi;
			Get_fields;	# Parse the $pquery to get all form input values
			print "Content-type: text/html\n\n"; $headerAdded = 1;
			$layer =~ s/\|/\\|/g;
			my $pscmd = "ps -ef | grep \"/var/www/cgi-bin/nww_kml.cgi GEOGLAM.*$layer\" | grep -v grep";
			my $psline = `$pscmd`;
			$psline =~ tr/  / /s;
			my @fields = split (/\s/, $psline);
			$pid = $fields[1];
			my $thispid = $$;
			if ($pid && $pid ne $thispid) 
			{ 
				`kill $pid`;
				print "<font style=\"color:#FF0000\">Killed the process. ID = <b>$pid</b></font>";
			}
			else
			{
				print "Could not find any process to kill.\n";
			}
			exit;
		}
		&debug("No valid \$sc_action ($sc_action) in the GET call.");			
	}
}
$|=1;
#$domain = "webgenie.com";
$domain = $ENV{HTTP_HOST};
$ows_domain = "130.56.242.15";
$docroot = $ENV{DOCUMENT_ROOT};
if (!$docroot) { $docroot = "/var/www/html"; }
$cgi = "http://$domain/cgi-bin/nww_kml.cgi"; # On VM19
$gskyUrl = "http://130.56.242.15/ows/ge";
$gskyUrlDEA = "http://130.56.242.15/ows/dea";
$basedir = "$docroot/GEWeb/DEA_Layers";
$tmpdir = "/var/www/html/NASA/WorldWind/data/Tmp";
$datadir = "/var/www/html/NASA/WorldWind/data/nww";
$localdir = "/local";
$url = "http://$domain";
#$url = $ENV{HTTP_REFERER};
$url = $url . "/WebGoogleEarth/KML";
$aus_bboxes = "aus_bboxes.csv";
$create_tiles_sh = "create_tiles.sh";
$visibility = 1;  
#$layer = "LS8:NBAR:TRUE";
$layer = "landsat8_nbart_16day";
$title = "DEA Landsat 8 surface reflectance true colour";
$callGsky = 1; # Use GetMap calls to GSKY instead of using the PNG files at high res
$ct0 = time();
$shownames = 1; # Set this to 0 to suppress the names of lakes
$include_named_only = 0; # Do not show unnamed lakes
$include_unnamed_only = 0; # Do not show unnamed lakes
$blank_name = " ";
@outlines = ("ff00ff00","ff0000ff","ffff0000","ff00ffff","ff008000","ff800000","ff00ffff");
&do_main;
=pod
Cache location: C:\Users\avs29\AppData\Local\Google\Chrome\User Data\Default\Cache
=cut
