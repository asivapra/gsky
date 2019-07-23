#!/usr/bin/env perl
# create_tiles.pl
# Created on 14 Jul, 2019
# Last edit: 23 Jul, 2019
# By Dr. Arapaut V. Sivaprasad
# --------------------------------------
# To create DEA tiles as PNG images for the entire continent
# Usage: ./create_tiles_all.pl layer date
# e.g.:  ./create_tiles_all.pl landsat8_nbar_16day 2013-03-17
# --------------------------------------

sub ReadBboxList
{
	my $bbox_list = "$tile_basedir/bboxes.txt";
	open (INP, "<$bbox_list");
	@bbox_list = <INP>;
	close(INP);
	$n_bboxes = $#bbox_list;
#print "n_bboxes = $n_bboxes\n";	
#print "bbox_list = $bbox_list\n";	
}
sub CreateTiles
{
	$mkdir = "mkdir -p $tile_basedir/$layer/$date";
	`$mkdir`;
	
	chop $ProcessTime;
	open (OUT, ">>create_tiles_all.log");
	print "----------$ProcessTime-----------\n";
	print OUT "----------$ProcessTime-----------\n";
#$n_bboxes = 2;	
	for (my $k=0; $k <= $n_bboxes; $k++)
	{
		$bbox = $bbox_list[$k];
		$bbox =~ s/\.png\n//gi;
		# Skip if the file has already been created
		$png = "$tile_basedir/$layer/$date/$bbox.png";
#print "PNG: $k. $png\n";				
		$created = 0;
		if (-f $png) { $created = 1; }
		if ($created)
		{
			print "Warning: Skip: $k. $png\n";				
			print OUT "Skip: $k. $png\n";				
		}
		else
		{
			# File is not present. Get it created by GSKY
			$ct1 = time();
			$bbox =~ s/_/,/g;
			$cmd = "curl 'http://130.56.242.15/ows/dea?time=$time&srs=EPSG:3857&transparent=true&format=image%2Fpng&exceptions=application%2Fvnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=$layer&bbox=$bbox&width=256&height=256'";
			print "Creating: $k. $cmd0";
			print OUT "Creating: $k. $cmd0";
			system($cmd);
			$ls = `ls -l $png`;
			
			# Delete blank tile
			if ($ls =~ / 820 /) 
			{
				print "Warning: Deleting blank: $ls\n";
				print OUT "Warning: Deleting blank: $ls\n";
				`rm -f $png`; 
			}
			$ct2 = time();
			$et1 = $ct2 - $ct1;
			$et0 += $et1;
			print "This tile: $et1 sec; Total: $et0 sec\n";
			print OUT "This tile: $et1 sec; Total: $et0 sec\n";
		}
#		last;
	}
	close(OUT);
}
sub PurgeBlanks
{
	chdir ("$tile_basedir/$layer/$date");
	$list = `ls -l | grep " 820 "`;
	@list = split(/\n/, $list);
	foreach $line (@list)
	{
		$line =~ tr/  / /s;
		@fields = split(/ /, $line);
		$filename = $fields[8];
		print "Deleting blank: $filename\n";	
		`rm -f $filename`;
	}
}
$tile_basedir = "/local/avs900/Australia/DEA_Tiles";
$ProcessTime = `date`;
$layer = $ARGV[0];
$date = $ARGV[1];
$time = $date . "T00:00:00.000Z";
&ReadBboxList;
&CreateTiles;
#&PurgeBlanks;

