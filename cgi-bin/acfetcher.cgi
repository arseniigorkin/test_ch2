#!/usr/bin/perl
use strict;
use warnings FATAL => 'all';
use v5.10;
use utf8::all;
use JSON::MaybeXS;
use HTTP::Tiny;

=head2 About the script
	This script does the next functions:
	1) receives a request form the sender via GET method in the format: q=[terms]
	2) accepts only 3+ symbols given at a time, thus, checking against it
	3) sends a request to the endpoint remote host via GET method
	4) checks against errors
	5) creates an HTML table with given results and prints it out to the sender
	6) quietly dies... :)
	
	A few words about the modules choice:
	utf8::all
		I have used this module because it helps to work with symbols form Norwegian
	JSON::MaybeXS
		This one is a very fast wrapper for most of JSON backend works.
		Since it works with JSON::XS (the fastest JSON module), it is the best choice for this job.
	HTTP::Tiny
		Sure thing we could use any other similar and much powerful ones, like LWP family, for example.
		But again, here it is not a need, thus, this lite and fast module is here.
		
		I used to use here friendly errors, so, if the server response will include
		some non-critical error, giving the same time a good data, the script won't  die.
=cut

say "Content-type: text/html\n\n";
my ($remote_host, $query, $response, $h_JSON);

# setting up a remote host for the endpoint (the full address)
$remote_host = "https://www.husleie.no/api/adresse";
$remote_host .= "?q=";

# receiving a query from the URI (GET method)
if($ENV{QUERY_STRING}) {
	$query = $ENV{QUERY_STRING};
	$query =~/^(?:q\=)([^=]*)(?:.*)/;
	$query = $1;
	
	# checking if the query has at least 3 symbols
	if (scalar(@{[$query =~/\S/g]}) < 3) {
		say "Please, continue typing for up to at least 3 letters to begin search.";
		exit;
	}
	makeRequest(); # if everything is OK with the query, going to get the data form the endpoint
}

else {
	error("No parameters have been given");
}

# this function is sends API GET request and treats status codes
sub makeRequest{
	$response = HTTP::Tiny->new->get($remote_host.$query);
	error("<b>$response->{status}:</b> $response->{reason}") if ($response->{status} != 200);
	fetchReceivedData(); # forwarding process to the parser
}

# this sub is working on a data, received form the GET request
sub fetchReceivedData{
	# converting the JSON data to the ARRAYREF
	$h_JSON = decode_json($response->{content});
	
	# checking, if there is an error and there is only a single string, then throwing an error
	if ($h_JSON->[0]->{error}
		and $h_JSON->[0]->{n}
		and ($h_JSON->[0]->{n} eq "Query contains illegal characters"
			or $h_JSON->[0]->{n} eq "Ingen treff")
		and scalar(@{$h_JSON}) == 1) {
		
			say "<img src='catplays.gif'><br />\
			<b>Sadly, nothing has been found yet. Please, try again harder.</b>";
	}
	# if the error is just due to the endpoint script fails and we have
	# a good data (more, than 1 row), though, then, start working on it
	elsif ($h_JSON->[0]->{error}
		and scalar(@{$h_JSON}) >> 1) {
		
			# starting creating a table with results
			wrapInATable();
	}
}

# this sub builds an HTML table with results
sub wrapInATable{
	
	# processing the first row against an error
	# If the error is about "Query contains illegal characters" or "Ingen treff",
	# that can be responded along with a good data, then we will remove this row.
	# If there is another error - we will treat it as others.
	if ($h_JSON->[0]->{error}
		and $h_JSON->[0]->{n}
		and ($h_JSON->[0]->{n} eq "Query contains illegal characters"
			or $h_JSON->[0]->{n} eq "Ingen treff")) {
		
		# removing the first string from the data pool, if it has an error inside
		shift @{$h_JSON} if ($h_JSON->[0]->{error});
	}
	
	my $outputHTML = <<HTMLBEGIN;
<table>
	<tr>
    <th>Id</th>
    <th>Address</th>
    <th>Municipality</th>
    <th>Zip code</th>
    <th>Postal area</th>
  </tr>
HTMLBEGIN
	
	
	
	# then starting filling the table
	for(@{$h_JSON}){
		
		if ($_->{error}) {
			# checking, if this is a row with an error and, thus, removing it
			$outputHTML .= <<ADDERRTR;
	<tr class="error">
		<td colspan="5">This row has an error inside: <b>$_->{n}</b></td>
	</tr>
ADDERRTR
		}
		else { # if this is a good row (with no error)
			$outputHTML .= <<ADDTR;
	<tr>
		<td>$_->{id}</td>
		<td>$_->{n}</td>
		<td>$_->{m}</td>
		<td>$_->{postnr}</td>
		<td>$_->{poststed}</td>
	</tr>
ADDTR
		}
	}
	$outputHTML .= <<HTMLEND;
</table>
HTMLEND
	say $outputHTML;
	exit;
}

# this simple function outputs errors. I added it to make it possible,
# in the "could be" future, been elaborated and converted in a better UI
sub error{
	my $content = shift;
	
	print <<HTML;
<h2>Error</h2> $content.
HTML
	exit;
}