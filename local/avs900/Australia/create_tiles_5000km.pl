#!/usr/bin/env perl
# create_tiles.pl
# Created on 14 Jul, 2019
# Last edit: 14 Jul, 2019
# By Dr. Arapaut V. Sivaprasad
# --------------------------------------
# To create DEA tiles as PNG images for the entire continent
my $j = 0;
$bboxes3857[$j] = "0.00000000,-20037508.34278924,20037508.34278924,0.00000000";
$n_tiles = $j;

`curl 'http://130.56.242.15/ows/dea?service=WMS&version=1.3.0&request=GetCapabilities' > capab.txt`;

$input = "capab.txt";
open (INP, "<$input");
@filecontent = <INP>;
close(INP);
my $len = $#filecontent;
#http://130.56.242.15/ows/dea?time=1986-08-15T00%3A00%3A00.000Z&srs=EPSG%3A3857&transparent=true&format=image%2Fpng&exceptions=application%2Fvnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=landsat5_nbar_16day&bbox=-20037508.342789244%2C0%2C-10018754.171394622%2C10018754.171394622&width=256&height=256
$ProcessTime = `date`;
chop $ProcessTime;
open (OUT, ">>create_tiles.log");
print "----------$ProcessTime-----------\n";
print OUT "----------$ProcessTime-----------\n";
for (my $j=0; $j <= $len; $j++)
{
	$times = "";
	if($filecontent[$j] =~ /<Layer queryable="1" opaque="0">/)
	{
		$nameLine = $filecontent[++$j];
		if ($nameLine =~ /<Name>(.*)<\/Name>/i)
		{
			$layer = $1;
		}
	}
	if($filecontent[$j] =~ /<Dimension name="time" default="current" current="True" units="ISO8601">(.*)<\/Dimension>/)
	{
		$times = $1;
		@times = split(/,/, $times);
		$ct0 = time();
		foreach $time (@times)
		{
			$date = $time;
			$date =~ s/T.*//g;
			$mkdir = "mkdir -p /local/avs900/Australia/DEA_Tiles/$layer/$date";
#			print "$mkdir\n";
			`$mkdir`;
			$n++;
			for (my $k=0; $k <= $n_tiles; $k++)
			{
				# Skip if the file has already been created
				$png = "/local/avs900/Australia/DEA_Tiles/$layer/$date/$bboxes3857[$k].png";
				$png =~ s/,/_/g;
				print "Checking: $n.$k. $png\n";				
				print OUT "Checking: $n.$k. $png\n";				
				$created = 0;
				if (-f $png) { $created = 1; }
				if ($created)
				{
					print "Skip: $n.$k. $png\n";				
					print OUT "Skip: $n.$k. $png\n";				
				}
				else
				{
					# File is not present. Get it created by GSKY
					$ct1 = time();
					$cmd = "curl 'http://130.56.242.15/ows/dea?time=$time&srs=EPSG:3857&transparent=true&format=image%2Fpng&exceptions=application%2Fvnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=$layer&bbox=$bboxes3857[$k]&width=256&height=256'\n";
					print "Creating: $n.$k. $cmd";
					print OUT "Creating: $n.$k. $cmd";
					system($cmd);
					$ct2 = time();
					$et1 = $ct2 - $ct1;
					$et0 += $et1;
					print "Time for this tile: $et1 sec; Total elapsed time: $et0 sec\n";
					$oneTimeSliceCreated++;
					print OUT "Time for this tile: $et1 sec; Total elapsed time: $et0 sec\n";
				}
			}
			last; # Use only the first date
		}
	}
	if ($oneTimeSliceCreated) 
	{ 
		print "Total tiles for $layer $date: $oneTimeSliceCreated\n";
		last; 
	}# Use only the first date
}
close(OUT);
