CMScout
======

CMScout is a python open source CMS scanner that automates the process of detecting security flaws of the most popular CMSs. The main purpose of CMScout is to integrate common vulnerabilities for different types of CMSs in a single tool.

At the moment, CMSs supported by CMScout are WordPress, Joomla, Drupal and Moodle.

CMScout is an independent fork of CMSmap; see [History and credit](#history-and-credit).

Please note that this project is an early state. As such, you might find bugs, flaws or mulfunctions.
Use it at your own risk!


Installation
=====
You can download the latest version of CMScout by cloning the GitHub repository:

     git clone https://github.com/creativeheadz/cmscout

Then you need to configure the `edbtype` and `edbpath` settings in `cmscout/cmscout.conf`. Use `GIT` if you have a local Git repository of Exploit-db :

    [exploitdb]
    edbtype = GIT
    edbpath = /opt/exploitdb/

Alternatively, use `APT` if you have installed the `debian` exploitdb package. For Kali, use the following settings :

    [exploitdb]
    edbtype = APT
    edbpath = /usr/share/exploitdb/

If you would like to run `cmscout` from anywhere in your system you can install it with `pip3` :

    cd cmscout
    pip3 install .

To uninstall it :

    pip3 uninstall cmscout -y


Usage
=====
    usage: cmscout.py [-f W/J/D/M] [-F] [-t] [-a] [-H] [-i] [-o] [-E] [-c] [-s]
                      [-d] [-u] [-p] [-x] [-k] [-w] [-v] [-h] [-D] [-U]
                      [target]

    CMScout tool v1.0 - Simple CMS Scanner
    Based on CMSmap by Mike Manzotti

    Scan:
      target                target URL (e.g. 'https://example.com:8080/')
      -f W/J/D/M, --force W/J/D/M
                            force scan (W)ordpress, (J)oomla or (D)rupal or (M)oodle
      -F, --fullscan        full scan using large plugin lists. False positives and slow!
      -t , --threads        number of threads (Default 5)
      -a , --agent          set custom user-agent
      -H , --header         add custom header (e.g. 'Authorization: Basic ABCD...')
      -i , --input          scan multiple targets listed in a given file
      -o , --output         save output in a file
      -E, --noedb           enumerate plugins without searching exploits
      -c, --nocleanurls     disable clean urls for Drupal only
      -s, --nosslcheck      don't validate the server's certificate
      -d, --dictattack      run low intense dictionary attack during scanning (5 attempts per user)

    Brute-Force:
      -u , --usr            username or username file
      -p , --psw            password or password file
      -x, --noxmlrpc        brute forcing WordPress without XML-RPC

    Post Exploitation:
      -k , --crack          password hashes file (Require hashcat installed. For WordPress and Joomla only)
      -w , --wordlist       wordlist file

    Others:
      -v, --verbose         verbose mode (Default false)
      -h, --help            show this help message and exit
      -D, --default         run CMScout with default options
      -U , --update         use (C)MScout, (P)lugins or (PC) for both

    Examples:
      cmscout.py https://example.com
      cmscout.py https://example.com -f W -F --noedb -d
      cmscout.py https://example.com -i targets.txt -o output.txt
      cmscout.py https://example.com -u admin -p passwords.txt
      cmscout.py -k hashes.txt -w passwords.txt


History and credit
=====
CMScout began as [CMSmap](https://github.com/Dionach/CMSmap), written by Mike
Manzotti and published by Dionach under the GPL-3.0. CMSmap has had no
commits since 2018. CMScout is an independent fork of that code, started in
October 2026 from the full CMSmap history and maintained by Andrei Trimbitas.

`cmsmap.py` still works: it forwards to `cmscout.py`, so command lines and
scripts written for CMSmap keep running.


Contribution guidelines
=====
If you want to contribute to CMScout, be sure to review the [contribution
guidelines](.github/CONTRIBUTING.md).


Disclaimer
=====
Usage of CMScout for attacking targets without prior mutual consent is illegal.
It is the end user's responsibility to obey all applicable local, state and federal laws.
Developers assume NO liability and are NOT responsible for any misuse or damage caused by this program.
