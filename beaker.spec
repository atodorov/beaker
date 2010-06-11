%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %global pyver %(%{__python} -c "import sys ; print sys.version[:3]")}
%{!?branch: %global branch %(echo "$Format:%d$"| awk -F/ '{print $NF}'| sed -e 's/[()$]//g' | awk '{print "." $NF}' | grep -v master)}
%if "0%{branch}" != "0"
%{!?timestamp: %global timestamp $Format:.%at$}
%endif

Name:           beaker
Version:        0.5.42
Release:        2%{?timestamp}%{?branch}%{?dist}
Summary:        Filesystem layout for Beaker
Group:          Applications/Internet
License:        GPLv2+
URL:            http://fedorahosted.org/beaker
Source0:        http://fedorahosted.org/releases/b/e/%{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch:      noarch
BuildRequires:  python-setuptools
BuildRequires:  python-setuptools-devel
BuildRequires:  python2-devel
BuildRequires:  TurboGears


%package client
Summary:        Client component for talking to Beaker server
Group:          Applications/Internet
Requires:       python
Requires:       kobo-client
Requires:	python-setuptools
Requires:	beaker
Requires:       python-krbV


%package server
Summary:       Server component of Beaker
Group:          Applications/Internet
Requires:       TurboGears
Requires:       intltool
Requires:       python-decorator
Requires:       python-xmltramp
Requires:       python-ldap
Requires:       mod_wsgi
Requires:       python-tgexpandingformwidget
Requires:       httpd
Requires:       python-krbV
Requires:       beaker
Requires:       python-TurboMail
Requires:	createrepo


%package lab-controller
Summary:        Lab Controller xmlrpc server
Group:          Applications/Internet
Requires:       python
Requires:       httpd
Requires:       cobbler >= 1.4
Requires:       yum-utils
%if 0%{?fedora} || 0%{?rhel} > 5
Requires:       /usr/sbin/fenced
%else
Requires:       /sbin/fenced
%endif
Requires:       telnet
Requires:       python-cpio
Requires:	beaker
Requires:	kobo-client
Requires:	python-setuptools
Requires:	python-xmltramp
Requires:       python-krbV

%description
Filesystem layout for beaker


%description client
This is the command line interface used to interact with the Beaker Server.


%description server
To Be Filled in - Server Side..


%description lab-controller
This is the interface to link Medusa and Cobbler together. Mostly provides
snippets and kickstarts.


%prep
%setup -q

%build
[ "$RPM_BUILD_ROOT" != "/" ] && [ -d $RPM_BUILD_ROOT ] && rm -rf $RPM_BUILD_ROOT;
DESTDIR=$RPM_BUILD_ROOT make

%install
DESTDIR=$RPM_BUILD_ROOT make install
ln -s RedHatEnterpriseLinux6.ks $RPM_BUILD_ROOT/%{_var}/lib/cobbler/kickstarts/redhat6.ks
ln -s Fedora.ks $RPM_BUILD_ROOT/%{_var}/lib/cobbler/kickstarts/Fedoradevelopment.ks

%clean
%{__rm} -rf %{buildroot}

%post server
/sbin/chkconfig --add beakerd

%post lab-controller
/sbin/chkconfig --add beaker-proxy
/sbin/chkconfig --add beaker-watchdog

%postun server
if [ "$1" -ge "1" ]; then
        /sbin/service beakerd condrestart >/dev/null 2>&1 || :
fi

%postun lab-controller
if [ "$1" -ge "1" ]; then
        /sbin/service beaker-proxy condrestart >/dev/null 2>&1 || :
        /sbin/service beaker-watchdog condrestart >/dev/null 2>&1 || :
fi

%preun server
if [ "$1" -eq "0" ]; then
        /sbin/service beakerd stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del beakerd || :
fi

%preun lab-controller
if [ "$1" -eq "0" ]; then
        /sbin/service beaker-proxy stop >/dev/null 2>&1 || :
        /sbin/service beaker-watchdog stop >/dev/null 2>&1 || :
        /sbin/chkconfig --del beaker-proxy || :
        /sbin/chkconfig --del beaker-watchdog || :
fi

%files
%defattr(-,root,root,-)
%{python_sitelib}/bkr/__init__.py*
%{python_sitelib}/bkr-%{version}-*
%{python_sitelib}/bkr-%{version}-py%{pyver}.egg-info/

