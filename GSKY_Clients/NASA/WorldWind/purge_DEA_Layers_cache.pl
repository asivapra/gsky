#!/usr/bin/env perl
# Created on 31 Mar, 2019
# Last edit: 5 Jul, 2019
# By Dr. Arapaut V. Sivaprasad
=pod
This CGI is for purging the DEA High Resolution tiles created by GoogleEarth and NASA World Wind usage.
=cut
# -----------------------------------
require "/var/www/cgi-bin/common.pl";
sub d
{
  $line = $_[0]; if (!$line) { $line = "OK"; }
  $exit = $_[1];
  if (!$headerAdded) { print "Content-type: text/html\n\n"; $headerAdded = 1; }
  print "$line<br>\n";
  if ($exit) { exit; }
}
sub do_main
{
	# To purge daily the high res tiles
	chdir ($basedir);
	$dir1 = `ls -FR | grep "/0.1"`;
	$dir2 = `ls -FR | grep "/0.02"`;
	$dirs = $dir1 . $dir2;
	@dirs = split(/\n/, $dirs);
	open(OUT, ">>/var/www/cgi-bin/purge_DEA_Layers_cache.log");
	print OUT "------------------------------------------------------------\n$ProcessTime\n";
	foreach $dir (@dirs)
	{
		$dir =~ s/://g;
		chdir ($dir);
		$pwd = `pwd`;
#		print "$pwd";
#		print OUT "$pwd";
		@dir = split(/\//, $pwd);
		$n = $#dir + 1;
#		if ($n != 7) { next; } # /local/GEWeb/DEA_Layers/landsat5_geomedian/1997-01-01/0.1
		if ($pwd !~ /^\/local\/GEWeb\/DEA_Layers/) { next; } # /local/GEWeb/DEA_Layers/landsat5_geomedian/1997-01-01/0.1
		$png = `ls -1 *.png | wc -l`;
		$png =~ s/\n//g;
		if ($png) 
		{ 
			print OUT "$pwd";
			print OUT "**** Deleting: $png PNG files.\n"; 
		}
		`rm *.png`;
		chdir ($basedir);
	}
	close(OUT);
}
$|=1;
#$docroot = $ENV{DOCUMENT_ROOT};
$basedir = "/local/GEWeb/DEA_Layers";

$ProcessTime = `/bin/date`; $ProcessTime =~ s/\n//g ;
&do_main;
=pod
Cache location: C:\Users\avs29\AppData\Local\Google\Chrome\User Data\Default\Cache
=cut
