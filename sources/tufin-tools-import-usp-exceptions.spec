#!/bin/bash
## COPYRIGHT (c) 2003-2016 by Tufin Software Technologies Ltd.
## All rights reserved.
##
## The Product and all rights, without limitation including proprietary rights
## therein, are owned by Tufin Technologies and/or its licensors and affiliates
## and are protected by international treaty provisions and all other
## applicable national laws of the country in which it is being used.
## The structure, organization, and code of the Product are the valuable trade
## secrets and confidential information of Tufin Technologies and/or its
## licensors and affiliates.
## Any copies must and shall contain the same copyright.
##
## THIS SOFTWARE IS PROVIDED BY TUFIN SOFTWARE TECHNOLOGES LTD. AND CONTRIBUTORS
## ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
## TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
## PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COMPANY OR CONTRIBUTORS
## BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
## CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
## SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
## INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
## CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
## ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
## POSSIBILITY OF SUCH DAMAGE.
##
%define _topdir	 	/opt/tufin/rpm-build
%define name		tufin-tools-import-usp-exceptions
%define release		20160926
%define version 	1.0
%define buildroot 	%{_topdir}/%{name}-%{version}-root

BuildArch:		noarch
BuildRoot:	 	%{buildroot}
URL: 			http://www.tufin.com
Summary: 		/tools utility to import USP exceptions from CSV file
License: 		GPL
Name: 			%{name}
Version: 		%{version}
Release: 		%{release}
Source: 		%{name}-%{version}.tar.gz
Prefix: 		/usr
Group: 			Development/Tools
Requires:		st >= 15.4, perl >= 5.10, perl-CGI >= 3.51, perl-Crypt-SSLeay >= 0.57, tufin-perl-extlib >= 1.0
# As we only want to copy the file tree, we disable the Auto Requires and Provides to not conflict with TufinOS system RPMs
AutoReqProv:		no

%description
Creates a new /tools entry for importing USP exceptions from CSV file

# Preparation when building RPM, simply tar xzf source files in BUILD
%prep
%setup -q

# Script executed when building RPM, simply copy files from BUILD to BUILDROOT (that will be installed on target system)
%install
install -m 0755 -d $RPM_BUILD_ROOT/var/www/html/tools/
install -m 0755 -d $RPM_BUILD_ROOT/var/www/html/tools/css-import-usp-exceptions/
install -m 0755 -d $RPM_BUILD_ROOT/var/www/cgi-bin/
install -m 0644 import-usp-exceptions.htm $RPM_BUILD_ROOT/var/www/html/tools/
install -m 0644 import-usp-exceptions.xlsx $RPM_BUILD_ROOT/var/www/html/tools/
install -m 0750 import-usp-exceptions.cgi $RPM_BUILD_ROOT/var/www/cgi-bin/
install -m 0644 css-import-usp-exceptions/pure-min.css $RPM_BUILD_ROOT/var/www/html/tools/css-import-usp-exceptions/
install -m 0644 css-import-usp-exceptions/tufin-se.css $RPM_BUILD_ROOT/var/www/html/tools/css-import-usp-exceptions/

# Set files permissions on target system
%files
%defattr(0644, apache, st, 0755)
/var/www/html/tools/import-usp-exceptions.htm
/var/www/html/tools/import-usp-exceptions.xlsx
/var/www/html/tools/css-import-usp-exceptions/pure-min.css
/var/www/html/tools/css-import-usp-exceptions/tufin-se.css
%attr(0750, root, st) /var/www/cgi-bin/import-usp-exceptions.cgi

%clean
rm -rf "$RPM_BUILD_ROOT"

# Post Installation script when RPM is installed
%post
# Check if files exists
if [ ! -f /var/www/cgi-bin/import-usp-exceptions.cgi ] ; then
    echo "Error: please make sure that /var/www/cgi-bin/import-usp-exceptions.cgi is on filesystem!"
    exit 1
fi

# Check if files has not been altered
MD5=`md5sum /var/www/cgi-bin/import-usp-exceptions.cgi   | cut -d ' ' -f1`
if [ "$MD5" != "7dba7383e9694f4f498d005c0cc0af94" ] ; then
    echo "Error: It seems that the script has been modified"
    echo "MD5(/var/www/cgi-bin/import-usp-exceptions.cgi) should be 7dba7383e9694f4f498d005c0cc0af94"
    exit 1
fi

# Check if entry already exists in DB
RES=`psql -qAt -U postgres securetrack -c "select exists (SELECT tool_id from user_tools where link='import-usp-exceptions.htm');"`
if [ $RES == "f" ]; then
	echo "Creating entry in PostgreSQL DB"
 	psql -qAt -U postgres securetrack -c "INSERT INTO user_tools (link, description, user_allowed, user_enabled) VALUES ('import-usp-exceptions.htm', 'Import USP Exceptions from CSV', TRUE, FALSE);"
 	RES=`psql -qAt -U postgres securetrack -c "select exists (SELECT tool_id from user_tools where link='import-usp-exceptions.htm');"`
 	if [ $RES == "f" ]; then
 		echo "Problem during installation, please check user_tools table"
 		exit 1
 	fi
fi
echo "Installation successful"
exit 0

# Post Installation script when RPM is UNinstalled
%postun
# Check if entry already exists in DB
RES=`psql -qAt -U postgres securetrack -c "select exists (SELECT tool_id from user_tools where link='import-usp-exceptions.htm');"`
if [ $RES == "t" ]; then
	echo "Deactivating entry in PostgreSQL DB"
 	psql -qAt -U postgres securetrack -c "DELETE FROM user_tools where link='import-usp-exceptions.htm';"
 	RES=`psql -qAt -U postgres securetrack -c "select exists (SELECT tool_id from user_tools where link='import-usp-exceptions.htm');"`
 	if [ $RES == "t" ]; then
 		echo "Problem during uninstallation, please check user_tools table"
 		exit 1
 	fi
fi
echo "Uninstallation successful"
exit 0