%files server
%defattr(-,root,root,-)
%doc Server/README COPYING
%doc SchemaUpgrades/*
%{python_sitelib}/bkr/server/
%{python_sitelib}/bkr.server-%{version}-*
%{python_sitelib}/bkr.server-%{version}-py%{pyver}.egg-info/
%{_bindir}/start-%{name}
%{_bindir}/%{name}-init
%{_sysconfdir}/init.d/%{name}d
%attr(0755,root,root)%{_bindir}/%{name}d
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}-server.conf
%attr(-,apache,root) %{_datadir}/bkr
%attr(-,apache,root) %config(noreplace) %{_sysconfdir}/%{name}/server.cfg
%attr(-,apache,root) %dir %{_localstatedir}/log/%{name}
%attr(-,apache,root) %dir %{_localstatedir}/www/%{name}/logs
%attr(-,apache,root) %dir %{_localstatedir}/www/%{name}/rpms
%attr(-,apache,root) %dir %{_localstatedir}/run/%{name}

%files client
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/beaker/client.conf
%{python_sitelib}/bkr/client/
%{python_sitelib}/bkr.client-%{version}-*
%{python_sitelib}/bkr.client-%{version}-py%{pyver}.egg-info/
%{_bindir}/bkr

%files lab-controller
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/beaker/proxy.conf
%{python_sitelib}/bkr/labcontroller/
%{python_sitelib}/bkr.labcontroller-%{version}-*
%{python_sitelib}/bkr.labcontroller-%{version}-py%{pyver}.egg-info/
%{_bindir}/%{name}-proxy
%{_bindir}/%{name}-watchdog
%doc LabController/README
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}-lab-controller.conf
%{_sysconfdir}/cron.daily/expire_distros
%{_var}/lib/cobbler/triggers/sync/post/osversion.trigger
%{_var}/lib/cobbler/snippets/*
%{_var}/lib/cobbler/kickstarts/*
%{_var}/www/beaker/*
%attr(-,apache,root) %dir %{_localstatedir}/log/%{name}
%{_sysconfdir}/init.d/%{name}-proxy
%{_sysconfdir}/init.d/%{name}-watchdog

%changelog
* Tue Jun 08 2010 Bill Peck <bpeck@redhat.com> - 0.5.42-1
- bz570186 Hopefully fix: Ability to set system owner to a group or individual
- bz589904 tests which crashing the system will timeout the watchdog
- bz591384 getenv("TERM") returns NULL
- bz599086 improve configfile handling
- bz600353 Limiting architectures (releases) in Beaker 
* Mon Jun 07 2010 Bill Peck <bpeck@redhat.com> - 0.5.41-3
- added push and legacypush to proxy
* Tue Jun 01 2010 Bill Peck <bpeck@redhat.com> - 0.5.41-1
- minor update for bz598320
* Tue Jun 01 2010 Bill Peck <bpeck@redhat.com> - 0.5.41-0
- bz501511,RFE: Use STABLE trees by default
- bz582295,No Watchdog page anymore?
- bz583014,RFE] provide single_package.py replacement with same CLI interface
- bz584592,Inventory not UTF safe?
- bz591992,Job Status page: typo: ""Finsihed""
- bz594714,Beaker] [Job Matrix Report] Test column out of order leads to confusion
- bz596802,RFE] split bkr job-watch
- bz597155,variant option of workflow-simple doesn't work
- bz598320,show failed results' shows passed results also

* Tue May 25 2010 Bill Peck <bpeck@redhat.com> - 0.5.40-0
- minor fixes in command line workflow.
- minor fixes in command line task list.
- added new command distro-verify to help admins.
- 592978 "Change Job detail page to use AJAX for showing results"
- 570186 "[Beaker] RFE: Ability to set system owner to a group or individual"
- 541290 "[Beaker] RFE: Consistent use of the terminology."
- 580090 "Beaker doesn't take into account boot command line parameters"
- 594746 "[Beaker] [Execute Tasks] View does not report sub test results."
- 559337 "[Beaker] RFE: executed test report"
- 584586 "Importing labinfo results in 500 ISE"
- 584587 "Importing excludes doesn't work"
- 591147 "strange listing of systems with a particular devices"
- 591401 "RFE: User style searches for other admin pages."
- 594038 "Increase proper error handling"
* Mon May 17 2010 Bill Peck <bpeck@redhat.com> - 0.5.39-0
- fix job_matrix report to show virt recipes as well.
* Mon May 17 2010 Bill Peck <bpeck@redhat.com> - 0.5.38-1
- added --pid-file to beakerd startup. make sure only one beakerd is running at a time.
* Mon May 17 2010 Bill Peck <bpeck@redhat.com> - 0.5.38-0
- upaded proxy to only re-authenticate every 60 seconds.
- fixed beakerd to not look at systems not in Working state.
* Wed May 12 2010 Bill Peck <bpeck@redhat.com> - 0.5.37-0
- fixed proxy to fork properly
* Tue May 11 2010 Bill Peck <bpeck@redhat.com> - 0.5.36-0
- merged bz589723 - fix spelling mistakes
- merged bz589843 - cannot select systems in reserve workflow
- merged bz590665 - link to systems owner by a particular group gives internal error
- merged bz589857 - Distro search dies on 'Breed' search
* Mon May 10 2010 Bill Peck <bpeck@redhat.com> - 0.5.35-1
- Change default to /bkr
* Mon May 10 2010 Bill Peck <bpeck@redhat.com> - 0.5.35-0
- Fix beakerd to not do process_routine until all recipes are in state processed.
- possible fix for favicon.ico not being found.
* Fri May 07 2010 Bill Peck <bpeck@redhat.com> - 0.5.34-1
- fix syntax errors in beakerd
* Fri May 07 2010 Bill Peck <bpeck@redhat.com> - 0.5.34-0
- possible fix for same identity key exists in this session (beakerd)
- also fix it so scheduled_recipes routine always runs after queued_recipes
* Thu May 06 2010 Bill Peck <bpeck@redhat.com> - 0.5.33-2
- pushed remote cobbler method to a ten minute timeout.  some power options take this long.
* Thu May 06 2010 Bill Peck <bpeck@redhat.com> - 0.5.33-1
- added additional debug code to beakerd.
- default guest recipes to non virt distro, ask for it if you want virt.
* Thu May 06 2010 Bill Peck <bpeck@redhat.com> - 0.5.33-0
- Remove --cost from rhel5 kickstart templates.  rhel5 doesn't support --cost.
* Wed May 05 2010 Bill Peck <bpeck@redhat.com> - 0.5.32-2
- fix workflow-simple to handle taskparam correctly and task types/packages
* Wed May 05 2010 Bill Peck <bpeck@redhat.com> - 0.5.32-1
- fix BeakerJob classes to add tasks to the correct node.
* Wed May 05 2010 Bill Peck <bpeck@redhat.com> - 0.5.32-0
- New beaker-client command workflow-simple
- minor fix to tasks/filter to support new workflow
* Wed Apr 28 2010 Bill Peck <bpeck@redhat.com> - 0.5.31-3
- only release_system if there is an active watchdog.
* Wed Apr 28 2010 Bill Peck <bpeck@redhat.com> - 0.5.31-2
- release_system should now catch tracebacks from failed cobbler attempts.
* Wed Apr 28 2010 Bill Peck <bpeck@redhat.com> - 0.5.31-1
- merged bz586163 - fixes job matrix report
* Wed Apr 28 2010 Bill Peck <bpeck@redhat.com> - 0.5.31-0
- added both provision methods to distro link
* Tue Apr 27 2010 Bill Peck <bpeck@redhat.com> - 0.5.30-0
- remove uneeded @identity on /distros/ 
* Mon Apr 26 2010 Bill Peck <bpeck@redhat.com> - 0.5.29-2
- switch show/hide links to buttons.
- hide logs by default
- show clone link for all jobs.
* Mon Apr 26 2010 Bill Peck <bpeck@redhat.com> - 0.5.29-1
- really fix package tag issues
* Mon Apr 26 2010 Bill Peck <bpeck@redhat.com> - 0.5.29-0
- fix package tag issues
* Sat Apr 24 2010 Bill Peck <bpeck@redhat.com> - 0.5.28-0
- compress task results by default, links for showall and showfail if failures
  state it remembered via a cookie.
* Fri Apr 23 2010 Bill Peck <bpeck@redhat.com> - 0.5.27-1
- fixed bad merge
* Fri Apr 23 2010 Bill Peck <bpeck@redhat.com> - 0.5.27-0
- bz583535 - RFE Provision from distro page
- bz582879 - Show all - bug in tasks library
- bz582186 - Searches should default to Contains
- bz581684 - Remove Tag page for Distros, distro page can now search on tags
- bz581502 - Sort distro family list
- bz567788 - search should show number of items returned
- update rhts_partitions snippet to allow ondisk specification
- update kickstarts to support firewall variable
- bz557116 - Show/search systems owned by groups
- bz582729 - Fixed html title to show job/recipe etc.. id on each page
- includes pub docs
* Tue Apr 20 2010 Bill Peck <bpeck@redhat.com> - 0.5.26-0
- Example cleanup in rhts_partitions snippet
- Fixed osversion.trigger not to process distros without ks_meta['tree']
- moved mod_wsgi socket location to /var/run to make fedora happy
- replaced Unicode() with UnicodeText() to make fedora happy
- add <packages><package name=""/></packages> tags so cloning works for custom_packages.
- loosen error checking on root name spaces for new tasks.
* Thu Apr 15 2010 Bill Peck <bpeck@redhat.com> - 0.5.25-0
- remove mod_python requirement from lab-controller
- Add X.log monitoring to anamon
* Wed Apr 14 2010 Bill Peck <bpeck@redhat.com> - 0.5.24-0
- added missing installPackage tag processing.
* Tue Apr 13 2010 Bill Peck <bpeck@redhat.com> - 0.5.23-2
- fixed install_start to push guest watchdog entries out as well.
* Tue Apr 13 2010 Bill Peck <bpeck@redhat.com> - 0.5.23-1
- Merge remote branch 'origin/bz541281' No sorting, filtering, or pagination settings on Accounts list
- Merge remote branch 'origin/bz580091' quick links on Job/Recipe pages for "Running", "Queued"
* Tue Apr 13 2010 Bill Peck <bpeck@redhat.com> - 0.5.23-0
- fix firewall syntax for mutliple ports
* Mon Apr 12 2010 Bill Peck <bpeck@redhat.com> - 0.5.22-2
- add system specific kickstart snippets
- Merge remote branch 'origin/bz578420'
- Merge remote branch 'origin/master_variables'
- Merge remote branch 'origin/job_submit_nowait'
* Mon Apr 12 2010 Bill Peck <bpeck@redhat.com> - 0.5.22-1
- Opened port 12432 for beah multi-host by default.
* Mon Apr 12 2010 Bill Peck <bpeck@redhat.com> - 0.5.22-0
- Added recipeset_stop to proxy method.
* Sat Apr 10 2010 Bill Peck <bpeck@redhat.com> - 0.5.21-1
- cherry-picked rcm addRepo code from 0.4.x
* Sat Apr 10 2010 Bill Peck <bpeck@redhat.com> - 0.5.21-0
- fixed beakerd filtering on Status, actually is SystemStatus.
* Fri Apr 09 2010 Bill Peck <bpeck@redhat.com> - 0.5.20-0
- prepend log dir with year of start_time.
* Thu Apr 08 2010 Bill Peck <bpeck@redhat.com> - 0.5.19-1
- fixed scheduler to honor system status.
* Thu Apr 08 2010 Bill Peck <bpeck@redhat.com> - 0.5.19-0
- Merge remote branch 'origin/bz576327'
- Merge remote branch 'origin/bz579972'
- Merge remote branch 'origin/bz578383'
- Fixed --convert to handle <partition> tags in legacy xml
* Wed Apr 07 2010 Bill Peck <bpeck@redhat.com> - 0.5.18-3
- BZ #578548 - fix provided by gozen
- fixed hostRequires and distroRequires parsing to not choke on empty <and/> or <or/> tags
- display time left in duration column if watchdog exists
* Tue Apr 06 2010 Bill Peck <bpeck@redhat.com> - 0.5.17-2
- fixed bz 570986, "TypeError: string indices must be integers" in expire_distros
- fixed task_stop(cancel or abort) returning None.
- fixed child.filter() to not die on unrecognized tags.
* Mon Apr 05 2010 Bill Peck <bpeck@redhat.com> - 0.5.16-2
- make sure old task rpm exists before trying to remove it.
- overwrite repos, don't append in rhts_post snippet.
* Thu Apr 01 2010 Bill Peck <bpeck@redhat.com> - 0.5.15-8
- fix apache conf for beaker-server
- pass repos to cobbler, separate harness_repos from custom_repos
- allow ks_meta to be passed in from recipe
* Wed Mar 31 2010 Bill Peck <bpeck@redhat.com> - 0.5.15-1
- move harness repos to server from lab-controller.
* Wed Mar 31 2010 Bill Peck <bpeck@redhat.com> - 0.5.14-0
- update rhts-post snippet to only enable our repos.
* Tue Mar 30 2010 Bill Peck <bpeck@redhat.com> - 0.5.13-1
- removed uneeded task_list code
- default task result to pass when no result recorded, this is for css display.
- display log summary when task.path == /
* Mon Mar 29 2010 Bill Peck <bpeck@redhat.com> - 0.5.12-1
- merged bz574179, arch and distro search in tasks.
- added stdin support for bkr job-submit
- minor spec file changes for fedora package review.
- added xmlrpc method to tasks for getting list of all tasks
- added command module to list tasks
* Fri Mar 26 2010 Bill Peck <bpeck@redhat.com> - 0.5.11-0
- fix status_watchdog to return correct seconds if remaining time is over a day.
* Thu Mar 25 2010 Bill Peck <bpeck@redhat.com> - 0.5.10-0
- Added missing code to deal with priorities.
- Added missing code to order available systems by Owner,Group, then shared.
- fixed extend_watchdog to return status_watchdog()
- added status_watchdog method to return the number of seconds remaining on watchdog.
- added missing user variable for system sorting.
* Wed Mar 24 2010 Bill Peck <bpeck@redhat.com> - 0.5.8-1
- removed -lib subpackage. beakerlib is now its own project.
- fixed extend_watchdog to not return None.
* Wed Mar 24 2010 Bill Peck <bpeck@redhat.com> - 0.5.6-2
- merged rmancy fix for bz576446 - added MyJobs/MyRecipe links to menu.
- moved My menus to Login area.
* Tue Mar 23 2010 Bill Peck <bpeck@redhat.com> - 0.5.5-0
- merged rmancy fix for bz574178 - added recipe search.
* Tue Mar 23 2010 Bill Peck <bpeck@redhat.com> - 0.5.4-0
- merged rmancy fix for bz576420 - fixes task search
* Tue Mar 23 2010 Bill Peck <bpeck@redhat.com> - 0.5.3-0
- merged rmancy fix for bz574176 - searching in jobs 
- merged mcsontos fix for bz576128 - add help for beaker-client subcommands
* Thu Mar 18 2010 Bill Peck <bpeck@redhat.com> - 0.5.2-0
- Merged Scheduler into master, renamed site-packages/beaker to site-packages/bkr
* Thu Mar 04 2010 Bill Peck <bpeck@redhat.com> - 0.4.89-0
- update osversion.trigger to update pushed data before calling addDistro.sh
* Wed Mar 03 2010 Bill Peck <bpeck@redhat.com> - 0.4.88-0
- update osversion.trigger to ignore xen variants when calling addDistro.sh
* Wed Mar 03 2010 Bill Peck <bpeck@redhat.com> - 0.4.87-0
- fixed osversion.trigger, FAMILYUPDATE may not exist for some distros.
* Tue Mar 02 2010 Bill Peck <bpeck@redhat.com> - 0.4.86-1
- fixed osversion.trigger, Distro -> distro.
- extend visit timeout to 6 hours by default.
- really include System/Location in search bar.
* Wed Feb 24 2010 Bill Peck <bpeck@redhat.com> - 0.4.85-2
- Added @x11 and @basic-desktop to rhel6 kickstarts
* Fri Feb 19 2010 Raymond Mancy <rmancy@redhat.com> - 0.4.85-1
- refactored system search
- cast partition size to int() before multiplying. 
* Wed Feb 17 2010 Bill Peck <bpeck@redhat.com> - 0.4.84-1
- update osversion.trigger to only process newly imported distros
- add robustness to rhts_partitions snippet.
- rmancy merged history search.
* Mon Feb 15 2010 Bill Peck <bpeck@redhat.com> - 0.4.83-0
- Remove auth from rhel6 kickstart, default is sane.
- Includes rmancy's update, added cpu_model_name to search options.
- escape variables in cheetah snippets.
* Wed Feb 03 2010 Bill Peck <bpeck@redhat.com> - 0.4.82-3
- Don't expire nightlies in one week, leave it up to the filesystem
- fix bz#554852 don't remove any distros if all are missing
- Process KickPart directive from legacy rhts if passed in.
- Update rhts_partitions snippet to support fstype
- run addDistro.sh with variant specified in .treeinfo if available
- install options should override base options
* Tue Feb 02 2010 Bill Peck <bpeck@redhat.com> - 0.4.81-2
- Fix bz#560823 for rhel3 systems not checking in to rhts properly
- Fix ISE 500 when looking up an invalid profile on cobbler
- Fix for rt#58689 when importing anything but an nfs distro we get the location 
  of the repos wrong.
- Fix bz#555551 - missing location for search and custom columns
- Fix bz#559656 - unable to handle commented %packages in kickstart
- Merged AccountClosure code.
* Tue Jan 26 2010 Bill Peck <bpeck@redhat.com> - 0.4.80-0
- added support for variants being read from .treeinfo
* Mon Jan 25 2010 Bill Peck <bpeck@redhat.com> - 0.4.79-1
- add missing admin decorators to user methods
* Fri Jan 22 2010 Bill Peck <bpeck@redhat.com> - 0.4.79-0
- rename table key to key_, key is a reserved word.
- shorten key_name value to varchar(50) to support mysql Unique column limitation.
* Wed Jan 20 2010 Bill Peck <bpeck@redhat.com> - 0.4.78-0
- Remove redundant arch aliases
* Wed Jan 13 2010 Bill Peck <bpeck@redhat.com> - 0.4.77-0
- fix ISE 500 when adding new system
* Tue Jan 12 2010 Bill Peck <bpeck@redhat.com> - 0.4.76-1
- fix for cookies not being set.
* Tue Jan 12 2010 Bill Peck <bpeck@redhat.com> - 0.4.76-0
- merged bz554775 - added missing search columns and changed the order of Family/Model.
* Mon Jan 11 2010 Bill Peck <bpeck@redhat.com> - 0.4.76-0
- merged bz544347 - add condition field when system status set to broken or removed.
- merged ticket51 - custom columns.
- merged bz553421 - fixed requesting a system with arch=i386 and arch=x86_64 would fail.
* Fri Jan 08 2010 Bill Peck <bpeck@redhat.com> - 0.4.76-0
- Fixed regression, remove pxe entries when returning a system.
* Thu Jan 07 2010 Bill Peck <bpeck@redhat.com> - 0.4.76-0
- merged bz537414 - show version on beaker pages and have a link for reporting bugs.
* Tue Jan 05 2010 Bill Peck <bpeck@redhat.com> - 0.4.75-1
- Server/Client/LabController require beaker.
* Tue Jan 05 2010 Bill Peck <bpeck@redhat.com> - 0.4.74-0
- Merged Raymond's bz549912
- updated spec file to include branch name and timestamp
* Tue Dec 22 2009 Bill Peck <bpeck@redhat.com> - 0.4.70-0
- another fix to the release_action code. send proper action methods
  to cobbler, Off->off On->on.
* Thu Dec 17 2009 Bill Peck <bpeck@redhat.com> - 0.4.69-0
- small fix for release action, default to power off.
* Fri Dec 11 2009 Bill Peck <bpeck@redhat.com> - 0.4.68-0
- osversion now knows what arches are expected for that update.
  This allows us to only tag distros as STABLE if all arches are imported and tagged as INSTALLS
- update distro-list command to show the distro name, suitable for feeding into workflows.
* Wed Dec 09 2009 Bill Peck <bpeck@redhat.com> - 0.4.67-0
- Raymonds fix for is_not in arch search
- additional fixes from Raymond
- fix for beaker-init to create ReleaseAction Table
* Sun Dec 06 2009 Bill Peck <bpeck@redhat.com> - 0.4.65-0
- New ReleaseAction code, allows systems to stay on or
  reprovision at time of return.
* Tue Dec 01 2009 Bill Peck <bpeck@redhat.com> - 0.4.64-0
- Fix ISE in simplesearch
- added PATH=/usr/bin:$PATH to rhel3 kickstart
* Fri Nov 20 2009 Bill Peck <bpeck@redhat.com> - 0.4.63-0
- merged Raymond's Key/Value search ability
* Fri Nov 20 2009 Bill Peck <bpeck@redhat.com> - 0.4.62-1
- Fixes for searching drivers
- Random selection when more than one host available.
* Tue Nov 17 2009 Bill Peck <bpeck@redhat.com> - 0.4.61-0
- Fixes for searching on cpuflags
- new manual kickstart keyword allows interactive installs
* Wed Oct 28 2009 Bill Peck <bpeck@redhat.com> - 0.4.57-0
- New search implemented by Raymond Mancy
- don't try and power off machines that were temporarily reserved by legacy rhts
- view groups for non admin users
* Fri Oct 16 2009 Bill Peck <bpeck@redhat.com> - 0.4.53-0
- fix allows custom kickstarts to still append packages
* Tue Oct 06 2009 Bill Peck <bpeck@redhat.com> - 0.4.52-0
- pass !key along to cobbler for further processing.
* Mon Oct 05 2009 Bill Peck <bpeck@redhat.com> - 0.4.51-0
- fix for reserve report, not all records have a Reserved action.
* Thu Oct 01 2009 Bill Peck <bpeck@redhat.com> - 0.4.50-0
- Fixed system exclude to work properly from Distro.systems()
  previously excluding one arch would exclude all.
- added first report. reserve, shows length of currently reserved systems
- updated reserve report to honor NDA/secret settings.
* Wed Sep 30 2009 Petr Muller <pmuller@redhat.com> - 0.4.46-0
- backported few beakerlib fixes from the development branch
* Wed Sep 29 2009 Bill Peck <bpeck@redhat.com> - 0.4.45-0
- updated rhts-checkin to report anaconda logs to legacy rhts.
* Tue Sep 15 2009 Bill Peck <bpeck@redhat.com> - 0.4.44-0
- fixed wrong default language for Fedora kickstarts
- attempted to make broken search a little better.
* Thu Sep 10 2009 Bill Peck <bpeck@redhat.com> - 0.4.43-0
- added RHEL6/F12 package groups for development
* Thu Sep 03 2009 Bill Peck <bpeck@redhat.com> - 0.4.42-0
- fixed saving tag Activity on Distro.
* Thu Aug 27 2009 Bill Peck <bpeck@redhat.com> - 0.4.41-0
- use action_release() in controllers
* Thu Aug 27 2009 Bill Peck <bpeck@redhat.com> - 0.4.40-0
- option to not wait for power commands if talking to cobbler 1.7 or newer
* Tue Aug 25 2009 Bill Peck <bpeck@redhat.com> - 0.4.39-7
- re-worked remote calls to cobbler to be in their own sub-class.
  This was needed to support the latest version of cobbler.
- added not_anonymous tags around distro tagi add/remove methods.
* Fri Aug 21 2009 Petr Muller <pmuller@redhat.com> - 0.4.39-0
- cherry picked fixes from master branch for beakerlib:
- various doc fixes
- tweaked phase reporting 
- new options & functionality for rlRun
- enabling manual use of journal comparator
- new rlPass and rlFail functions
- new rlSendFile function
- plugin mechanism
- xml character breakage fix
* Thu Aug 20 2009 Bill Peck <bpeck@redhat.com> - 0.4.38-0
- Allow skipx in kickstarts to be passed in from metadata.
- Added xmlrpc method for editing distro Update.
* Wed Aug 12 2009 Bill Peck <bpeck@redhat.com> - 0.4.37-0
- Escape $ in custom kickstarts sent to cobbler
* Tue Aug 11 2009 Bill Peck <bpeck@redhat.com> - 0.4.36-0
- create subprofile
* Mon Aug 10 2009 Bill Peck <bpeck@redhat.com> - 0.4.34-0
- Change how custom kickstarts are handled. Don't copy
  cobbler profiles anymore, just use system profile and set
  parent if needed.
* Fri Aug 07 2009 Bill Peck <bpeck@redhat.com> - 0.4.33-0
- Allow the owner of a system to force a loan return.
* Wed Aug 05 2009 Bill Peck <bpeck@redhat.com> - 0.4.32-0
- Require users to be logged in to do actions and saves.
  This forces an automatic relogin if using kerberos.
* Tue Aug 04 2009 Bill Peck <bpeck@redhat.com> - 0.4.31-0
- fixed remove_distro call in expire distros
* Mon Aug 03 2009 Bill Peck <bpeck@redhat.com> - 0.4.30-0
- Updated osversion.trigger to not traceback when encountering an 
  unknown compressor.
* Tue Jul 28 2009 Bill Peck <bpeck@redhat.com> - 0.4.29-0
- Changes cobbler scripts to do everything through xmlrpc.
  cobbler gets confused otherwiese.
* Fri Jul 24 2009 Bill Peck <bpeck@redhat.com> - 0.4.28-0
- Fixed string_to_hash to not barf on extra spaces
* Mon Jul 20 2009 Bill Peck <bpeck@redhat.com> - 0.4.27-0
- Expanded user_name field to 255 chars.
* Mon Jul 20 2009 Bill Peck <bpeck@redhat.com> - 0.4.26-0
- Enable ntp in cobbler snippets
* Fri Jul 17 2009 Bill Peck <bpeck@redhat.com> - 0.4.25-0
- Fixed system arch filtering to be unicode not int.
* Thu Jul 16 2009 Bill Peck <bpeck@redhat.com> - 0.4.24-0
- Allow systems to query on arch even though we are already starting
  from a distro.  This allows you to ask for systems that are not x86_64
  for example.
- Don't fail if we can't power off a system when returning it.
- Use correct username when returning a system to the pool.
- Remove --resolvedeps from RHEL6 kickstart file.
* Tue Jul 14 2009 Bill Peck <bpeck@redhat.com> - 0.4.22-0
- Fix distro_method value to be unicode instead of boolean.
* Mon Jul 13 2009 Bill Peck <bpeck@redhat.com> - 0.4.21-0
- Allow legacy RHTS to ask for distros based on install method
* Tue Jul 07 2009 Bill Peck <bpeck@redhat.com> - 0.4.20-0
- Include Workstation key for RedHatEnterpriseLinuxClient5
* Mon Jul 06 2009 Bill Peck <bpeck@redhat.com> - 0.4.19-0
- Don't populate runtest_url in ks_meta if its not defined.
* Wed Jul 01 2009 Bill Peck <bpeck@redhat.com> - 0.4.18-2
- Use RUNTEST_URL from rhts if passed.
- Include Fedoradevelopment.ks for rawhide
* Tue Jun 30 2009 Bill Peck <bpeck@redhat.com> - 0.4.17-0
- Call the correct method for _tag
* Tue Jun 30 2009 Bill Peck <bpeck@redhat.com> - 0.4.16-0
- update login_krbv method for newer kobo package
* Tue Jun 30 2009 Bill Peck <bpeck@redhat.com> - 0.4.15-0
- Call addDistros.sh from osversion.trigger if it exists.
* Mon Jun 29 2009 Bill Peck <bpeck@redhat.com> - 0.4.14-0
- Allow searching by treepath for command line client
- return distro name for legacy rhts.
* Mon Jun 22 2009 Bill Peck <bpeck@redhat.com> - 0.4.13-0
- Fixed osversion.trigger to work with methods other than nfs
* Fri Jun 19 2009 Bill Peck <bpeck@redhat.com> - 0.4.12-0
- Raise BeakerExceptions if we run into trouble
* Thu Jun 18 2009 Bill Peck <bpeck@redhat.com> - 0.4.11-0
- added install_name to distro pick method
- fixed 500 error when non-admin adds a new system with shared set.
* Fri Jun 12 2009 Bill Peck <bpeck@redhat.com> - 0.4.9-1
- releng fixed the name of rhel6 to RedHatEnterpriseLinux6 in .treeinfo
* Wed Jun 10 2009 Bill Peck <bpeck@redhat.com> - 0.4.9
- Added simple json method for tagging distros as Installable.
- Added RHEL6 kickstart file.
* Wed Jun 03 2009 Bill Peck <bpeck@redhat.com> - 0.4.8
- Catch xmlrpc errors from cobbler and record/display them
* Mon Jun 01 2009 Bill Peck <bpeck@redhat.com> - 0.4.7
- added distros list,tag,untag to beaker-client
- fixed some minor issues with the xmlrpc interface.
* Thu May 28 2009 Bill Peck <bpeck@redhat.com> - 0.4.6
- Clear systems console log via xmlrpc
* Thu May 28 2009 Bill Peck <bpeck@redhat.com> - 0.4.5
- free and available views will only show working systems now.
* Tue May 26 2009 Bill Peck <bpeck@redhat.com> - 0.4.4
- Fixed missing power_id from CSV import/export
- Use $default_password_crypted from /etc/cobbler/settings unless $password 
  is set.
* Fri May 22 2009 Bill Peck <bpeck@redhat.com> - 0.4.2
- Added in beakerlib sub package
- Fixed tempfile close in osversion.trigger
* Thu May 21 2009 Bill Peck <bpeck@redhat.com> - 0.4-3
- fix power import
* Tue May 19 2009 Bill Peck <bpeck@redhat.com> - 0.4-1
- Major reworking of directory layout.
* Tue May 12 2009 Bill Peck <bpeck@redhat.com> - 0.3-1
- First stab at client interface