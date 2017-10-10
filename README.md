# tufin-tools-import-usp-exceptions

![Tufin logo](https://www.dropbox.com/s/0hujyyxob3gb3r2/tufin-square-logo.png?dl=1)

## Introduction
This utility will help you to import Tufin Unified Security Policy (USP) compliance exceptions in SecureTrack using a CSV spreadsheet.

##<a name="dependencies"></a>Dependencies

As this tool is written in perl CGI, it will require the following packages :

* perl >= 5.10 *(included in TufinOS)*
* [perl-CGI](ftp://195.220.108.108/linux/centos/6.8/os/x86_64/Packages/perl-CGI-3.51-141.el6_7.1.x86_64.rpm) >= 3.51
* [perl-Crypt-SSLeay](ftp://195.220.108.108/linux/centos/6.8/os/x86_64/Packages/perl-Crypt-SSLeay-0.57-17.el6.x86_64.rpm) >= 0.57
* [tufin-perl-extlib](https://www.dropbox.com/s/xsd1cs55vnza6wq/tufin-perl-extlib-1.2-20160526.noarch.rpm?dl=1)  >= 1.0
* SecureTrack >= 15.4

*(dependencies compatible with TufinOS 2.X only - 64bits versions)*

## Installation
1. Download all the required rpms documented in section [Dependencies](#dependencies) *(available also under dependencies directory)*
2. Download Import USP Exceptions utility rpm from **GitHub** under **dist** directory
3. Upload all rpms on your SecureTrack installation using your favorite SCP client
4. Run the following cli commands :

~~~bash
# From your upload folder
# Install Dependencies
rpm -ivh perl-CGI-3.51-141.el6_7.1.x86_64.rpm
#[...]
rpm -ivh perl-Crypt-SSLeay-0.57-17.el6.x86_64.rpm
#[...]
rpm -ivh tufin-perl-extlib-1.2-20160526.noarch.rpm
#[...]
# Install Tool
rpm -ivh tufin-tools-import-usp-exceptions-1.0-20160926.noarch.rpm
#Preparing...                ########################################### [100%]
#   1:tufin-tools-import-usp-########################################### [100%]
#Creating entry in PostgreSQL DB
#Installation successful
~~~

## Usage
Once installed, point your favorite web browser to <https://your.tufin.host/tools>, you will see a new link : Import USP Exceptions from CSV.

The following webpage will allow you to upload USP exceptions :

![Import USP Homepage](https://www.dropbox.com/s/u4vwwigmw3zan9t/import-usp-exceptions.png?dl=1)


1. Download the Excel XLSX template from the webpage
2. Fill all your USP Exception data in it
	* **Inner delimiter** for multiple Sources, Destinations and Services is **','**
	* Sources and Destinations **must be IP Address or Subnet (IP/Mask) or ANY**
	* Services **must be tcp or udp with port number, range number or ANY**, ex tcp-443 or udp-53 or tcp-1024-65535
	* Date format **must be : Year-Month-Day (%Y-%m-%d)**
	* CreatedBy **must be a valid SecureTrack account**
	* Exception Name **must be unique** otherwise exception will not be inserted
3. Export the spreadsheet as a **CSV with ';' delimiter**
4. Upload it using the webpage and click **Submit**

## Uninstall
~~~bash
rpm -ev tufin-tools-import-usp-exceptions
~~~

## TODO
* Support for IP Ranges
* Support for Domains

## Licensing
This utility is distributed as a beerware under Apache 2.0 Licence

## Help
For any issues or improvments please contact the [Tufin Developer Community](https://plus.google.com/communities/112366353546062524001) on Google.
