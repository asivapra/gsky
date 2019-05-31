#!/usr/bin/env perl
# Created on 31 Mar, 2019
# Last edit: 3 Apr, 2019
# By Dr. Arapaut V. Sivaprasad
=pod
This CGI is for creating the KMLs for displaying the GSKY layers via Google Earth Web.
See http://www.webgenie.com/WebGoogleEarth/
=cut
# -----------------------------------

require "/var/www/cgi-bin/common.pl";
#require "/var/www/vhosts/webgenie.com/cgi-bin/common.pl";
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
sub GetOuters
{
	my $relations = $xml_hash->{osm}->{relation};
	my @relations = @$relations;
	my $len = $#relations;
	my @outers = ();
}
sub OrderTheOuters
{
#pd(\@outers);	
	my $way_ids = $xml_hash->{osm}->{way};
	my @way_ids = @$way_ids;
	my $len = $#outers;
#p("	for (my $j=0; $j <= $len; $j++)");
	for (my $j=0; $j <= $len; $j++)
	{
#pd($outers[$j]);				
		my $len1 = $#way_ids;
print "$outers[$j]:\n";				
		for (my $k=0; $k <= $len1; $k++)
		{
			if ($way_ids[$k]->{id} == $outers[$j])
			{
#p($way_ids[$k]->{id});				
				my $way_nds = $way_ids[$k]->{nd};
				@way_nds = @$way_nds;
				foreach $nd (@way_nds)
				{
print "   $nd->{ref}\n";				
				}
=pod
				my $first_id = $way_nds[0]->{ref};
				my $last_id = $way_nds[$#way_nds]->{ref};
				$$outers[$j]->{first} = $first_id;
				$$outers[$j]->{last} = $last_id;
print "$outers[$j],$first_id,$last_id\n";				
=cut
#pd($$outers[$j]);
#pd(\@way_nds,1);	
			}
		}
	}
}
sub GetLakes
{
	my $relations = $xml_hash->{osm}->{relation};
	my @relations = @$relations;
	my $len = $#relations;
	my @lakes = ();
	for (my $j=0; $j <= $len; $j++)
	{
		if ($relations[$j]->{tag}[0]->{k} eq "name")
		{
			$line = $relations[$j]->{tag}[0]->{v};
#			print $relations[$j]->{tag}[0]->{v} . "\n";
#			push (@lakes, $relations[$j]->{tag}[0]->{v});
		}
		else
		{
			$line = " ";
#			push (@lakes, " ");
		}
		my $members = $relations[$j]->{member};
#p($relations[$j]->{id});		
#pd($members);
#exit;			

		# First the outer IDs
		@outers = ();
		foreach $member (@$members)
		{
			if ($member->{role} eq "outer")
			{
				push (@outers,$member->{ref}); 
				$line .= ";" . $member->{ref} . "|" . $member->{role};
			}
		}
#pd(\@outers);	
		$ordered_outers = OrderTheOuters;
		# Then the inners
		foreach $member (@$members)
		{
			if ($member->{role} eq "inner")
			{
				$line .= ";" . $member->{ref} . "|" . $member->{role};
			}
		}
		push (@lakes, $line);
#=cut
	}
	return \@lakes;
}
sub do_main
{
	chdir "/var/www/html/NASA/WorldWind/data/AVS";
	my $filename = "natural_water.json";
	my $xml_doc = $parser->parsefile ($filename);
#  Convertion from a XML::DOM::Document into a HASH
	$xml_hash = $xml_converter->fromDOMtoHash($xml_doc);
	my $lakes = GetLakes;
#	my $outers = GetOuters;
#	my @keys = keys $xml_hash;
#pd($lakes);	
#pd($xml_hash->{osm}->{relation});
}
$|=1;
&do_main;
