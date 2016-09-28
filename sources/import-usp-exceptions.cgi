#!/usr/bin/perl
# Romain Morel
# romain@tufin.com
# 23/09/2015
# 
use lib '/opt/tufin/securitysuite/ps/perl/extlib/lib/perl5';
use strict;
use warnings;
use CGI;
use CGI::Carp qw ( fatalsToBrowser );
use File::Basename;
use MIME::Base64;
use REST::Client;
use JSON;
use Net::Netmask;
use Data::Dumper;

my $DEBUG = 0;
# SSL verification
$ENV{PERL_LWP_SSL_VERIFY_HOSTNAME} = 0;

###############################################################################
#
# CONTENT / PARAMETER CHECKGING
#
###############################################################################

# Define the filesize limit to 5MB
$CGI::POST_MAX = 1024 * 5000;
my $safe_filename_characters = "a-zA-Z0-9_.-";
my $upload_dir = "/tmp/";

# Retrieve Request parameters
my $query = new CGI;
my $filename = $query->param("filename");
if (!$filename) {
    print $query->header();
    die "There was a problem uploading your file (try a smaller size).";
}

# Extract and clean filename 
my ( $name, $path, $extension ) = fileparse($filename, '..*');
$filename = $name . $extension;
$filename =~ tr/ /_/;
$filename =~ s/[^$safe_filename_characters]//g;
if ( $filename =~ /^([$safe_filename_characters]+)$/ ) {
    $filename = $1;
}
else {
    die "Filename contains invalid characters";
}


###############################################################################
#
# ST REST API SETUP
#
###############################################################################

# Prepare Rest::Client for SecureTrack
my $st_client = REST::Client->new(host => "https://localhost");
$st_client->addHeader("Accept", "application/json" );
# Forward uid and sid cookies to keep user credentials when using REST API
my $sid = $query->cookie('sid');
my $uid = $query->cookie('uid');
$st_client->addHeader("Cookie", "uid=$uid; sid=$sid");

########################################################################
#
# MAIN LOGIC
#
###############################################################################

# Recuperation des Exceptions
my $exceptions = load_csv($filename);
if ($query->param("submit")) {
    process_submit();
}
else {
    die "Unsupported action\n";
}

###############################################################################
#
# HTML OUTPUT
#
###############################################################################
sub print_header {
    print $query->header();
    print <<HEADER;
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        
        <meta http-equiv="cache-control" content="max-age=0" />
        <meta http-equiv="cache-control" content="no-cache" />
        <meta http-equiv="expires" content="0" />
        <meta http-equiv="expires" content="Tue, 01 Jan 1980 1:00:00 GMT" />
        <meta http-equiv="pragma" content="no-cache" />
        
        <title>ST SE Tools - Import USP Exceptions</title>

        <link rel="stylesheet" href="/tools/css-import-usp-exceptions/pure-min.css">  
        <link rel="stylesheet" href="/tools/css-import-usp-exceptions/tufin-se.css">

        <script type="text/javascript" src="/lib/jquery.min.js"></script>
        <script type="text/javascript" src="/js/stinit.js"></script>

    </head>
    <body>
    <div class="header">
        <div class="home-menu pure-menu pure-menu-horizontal pure-menu-fixed">
            <a class="pure-menu-heading" href="">SecureTrack SE Tools</a>        
        </div>
    </div>


    <div class="content-wrapper">
            <div class="pure-g">
                <div class="l-box pure-u-1">
                <h3>Import USP Exceptions</h3>
                <table class="pure-table pure-table-striped">
HEADER
}

sub print_footer {

    print <<FOOTER;
            </div>
        </div>
    </div>
    </body>
</html>
FOOTER
}


