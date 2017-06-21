# malta-files

Journalists working with EIC.network dug into hundreds of thousands of
documents that show how Malta operates a tax system where companies pay
the lowest tax on profits in the EU. Part of the data that was used for
this research is the public Malta Registry of Companies. If you want to
use our scraper yourself, go ahead, you should find everything you need
here.

We have re-arranged, cleaned and made searchable in new ways the public
information contained in the register.

For more information about Malta Files investigation, see : https://eic.network/projects/malta-files

Keep in mind that the data we make available is only for information
purposes and does not indicate any illegal activity. For any current and
official status go to the Malta Registry of Companies here
http://rocsupport.mfsa.com.mt/pages/SearchCompanyInformation.asp


# technical information

This a scraper that uses PhantomJS and Selenium for navigating around, so 
you'd better have those two installed to begin with.

In the file [proxy_list.txt](./proxy_list.txt) you will find a list of 
proxies that need to be supplied in order for the scraper to be able to 
change its IP address once every few hundred requests. Of course you can 
supply your own proxies in the list, so we only left one as example.

For the most part, navigating the Maltese RoC website requires authentication. 
In the file [lookup.py](./lookup.py) you will find a dict called `_LOGIN_DATA`, 
which is where you should provide your own credentials.

The whole scraping machine starts by running [the shell script found in the root 
directory of this project](./runner.sh).

After you start it, make sure the internet connection is stable and let it 
finish. It will likely take a day or more, depending on your bandwidth and 
proxies speed.

That's it, after it runs you should see some results similar to what is now 
in the [output](./output) directory.

See [the results repository](https://github.com/eic-network/malta-files) for 
more info about the data extracted.
