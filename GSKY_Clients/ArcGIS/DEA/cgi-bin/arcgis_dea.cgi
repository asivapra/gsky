#!/usr/bin/env perl
# Created on 31 Mar, 2019
# Last edit: 3 Apr, 2019
# By Dr. Arapaut V. Sivaprasad
=pod
This CGI is for creating the KMLs for displaying the GSKY layers via Google Earth Web.
See http://www.webgenie.com/WebGoogleEarth/
=cut
# -----------------------------------
require "/var/www/vhosts/webgenie.com/cgi-bin/common.pl";
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
	$groundOverlay .= "
	<Folder>
		<visibility>$visibility</visibility>
		<name>$date</name>
		<GroundOverlay>
			<Icon>
				<href>
					$gskyUrl?SERVICE=WMS&amp;BBOX=$west,$south,$east,$north&amp;$time&amp;VERSION=1.1.1&amp;REQUEST=GetMap&amp;SRS=EPSG:4326&amp;WIDTH=512&amp;HEIGHT=512&amp;LAYERS=$layer&amp;STYLES=&amp;TRANSPARENT=TRUE&amp;FORMAT=image/png
				</href>
			</Icon>
			<LatLonBox>
				<west>$west</west>
				<south>$south_latlon</south>
				<east>$east</east>
				<north>$north_latlon</north>
			</LatLonBox>
		</GroundOverlay>
	</Folder>
	";
}
sub CreateSingleKML
{
	$north_latlon = $north;
	$south_latlon = $south;
	if ($wmsclient eq "ArcGIS" && $region eq "Australia")
	{
		$north_latlon++;
		$south_latlon++;
	}
	$kml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\" xmlns:kml=\"http://www.opengis.net/kml/2.2\" xmlns:atom=\"http://www.w3.org/2005/Atom\">
<GroundOverlay>
    <name>$title</name>
    <visibility>1</visibility>
    <Icon>
        <href>
            $gskyUrl?SERVICE=WMS&amp;VERSION=1.1.1&amp;REQUEST=GetMap&amp;SRS=EPSG:4326&amp;WIDTH=512&amp;HEIGHT=512&amp;LAYERS=$layer&amp;STYLES=&amp;TRANSPARENT=TRUE&amp;FORMAT=image/png&amp;BBOX=$west,$south,$east,$north&amp;$time
        </href>
    </Icon>
    <LatLonBox>
        <north>$north_latlon</north>
        <south>$south_latlon</south>
        <east>$east</east>
        <west>$west</west>
    </LatLonBox>
</GroundOverlay>
</kml>
	";
}

sub CreateMultipleKML
{
	$north_latlon = $north;
	$south_latlon = $south;
	if ($wmsclient eq "ArcGIS" && $region eq "Australia") # These come from the web page
	{
		# The latitude values must be corrected by 1 degree north. It is an anomaly in ArcGIS
		$north_latlon++;
		$south_latlon++;
	}
	# For the GEOGLAM Tiles. Called from geoglam.html as below.
	$visibility = 1; # Set this to 0 after the first layer. 
	my @times = split(/,/, $time);
	my $len = $#times;
	for (my $j=0; $j <= $len; $j++)
	{
		$date = $times[$j];
		$date =~ s/T.*Z//gi;
		$title = $region . "_" . $basetitle . " " . $date;
		$time = "";
		if($times[$j]) { $time="TIME=$times[$j]"; }
		GroundOverlay;
		$visibility = 0; # Subsequent layers are set as visibility=0
	}
	$kml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\" xmlns:gx=\"http://www.google.com/kml/ext/2.2\" xmlns:kml=\"http://www.opengis.net/kml/2.2\" xmlns:atom=\"http://www.w3.org/2005/Atom\">
<Document>
	<name>$layer</name>
$groundOverlay	
</Document>
</kml>
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
=pod		
		$groundOverlay .= "<Folder>
<visibility>$visibility</visibility>
<name>$title</name>
<LookAt>
	<longitude>$x</longitude>
	<latitude>$y</latitude>
	<altitude>$eye</altitude>
</LookAt>
";
=cut
	}
	if ($action == 2)
	{
		$groundOverlay .= "</Folder>";
	}
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
	if ($method == 1) { $i = 3; }
