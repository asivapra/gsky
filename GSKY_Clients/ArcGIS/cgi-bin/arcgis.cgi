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
$docroot = "/var/www/vhosts/webgenie.com/httpdocs/GSKY/ArcGIS";
$kmlDir = "$docroot/KML";
$basedir = "$docroot/GEWeb/DEA_Layers";
$localdir = $docroot;
$url = "https://$domain";
$url = $url . "/GSKY/ArcGIS/KML";
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