sub process_submit {
# Process Exceptions and display summary table
foreach my $exception (@$exceptions) {
    if ($exception->{skip}) {
        $exception->{ret} = 0;
        $exception->{message} = $exception->{skip};
    }
    else {
        delete $exception->{skip};
        my ($ret, $message) = add_usp_exception($exception);
        $exception->{ret} = $ret;
        $exception->{message} = $message;
    }
}

print_header();
print "<thead>
        <tr>
            <th>Exception #</th>
            <th>Return code</th>
            <th>Message</th>
        </tr>
        </thead>
        <tbody>";

my $cpt = 0;
my $i = 1;
foreach my $exception (@$exceptions) {
    print "<tr><td>$i</td>";
    if ($exception->{ret} == 1) {
        print '<td class="success">OK</td>';
    }
    else {
        print '<td class="error">ERROR</td>';
    }
    print "<td>$exception->{message}</td></tr>";
    $cpt++ if $exception->{ret};
    $i++
}

print "</tbody>
        </table>
        <p>$cpt exceptions imported</p>
        <a href=\"/tools/import-usp-exceptions.htm\">Back to Import USP Exceptions</a>";
print_footer();
}


###############################################################################
#
# CSV PARSER
#
###############################################################################
sub load_csv {
    my $csv_file = shift;
    my @exceptions;

    # Process file
    my $upload_filehandle = $query->upload("filename");
    while (<$upload_filehandle>) {
        # Parse CSV
        chomp;
        next if $_ =~ m/^#/;
        my ($usp_name, $src_zone, $dst_zone, $srcs, $dsts, $services, $exception_name, $expiration_date, $creation_date, $ticket_id, $created_by, $approved_by, $requested_by, $description) = split /;/, $_;
        my $exception;
        $exception->{skip} = 0;
        
        # Define Exception
        if ($exception_name and $src_zone and $dst_zone and $srcs and $dsts and $services) {
            # Input Control - Exception name
            if ($exception_name =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{name} = $exception_name; 
            }
            else {
                $exception->{skip} = 'Unvalid Exception name, only alphanumeric characters are allowed';
            }
            
            # Input Control - Expiration date
            if ($expiration_date =~ m/^\d{4}\-\d{2}\-\d{2}$/) {
                $exception->{security_policy_exception}->{expiration_date} = $expiration_date;
            }
            else {
                $exception->{skip} = 'Unvalid Expiration Date format must be %Y-%m-%d';
            }

            # Input Control - Creation date
            if ($creation_date =~ m/^\d{4}\-\d{2}\-\d{2}$/) {
                $exception->{security_policy_exception}->{creation_date} = $creation_date;
            }
            else {
                $exception->{skip} = 'Unvalid Creation Date format must be %Y-%m-%d';
            }

            # Input Control - Ticket ID
            if (!$ticket_id or $ticket_id =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{ticket_id} = $ticket_id;
            }
            else {
                $exception->{skip} = 'Unvalid Ticket ID, only numerics are allowed';
            }
           
            # Input Control - Created By
            if (!$created_by or $created_by =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{created_by} = $created_by;
            }
            else {
                $exception->{skip} = 'Unvalid Created By name, only alphanumeric characters are allowed';
            }

            # Input Control - Approved By
            if (!$approved_by or $approved_by =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{approved_by} = $approved_by;
            }
            else {
                $exception->{skip} = 'Unvalid Approved By name, only alphanumeric characters are allowed';
            }
            
            # Input Control - Requested By
            if (!$requested_by or $requested_by =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{requested_by} = $requested_by;
            }
            else {
                $exception->{skip} = 'Unvalid Requested By name, only alphanumeric characters are allowed';
            }

            # Input Control - Description
            if (!$description or $description =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{description} = $description;
            }
            else {
                $exception->{skip} = 'Unvalid Description, only alphanumeric characters are allowed';
            }
            
            # Input Control - Source Zone
            if ($src_zone =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{security_requirements}->{zone_to_zone_security_requirement}->{from_zone} = $src_zone;
            }
            else {
                $exception->{skip} = 'Unvalid Source Zone name, only alphanumeric characters are allowed';
            }
            
            # Input Control - Destination Zone
            if ($dst_zone =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{security_requirements}->{zone_to_zone_security_requirement}->{to_zone} = $dst_zone;
            }
            else {
                $exception->{skip} = 'Unvalid Destination Zone name, only alphanumeric characters are allowed';
            }

            # Input Control - USP Policy Name
            if ($usp_name =~ m/^[\w\s\-\.]+$/) {
                $exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{security_requirements}->{zone_to_zone_security_requirement}->{policy_name} = $usp_name;
            }
            else {
                $exception->{skip} = 'Unvalid USP Policyname, only alphanumeric characters are allowed';
            }

            # Source
            foreach my $source (split(/,/, $srcs)) {
                $source=~s/^\s+//;
                $source=~s/\s+$//;
                if ($source =~ m/^any$/i) {
                    $exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{source_network_collection}->{is_any} = 1; 
                }
                else {
                    my $block = new Net::Netmask($source);
                    if (!$block->{'ERROR'}) {
                        my $new_object; 
                        $new_object->{'@xsi.type'} = 'subnet';
                        $new_object->{ip} = $block->base();
                        $new_object->{netmask} = $block->mask();
                        push @{$exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{source_network_collection}->{network_items}->{network_item}}, $new_object;    
                    }
                    else {
                        $exception->{skip} = 'Unvalid Source object, only IP or IP/MASK or ANY are allowed '.$block->{'ERROR'};
                    }
                }
            }

            # Destinations
            foreach my $destination (split(/,/, $dsts)) {
                $destination=~s/^\s+//;
                $destination=~s/\s+$//;
                if ($destination =~ m/^any$*/i) {
                    $exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{dest_network_collection}->{is_any} = 1; 
                }
                else {
                     my $block = new Net::Netmask($destination);
                    if (!$block->{'ERROR'}) {
                        my $new_object; 
                        $new_object->{'@xsi.type'} = 'subnet';
                        $new_object->{ip} = $block->base();
                        $new_object->{netmask} = $block->mask();
                        push @{$exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{dest_network_collection}->{network_items}->{network_item}}, $new_object;
                    }
                    else {
                         $exception->{skip} = 'Unvalid Destination object, only IP or IP/MASK or ANY are allowed '.$block->{'ERROR'};
                    }
                }
            }

            # Services
            foreach my $service (split(/,/, $services)) {
                $service=~s/^\s+//;
                $service=~s/\s+$//;
                if ($service =~ m/^any$/i) {
                    $exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{service_collection}->{is_any} = 1; 
                }
                elsif ($service =~ m/icmp/i or $service =~ m/ping/i) {
                     my $new_object; 
                        $new_object->{'@xsi.type'} = 'predefined';
                        $new_object->{predefined_service_name} = 'echo-request';
                        push @{$exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{service_collection}->{service_items}->{service_item}}, $new_object;
                }
                else {
                    if ($service =~ m/^(tcp|udp)\-(\d+)/) {
                        my $new_object; 
                        $new_object->{'@xsi.type'} = 'custom';
                        $new_object->{protocol} = lc($1);
                        $new_object->{port} = $2;
                        push @{$exception->{security_policy_exception}->{exempted_traffic_list}->{exempted_traffic}->{service_collection}->{service_items}->{service_item}}, $new_object;
                    }
                    else {
                         $exception->{skip} = 'Unvalid Service object, only tcp-<port> or udp-<port> or ANY are allowed';
                    }
                }
            }
        }
        else {
            $exception->{skip} = "Please fill all mandatory fields"
        }
        push @exceptions, $exception;
    }
    return \@exceptions;
}

###############################################################################
#
# API HELPERS
#
###############################################################################

sub add_usp_exception { 
    my $usp = shift;
    
    $st_client->addHeader('Content-Type', 'application/json');
    $st_client->POST("/securetrack/api/security_policies/exceptions", to_json($usp));
    
    # Catch return codes
    if ($st_client->responseCode() ne "201") {
        return 0, $st_client->responseContent();
    }
    return 1, $st_client->responseContent();
}
