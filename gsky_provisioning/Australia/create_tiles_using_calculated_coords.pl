#!/usr/bin/env perl
# create_tiles.pl
# Created on 14 Jul, 2019
# Last edit: 16 Aug, 2019
# By Dr. Arapaut V. Sivaprasad
# --------------------------------------
# To create DEA tiles as PNG images for the entire continent
=pod
This script will create the PNG tiles for a specified zoom level. 

The BBOXes for the tiles are dynamically calculated from the continent-level BBOX and zoom level.
	How to run:
		1. Change directory to anywhere.
		2. Run the script as...
			'/local/avs900/Australia/create_tiles_all.pl cc landsat8_nbar_16day 2011-11-08 200&'
			- Tiles will be for the 200km zoom level and will be saved as 
				'landsat8_nbar_16day_2011-11-08_200.tar.gz' in './landsat8_nbar_16day/2011-11-08/200'
				
Pre-requisites:
	The MAS database must be ingested with the required data.
	The MAS, OWS servers and GRPC workers must be running.
	see 'build_gsky.py' and 'provision_single_node.py' to build GSKY, MAS and to start the servers. 
=cut
# --------------------------------------
sub WaitForJobs
{
	# Wait until all remaining jobs are finished
	$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
	chop ($n_curls);
	$on_curls = $n_curls;
	while ($n_curls > 0) # Remaining jobs
	{
		sleep(3);
		$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
		chop ($n_curls);
		print("Remaining curls: $n_curls/$on_curls\n");
#		$n_gdal = `ps -ef | grep gsky-gdal-proce | grep -v grep | wc -l`;
#		chop ($n_gdal);
#		print("Remaining GDALs: $n_gdal\n");
#		if (!$n_gdal) 
#		{ 
#			print("Error: $n_gdal GDAL processes. GRPC servers exited?\n");
#			last; 
#		}
	}
}
sub ThrottleTheJobs
{
	$n_curls = `ps -ef | grep curl | grep -v grep | grep avs900 | wc -l`;
	chop ($n_curls);
	$on_curls = $n_curls;
#	if ($n_curls > $max_jobs)
#	{
#		print("Jobs: $n_curls/$on_curls. Waiting to come down....\n");
#	}
	while ($n_curls > $max_jobs) # Max jobs at a time. Wait until the number comes down
	{
		print("Excess Jobs: $n_curls/$on_curls...\n");
		sleep(3);
		$n_curls = `ps -ef | grep curl | grep -v grep | grep avs900 | wc -l`;
		chop ($n_curls);
	}
}
sub PurgeBlanksAndCreateTarGz
{
	# Remove the blank tiles
	print "Created the tiles. Purging the blanks...\n";
#	$subdir = "$homedir/$date/$zoom";
#	print "subdir = $subdir\n";
	chdir($subdir);
#	`find . -name "*.png" -size -821c -exec rm -f {} \;`; # Doesn't work
	$ls = `ls -l`;
	@ls = split(/\n/, $ls);
	foreach $line (@ls)
	{
		if ($line =~ / 820 / || $line =~ / 0 /)
		{
			my @fields = split(/ /, $line);
			my $len = $#fields;
			$png = $fields[$len];
			`rm $png`;
		}
	}
	print "Creating a 'tar' archive and deleting the individual files... \n";
	# Tar the files
	$n_png = `ls -1 *.png | wc -l`;
	chop ($n_png);
	if ($n_png)
	{
		$tarfile = $layer . "_" . $date . "_" . $zoom . ".tar";
		`tar cf $tarfile ./*.png`;
		`gzip $tarfile`;
		# Remove the PNGs
		`rm -f ./*.png`;
	}
	else
	{
		print "No PNG files for $date/$zoom.";
	}
}
sub CreateTilesDC
{
	$o = $diffs{$zoom}; # The X,Y offset for this zoom level between the bottom left corner and the top right corner of the tile
	@aus_bbox = split (/,/, $aus_bboxes{$zoom}); # The continent BBOX for this zoom level.
	$x = $aus_bbox[0];
	$y = $aus_bbox[1];
	$X = $aus_bbox[2];
	$Y = $aus_bbox[3];

	# The subdir to create the PNG files.
#	print "$k1. $date\n";
	$subdir = "$date/$zoom";
	`mkdir -p $subdir`; # Tiles will be created in this Tmp dir
	$max_jobs = 160; # Arbitrary limit: 10 per core
	$curl_timeout = 6000; # Arbitrary limit
	# Iterate through the X,Y coordinates to construct the tile's BBOX. 
	$gz = `ls $subdir/*.gz`;
	chop($gz);
	my $size = -s $gz;
#print "gz = $gz; $size\n";			
	if (-f $gz) 
	{
		next; 
	}
	$jobs = 0;
	$tot = 0;
	for (my $k=$y; $k < $Y; $k+=$o)
	{
		for (my $j=$x; $j <= $X; $j+=$o)
		{
			$jobs++;
			$tot++;
			my $x = $j;
			my $X = $x + $o; if ($X < -0 && $X > -2) { $X = 0; }
			my $y = $k;
			my $Y = $y + $o; if ($y == 0 || ($Y < -0 && $Y > -2)) { $Y = 0; }
			$png = sprintf("%.2f_%.2f_%.2f_%.2f.png",$x, $y, $X, $Y); # Truncate the values to 2 decimals to accommodate any difference in the values sent by Terria
			$png = "$subdir/$png";
			my $size = -s $png;
			if (-f $png && $size > 0) 
			{
				next; 
			}
 
			$cmd = "curl -s --max-time $curl_timeout '$url" . "$x,$y,$X,$Y&width=256&height=256" . "'> $png";
			system ("$cmd&");
			if ($jobs >= $max_jobs)
			{
				print "ThrottleTheJobs: Total: $jobs. $tot\n";
				&ThrottleTheJobs;
				$jobs = 0;
			}
		}
	}
}
sub CreateTilesCC
{
	$o = $diffs{$zoom}; # The X,Y offset for this zoom level between the bottom left corner and the top right corner of the tile
	@aus_bbox = split (/,/, $aus_bboxes{$zoom}); # The continent BBOX for this zoom level.
	$x = $aus_bbox[0];
	$y = $aus_bbox[1];
	$X = $aus_bbox[2];
	$Y = $aus_bbox[3];

	$ct0 = time();
	$kk = 0;
	$tot = 0;
	
	# The subdir to create the PNG files.
	$subdir = "$layer/$date/$zoom";
	`mkdir -p $subdir`; # Tiles will be created in this Tmp dir
	
	# Iterate through the X,Y coordinates to construct the tile's BBOX. 
	for (my $k=$y; $k < $Y; $k+=$o)
	{
		$kk++;
		$jj = 0;
		for (my $j=$x; $j < $X; $j+=$o)
		{
			$jj++;
			my $x = $j;
			my $X = $x + $o; if ($X < -0 && $X > -2) { $X = 0; }
			my $y = $k;
			my $Y = $y + $o; if ($y == 0 || ($Y < -0 && $Y > -2)) { $Y = 0; }
			$png = sprintf("%.2f_%.2f_%.2f_%.2f.png",$x, $y, $X, $Y); # Truncate the values to 2 decimals to accommodate any difference in the values sent by Terria
			$png = "$subdir/$png";
			$created = 0;
			if (-f $png) { $created = 1; }
			if ($created)
			{
			}
			else
			{
				$cmd = "curl -s '$url" . "$x,$y,$X,$Y&width=256&height=256" . "'> $png";
				system ("$cmd&");
				$tot++;
#				print "$tot. $cmd\n";
			}
		}
		
		# Too many job in the queue can slow down things. So, make sure that the numbers are within limits.
		# The normal parallelisation will send only as many jobs as there are cores and wait for their completion before sending another batch.
		# It will prove to be more time consuming, as the jobs here take different times to complete. 
		# Hence, overloading the CPUs with more jobs than the number of cores. Even with some jobs taking more time, the overall speed will increase.
		# This logic must be reviewed.
		if ($high_jobs) { sleep(5); }
		$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
		chop ($n_curls);
		$high_jobs = 0;
		$on_curls = $n_curls;
		if ($n_curls > $jj)
		{
			print("Jobs exceed $jj: Row $kk/$jj. Jobs: $n_curls/$on_curls. Waiting to come down....\n");
		}
		while ($n_curls > $jj) # Max jobs at a time. Wait until the number comes down
		{
			$high_jobs = 1;
			sleep(1);
			$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
			chop ($n_curls);
		}
	}
	# Wait until all remaining jobs are finished
	$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
	chop ($n_curls);
	$on_curls = $n_curls;
	while ($n_curls > 0) # Remaining jobs
	{
		sleep(1);
		$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
		chop ($n_curls);
		print("Remaining jobs: $n_curls/$on_curls\n");
	}
	
	$ct1 = time();
	$et1 = $ct1 - $ct0;
	
	# Remove the blank tiles
	print "Created the tiles. Purging the blanks... \n";
	chdir($subdir);
	$ls = `ls -l`;
	@ls = split(/\n/, $ls);
	foreach $line (@ls)
	{
		if ($line =~ / 820 / || $line =~ / 0 /)
		{
			my @fields = split(/ /, $line);
			my $len = $#fields;
			$png = $fields[$len];
			`rm $png`;
		}
	}
	print "Creating a 'tar' archive and deleting the individual files... \n";
	# Tar the files
	$tarfile = $layer . "_" . $date . "_" . $zoom . ".tar";
	`tar cf $tarfile ./*.png`;
	`gzip $tarfile`;
	
	# Remove the PNGs
	`rm -f ./*.png`;
	
	$ct2 = time();
	$et2 = $ct2 - $ct1;
	print "Finished! $et1 sec to create tiles; $et2 sec to purge the blanks.\nHit return to continue...\n";
}
sub SanityCheck
{
	$exit = 0;
	if (!$sc_action) { print "You must specify an action. e.g. cc\n"; $exit = 1; }
	if (!$layer) { print "You must specify a layer. e.g. landsat5_nbar_16day\n"; $exit = 1; }
	if (!$date)  { print "You must specify a date. e.g. 2011-11-08\n"; $exit = 1; }
	if (!$zoom)  { print "You must specify a zoom level. e.g. 200\n"; $exit = 1; }
	if ($zoom < 5 || $zoom > 3000) { print "Zoom level must be between 5 and 3000. e.g. 200\n"; $exit = 1;}
	if ($exit)
	{
		print "Syntax: create_tiles_all.pl cc landsat5_nbar_16day 2011-11-08 50 200\nExitting!\n";
		exit;
	}
}
# Main body of the script
sub do_main
{
	$sc_action = $ARGV[0];
	$layer = $ARGV[1];
	$date = $ARGV[2]; 
	$zoom = $ARGV[3]; 
	&SanityCheck;
	if ($sc_action eq "cc") # Create the coordinates for tiles. e.g. './create_tiles_using_calculated_coords.pl cc landsat5_nbar_16day 2011-11-08 200'
	{
		$time = $date . "T00:00:00.000Z";
		$url = "http://localhost:9511/ows?time=$time&srs=EPSG:3857&transparent=true&format=image/png&exceptions=application/vnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=$layer&bbox=";
		&CreateTilesCC;
	}

	if ($sc_action eq "dc0") # Check which dates have data. This is important for the Sentinel2
	{
		$getcap = `curl 'http://localhost:9511/ows?service=WMS&version=1.3.0&request=GetCapabilities'`;
#print "$getcap\n";
		my @filecontent = split(/\n/, $getcap);
		my $len = $#filecontent;
		for (my $j=0; $j <= $len; $j++)
		{
			if ($filecontent[$j] =~ /<Dimension name="time" default="current" current="True" units="ISO8601">(.*)<\/Dimension>/)
			{
				$times = $1;
				@times = split(/,/,$times);
				my $lt = $#times;
				for (my $k=0; $k <= $lt; $k++)
				{
					$time = $times[$k];
					$date = $time;
					$date =~ s/T00:00:00.000Z//g;
					$url = "http://localhost:9511/ows?time=$time&srs=EPSG:3857&transparent=true&format=image/png&exceptions=application/vnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=$layer&bbox=";
#					print "$times[$k]\n";
					print "$k.$lt. $date\n";
#					&CheckData;
				}
			}
		}
		exit;
	}
	if ($sc_action eq "dc") # Check which dates have data. This is important for the Sentinel2
	{
		$homedir = `pwd`;
		chop($homedir);
#		@zoom_levels = (3000,1000,500,300,200,100);		
		@zoom_levels = (20);		
		#sentinel2_nbart_daily
#		@times = ("2015-08-21","2015-10-20","2015-12-27","2016-01-06","2016-02-20","2016-04-11","2016-06-16","2016-08-04","2016-09-25","2016-10-05","2016-12-02","2016-12-08","2017-01-20","2017-03-27","2017-05-16","2017-06-30","2017-07-11","2017-08-22","2017-08-28","2017-09-03","2017-09-09","2017-10-23","2017-10-29","2017-11-02","2017-11-08","2018-02-11");

		# DEA LS8_NBAR_16-day
#		@times = ("2013-03-19","2013-04-04","2013-04-20","2013-05-06","2013-05-22","2013-06-07","2013-06-23","2013-07-09","2013-07-25","2013-08-10","2013-08-26","2013-09-11","2013-09-27","2013-10-13","2013-10-29","2013-11-14","2013-11-30","2013-12-16","2014-01-01","2014-01-17","2014-02-02","2014-02-18","2014-03-06","2014-03-22","2014-04-07","2014-04-23","2014-05-09","2014-05-25","2014-06-10","2014-06-26","2014-07-12","2014-07-28","2014-08-13","2014-08-29","2014-09-14","2014-09-30","2014-10-16","2014-11-01","2014-11-17","2014-12-03","2014-12-19","2015-01-04","2015-01-20","2015-02-05","2015-02-21","2015-03-09","2015-03-25","2015-04-10","2015-04-26","2015-05-12","2015-05-28","2015-06-13","2015-06-29","2015-07-15","2015-07-31","2015-08-16","2015-09-01","2015-09-17","2015-10-03","2015-10-19","2015-11-04","2015-11-20","2015-12-06","2015-12-22","2016-01-07","2016-01-23","2016-02-08","2016-02-24","2016-03-11","2016-03-27","2016-04-12","2016-04-28","2016-05-14","2016-05-30","2016-06-15","2016-07-01","2016-07-17","2016-08-02","2016-08-18","2016-09-03","2016-09-19","2016-10-05","2016-10-21","2016-11-06","2016-11-22","2016-12-08","2016-12-24","2017-01-09","2017-01-25","2017-02-10","2017-02-26","2017-03-14","2017-03-30","2017-04-15","2017-05-01","2017-05-17","2017-06-02","2017-06-18","2017-07-04","2017-07-20","2017-08-05","2017-08-21","2017-09-06","2017-09-22","2017-10-08","2017-10-24","2017-11-09","2017-11-25","2017-12-11","2017-12-27","2018-01-12","2018-01-28","2018-02-13","2018-03-01","2018-03-17","2018-04-02","2018-04-18","2018-05-04","2018-05-20","2018-06-05","2018-06-21","2018-07-07","2018-07-23","2018-08-08","2018-08-24","2018-09-09","2018-09-25","2018-10-11","2018-10-27","2018-11-12","2018-11-28","2018-12-14","2018-12-30","2019-01-15","2019-01-31","2019-02-16","2019-03-04","2019-03-20","2019-04-05","2019-04-21","2019-05-07");
#		@times = ("2013-04-20","2013-05-06","2013-05-22","2013-06-07","2013-06-23");
#		@times = ("2013-05-06","2013-05-22");
		@times = ("2013-03-19");

			my $lt = $#times;
			$n_times = $lt+=1;
			print "homedir = $homedir\nStarting to process $n_times time slices...\n";		
			for (my $k=0; $k < $lt; $k++)
			{
				foreach $zoom (@zoom_levels)
				{
					print "Processing: $date/$zoom\n";		
					$ct0 = time();
					chdir($homedir);
					$ct00 = time();
					$k1++;
					$time = $times[$k] . "T00:00:00.000Z";
					$date = $time;
					$date =~ s/T00:00:00.000Z//g;
					$url = "http://localhost:9511/ows?time=$time&srs=EPSG:3857&transparent=true&format=image/png&exceptions=application/vnd.ogc.se_xml&styles=&tiled=true&feature_count=101&service=WMS&version=1.1.1&request=GetMap&layers=$layer&bbox=";
#					print "$k. $date; $zoom\n";
					&CreateTilesDC;
					&WaitForJobs;
					&PurgeBlanksAndCreateTarGz;
					$ct1 = time();
					$et0 = $ct1 - $ct00;
					print "Finished this time slice in $et0 sec.\n";
				}
			}
			$ct2 = time();
			$et2 = $ct2 - $ct1;
			print "Finished! $et2 sec to process $n_times time slices.\nHit return to continue...\n";
		exit;
=pod		
		# Wait until all remaining jobs are finished
		$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
		chop ($n_curls);
		$on_curls = $n_curls;
		while ($n_curls > 0) # Remaining jobs
		{
			sleep(3);
			$n_curls = `ps -ef | grep curl | grep -v grep | wc -l`;
			chop ($n_curls);
			print("Remaining jobs: $n_curls/$on_curls\n");
		}
		$ct1 = time();
		$et1 = $ct1 - $ct0;
		# Remove the blank tiles
		print "Created the tiles. Purging the blanks...\n";
		for (my $k=0; $k < $lt; $k++)
		{
			$time = $times[$k] . "T00:00:00.000Z";
			$date = $time;
			$date =~ s/T00:00:00.000Z//g;
			$subdir = "$homedir/$date/$zoom";
			print "subdir = $subdir\n";
			chdir($subdir);
			$ls = `ls -l`;
			@ls = split(/\n/, $ls);
			foreach $line (@ls)
			{
				if ($line =~ / 820 / || $line =~ / 0 /)
				{
#print "$line\n";
					my @fields = split(/ /, $line);
					my $len = $#fields;
					$png = $fields[$len];
					`rm $png`;
				}
			}
			print "Creating a 'tar' archive and deleting the individual files... \n";
			# Tar the files
			$n_png = `ls -1 *.png | wc -l`;
			chop ($n_png);
			if ($n_png)
			{
				$tarfile = $layer . "_" . $date . "_" . $zoom . ".tar";
				`tar cf $tarfile ./*.png`;
				`gzip $tarfile`;
				# Remove the PNGs
				`rm -f ./*.png`;
			}
			else
			{
				print "No PNG files for $date/$zoom.";
			}
		}
		
		
		$ct2 = time();
		$et2 = $ct2 - $ct1;
		print "Finished! $et1 sec to create tiles; $et2 sec to purge the blanks.\nHit return to continue...\n";
=cut
	}
	if ($sc_action eq "dct") # Check which dates have data. This is important for the Sentinel2
	{
		$filename = $ARGV[1];
		open (INP, "<$filename");
		while ($line = <INP>)
		{
			$n++;
			if ($line =~ /timestamps":\["(.*?)Z"\]/)
			{
				$date = $1;
				$date =~ s/T.*//g;
				print "$date\n";
			}
#			exit;
		}
		close(INP);
	}
}
# The difference between MaxX and MinX; The same as MaxY - MinY is used to calculate the BBOXes
%diffs = (
	5 => 19567.8792411,
	10 => 39135.75848201,
	20 => 78271.51696402,
	50 => 156543.03392804,
	100 => 313086.06785608,
	200 => 626172.13571216,
	300 => 1252344.27142434,
	500 => 2504688.54284865,
	1000 => 5009377.0856973,
	3000 => 10018754.17139462,
#		5000 => 20037508.34278924
);
# The bounding boxes to cover the entire continent at different zoom levels.
%aus_bboxes = (
#		5000 => "0,0,20037508.342789244,20037508.342789244",
	3000 => "10018754.17139462,-10018754.17139462,20037508.342789244,0",
	1000 => "10018754.17139462,-5009377.085697312,20037508.342789244,0",
	500 => "12523442.714243278,-7514065.628545966,15028131.257091936,0",
	300 => "12523442.714243278,-6261721.357121639,17532819.79994059,-1252344.271424327",
	200 => "12523442.714243278,-5635549.221409474,17532819.79994059,-1252344.271424327",
	100 => "12523442.714243278,-5635549.221409474,17532819.79994059,-1252344.271424327",
	50  => "12523442.714243278,-5635549.221409474,17532819.79994059,-1252344.271424327",
	20  => "12523442.714243278,-5635549.221409474,17532819.79994059,-1252344.271424327",
	10  => "12523442.714243278,-5635549.221409474,17532819.79994059,-1252344.271424327",
	5   => "12523442.714243278,-5635549.221409474,17532819.79994059,-1252344.271424327",
	);
&do_main;