#if ($i < 1) { $i = 1; } # Temp fix for method=1 (directly from GSKY)
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
			$tileurl = "https://$domain/GSKY/ArcGIS/DEA/Tiles/$layer/$time/$r/" . $w1 . "_" . $s1 . "_" . $e1 . "_" . $n1 . "_" . $time . "_$r" . ".png";
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
sub GroundOverlayTiles
{
	# Called from DEA alone
	my $n_tiles = $_[0];
	my $title = $_[1];
	my $x = ($east+$west)/2.0;
	my $y = ($north+$south)/2.0;
	my $eye = abs($south - $north)*120*1000;
	my $eye1 = abs($east - $west)*120*1000;
	if ($eye1 > $eye) { $eye = $eye1; } 
	$lookAt = "";
	# To create the multi "GroundOverlay" KML for displaying the DEA tiles
	$groundOverlay .= "
		<GroundOverlay>
			<Icon>
				<href>
					$tileUrl
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
sub GroundOverlayTiles_0
{
	# Called from DEA alone
	my $n_tiles = $_[0];
	my $title = $_[1];
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
	# To create the multi "GroundOverlay" KML for displaying the DEA tiles
	$groundOverlay .= "
<GroundOverlay>
	<name>$title</name>
	<visibility>1</visibility>
	<Icon>
		<href>
			$tileUrl
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
		&debug("<font style=\"color:#008000; font-size:12px\">May take a long time!</font>");
	}
}
sub do_main
{
#&debugEnv;	
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
		if ($sc_action eq "GEOGLAM")
		{
=pod
	For GEOGLAM the call from geoglam.html will create a KML with GSKY call as..
         $gskyUrl?SERVICE=WMS&amp;VERSION=1.1.1&amp;REQUEST=GetMap&amp;SRS=EPSG:4326&amp;WIDTH=512&amp;HEIGHT=512&amp;LAYERS=global:c6:frac_cover&amp;STYLES=default&amp;TRANSPARENT=TRUE&amp;FORMAT=image/png&amp;BBOX=112.324219,-44.087585,153.984375,-10.919618&amp;

    The BBox values specified in the above call will be used to generate the PNG
    file on the fly as in the case of a GetMap request to the GSKY server.
	
=cut		
			print "Content-type: text/html\n\n"; $headerAdded = 1;
			$pquery = reformat($ARGV[2]);
			$pquery =~ s/\\//gi;
			Get_fields;	# Parse the $pquery to get all form input values
			@fields = split (/\|/, $layer);
			$layer = $fields[0];
			$title = $fields[1];
			$basetitle = $title;
			if ($time =~ /,/)
			{
				# This is a multiple time selection
				CreateMultipleKML;
				$outfile = $region . "_" . $basetitle . "_" . $$ . ".kml";
				$outfile =~ s/ /_/gi;
				open (OUT, ">$kmlDir/$outfile");
				print OUT $kml;
				close(OUT);
				print "<small><a href=\"$url/$outfile\">$outfile</a></small>";
				exit;
			}
			else
			{
				$date = $time;
				$date =~ s/T.*//g;
				if ($time)
				{
					$time="TIME=$time";
				}
				$title = $region . "_" . $basetitle . " " . $date;
				CreateSingleKML;
				$outfile = $region . "_" . $basetitle . "_" . $$ . "_" . $date . ".kml";
				$outfile =~ s/ /_/gi;
				open (OUT, ">$kmlDir/$outfile");
				print OUT $kml;
				close(OUT);
				print "<small><a href=\"$url/$outfile\">$outfile</a></small>";
			}
			exit;
		}
		if ($sc_action eq "DEA")
		{
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
			if ($method == 1) { $i = 3; }
			if ($i < 1)
			{
#				DEA_High($layer, $title);
#				$i = 1; # Temp fix for method=1 (directly from GSKY)
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
			$groundOverlay = "\t<!-- Start of GroundOverlays -->";
			Folder_groundOverlay(1,$title,$bbox0); # Start of grouping the "GroundOverlays" in a Folder
			$n_tiles = 0;
			my @times = split(/,/,$time);
			foreach $time(@times)
			{
				$time =~ s/T.*$//gi;
				CountTheTilesLow($w,$s,$e,$n,$i,$layer,$time);
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
						$bbox = "$west,$south,$east,$north";
						if ($method == 1)
						{
							$gskyUrl = "https://gsky.nci.org.au/ows/dea?time=$time" . "T00:00:00.000Z&srs=EPSG:4326&transparent=true&format=image/png&exceptions=application/vnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=landsat8_nbar_16day&bbox=$bbox&width=256&height=256";
						}
						else
						{
							$gskyUrl = "https://$domain/GSKY/ArcGIS/DEA/Tiles/$layer/$time/$r/$west" . "_" . $south . "_" . $east . "_" . $north . "_" . $time . "_" . $r . ".png";
						}
						if ($callGsky)
						{
							$tileUrl = $gskyUrl;
							$tileUrl =~ s/&/&amp;/gi;
						}
#						$title = "$time: $w1,$s1";
						$title = "$w1,$s1";
						GroundOverlayTiles($n_tiles,$title);
						$visibility = 0;
						if($n1 == $n) { last; }
					}
				}
			}
			&debug("Number of tiles: <big>$n_tiles</big><br>\n");
			if ($n_tiles <= 0)
			{
				&debug("<font style=\"color:red; font-size:12px\">No tiles in the selected region. Please choose another region.</font>");
			}
#			Folder_groundOverlay(2); # End the Group the "GroundOverlays" in a Folder
			$groundOverlay .= "<!-- End of GroundOverlays -->";
			$kml = "$groundOverlay";
			$date = $time;
			$date =~ s/T.*$//gi;
			$outfile = "DEA_" . $layer . "_" . $date . "_" . $$ . ".kml";
			$outfile =~ s/ /_/gi;
			my $xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\">
<Document>
	<name>$basetitle</name>
	<Folder>
		<name>$date</name>
	$groundOverlay
	</Folder>
</Document>
</kml>
	";
	open(OUT, ">$kmlDir/$outfile");
	print OUT "$xml\n";
	close(OUT);
			print "<small><a href=\"$url/$outfile\">$outfile</a></small>";
			exit;
		}
		else
		{
			&debug("Warning: sc_action not found!");
		}
	}
}
$|=1;
#$domain = "webgenie.com";
$domain = $ENV{HTTP_HOST};
$gskyUrl = "https://gsky.nci.org.au/ows/geoglam";
$docroot = "/var/www/vhosts/webgenie.com/httpdocs/GSKY/ArcGIS/DEA";
$kmlDir = "$docroot/KML";
$basedir = "$docroot/Tiles";
$localdir = $docroot;
$url = "https://$domain";
$url = $url . "/GSKY/ArcGIS/DEA/KML";
$aus_bboxes = "aus_bboxes.csv";
$create_tiles_sh = "create_tiles.sh";
$visibility = 1;  
#$layer = "LS8:NBAR:TRUE";
$layer = "landsat8_nbart_16day";
$title = "DEA Landsat 8 surface reflectance true colour";
$callGsky = 1; # Use GetMap calls to GSKY instead of using the PNG files at high res
$ct0 = time();
$ProcessTime = `/bin/date`; $ProcessTime =~ s/\n//g ;
&do_main;
=pod
Cache location: C:\Users\avs29\AppData\Local\Google\Chrome\User Data\Default\Cache
=cut
