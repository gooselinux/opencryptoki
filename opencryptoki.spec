Name:			opencryptoki
Summary:		Implementation of the PKCS#11 (Cryptoki) specification v2.11
Version:		2.3.1
Release:		5%{?dist}
License:		CPL
Group:			System Environment/Base
URL:			http://sourceforge.net/projects/opencryptoki
Source:			http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tar.gz
Patch0:			%{name}-2.2.8-do-not-create-group-in-pkcs11_startup.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=547324
# https://sourceforge.net/tracker/?func=detail&aid=2992772&group_id=128009&atid=710344
Patch1:                 %{name}-2.3.0-lsb.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=547324
# https://sourceforge.net/tracker/?func=detail&aid=2992760&group_id=128009&atid=710344
Patch2:                 %{name}-2.3.1-pidfile.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=546274
# https://sourceforge.net/mailarchive/forum.php?thread_name=1274175144-26515-1-git-send-email-dan%40danny.cz&forum_name=opencryptoki-tech
# https://sourceforge.net/mailarchive/forum.php?thread_name=1274175144-26515-2-git-send-email-dan%40danny.cz&forum_name=opencryptoki-tech
Patch3:                 %{name}-2.3.1-bz546274.patch
BuildRoot:		%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
Requires(pre):		shadow-utils coreutils sed
Requires(post):		chkconfig
Requires(preun):	chkconfig
# This is for /sbin/service
Requires(preun):	initscripts
Requires(postun):	initscripts
BuildRequires:		openssl-devel trousers-devel
BuildRequires:		autoconf automake libtool
%ifarch s390 s390x
BuildRequires:		libica-devel >= 2.0
%endif
Requires:		%{name}-libs%{?_isa} = %{version}-%{release}

%description
openCryptoki implements the PKCS#11 specification v2.11. It includes support
for cryptographic hardware such as the IBM 4758 Cryptographic CoProcessor,
the IBM eServer Cryptographic Accelerator (FC 4960 on pSeries) or the Trusted
Platform Module (TPM) as well as a software token for testing.

%package libs
Group:			System Environment/Libraries
Summary:		The runtime libraries for opencryptoki package

%description libs
The runtime libraries for use with openCryptoki based applications.

%package devel
Group:			Development/Libraries
Summary:		Development files for openCryptoki
Requires:		%{name}-libs = %{version}-%{release}

%description devel
This package contains the development header files for building openCryptoki
based applications.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1

%build
# Upstream tarball has unnecessary executable perms set on the sources
find . -name '*.[ch]' -print0 | xargs -0 chmod -x

./bootstrap.sh
%configure 	\
%ifarch s390 s390x
	--enable-ccatok \
%endif
	--enable-tpmtok

make %{?_smp_mflags}

%install
rm -rf $RPM_BUILD_ROOT

make install DESTDIR=$RPM_BUILD_ROOT

mkdir -p $RPM_BUILD_ROOT/usr/include/opencryptoki
cp -a usr/include/pkcs11/{apiclient.h,pkcs11.h,pkcs11types.h} $RPM_BUILD_ROOT/usr/include/opencryptoki

# Move the initscript to its proper place
mkdir -p $RPM_BUILD_ROOT%{_initddir}
mv $RPM_BUILD_ROOT%{_sysconfdir}/init.d/pkcsslotd $RPM_BUILD_ROOT%{_initddir}/pkcsslotd

mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/%{name}

# Remove unwanted cruft
rm -rf doc/CVS
rm -f $RPM_BUILD_ROOT/%{_libdir}/%{name}/*.la
rm -f $RPM_BUILD_ROOT/%{_libdir}/%{name}/stdll/*.la
rm -rf $RPM_BUILD_ROOT/%{_datadir}/%{name}

%clean
rm -rf $RPM_BUILD_ROOT

%postun libs -p /sbin/ldconfig

%post libs -p /sbin/ldconfig

%postun
if [ "$1" -ge "1" ] ; then
	/sbin/service pkcsslotd condrestart >/dev/null 2>&1
fi
exit 0

%post
/sbin/chkconfig --add pkcsslotd
exit 0

%preun
if [ "$1" = "0" ] ; then
	/sbin/service pkcsslotd stop >/dev/null 2>&1
	/sbin/chkconfig --del pkcsslotd
fi
exit 0

%pre
getent group pkcs11 >/dev/null || groupadd -r pkcs11
# Add root to the pkcs11 group
/usr/sbin/usermod -G $(/usr/bin/id --groups --name root | /bin/sed -e '
# add the pkcs group if it is missing
/(^| )pkcs11( |$)/!s/$/ pkcs11/
# replace spaces by commas
y/ /,/
'),pkcs11  root
exit 0

%files
%defattr(-,root,root,-)
%doc FAQ README LICENSE doc/*
%{_initddir}/pkcsslotd
%{_sbindir}/*
%{_mandir}/man*/*
%dir %attr(770,root,pkcs11) %{_sharedstatedir}/%{name}
%ifarch s390 s390x
%doc usr/lib/pkcs11/cca_stdll/README-IBM_CCA_users
%endif

%files libs
%defattr(-,root,root,-)
%{_sysconfdir}/ld.so.conf.d/*
# Unversioned .so symlinks usually belong to -devel packages, but opencryptoki
# needs them in the main package, because:
#   pkcs11_startup looks for opencryptoki/stdll/*.so, and
#   documentation suggests that programs should dlopen "PKCS11_API.so".
%{_libdir}/opencryptoki
%{_libdir}/pkcs11

%files devel
%defattr(-,root,root,-)
%{_includedir}/*


%changelog
* Thu May 20 2010 Dan Horák <dhorak@redhat.com> 2.3.1-5
- rebuilt with CCA enabled (#604287)
- Resolves: #604287

* Thu May 20 2010 Dan Horák <dhorak@redhat.com> 2.3.1-4
- fixed issues from #546274
- Resolves: #546274

* Fri Apr 30 2010 Dan Horák <dhorak@redhat.com> 2.3.1-3
- fixed one more issue in the initscript (#547324)
- Related: #547324

* Tue Apr 27 2010 Dan Horák <dhorak@redhat.com> 2.3.1-2
- fixed pidfile creating and usage (#547324)
- Related: #547324

* Tue Mar  2 2010 Dan Horák <dhorak@redhat.com> 2.3.1-1
- New upstream release 2.3.1. (#559364)
- opencryptoki-2.3.0-fix-nss-breakage.patch was merged.
- updated pkcsslotd initscript (#547324)
- Resolves: #559364
- Related: #547324

* Mon Feb  8 2010 Dan Horák <dhorak@redhat.com> 2.3.0-6
- added missing action to pkcsslotd initscript (#547324)
- Related: #547324

* Fri Jan 22 2010 Dan Horák <dhorak@redhat.com> 2.3.0-5
- made pkcsslotd initscript LSB compliant (#547324)
- Resolves: #547324

* Fri Dec 11 2009 Dennis Gregorovic <dgregor@redhat.com> - 2.3.0-4.1
- Rebuilt for RHEL 6

* Mon Sep 07 2009 Michal Schmidt <mschmidt@redhat.com> 2.3.0-4
- Added opencryptoki-2.3.0-fix-nss-breakage.patch on upstream request.

* Fri Aug 21 2009 Tomas Mraz <tmraz@redhat.com> - 2.3.0-3
- rebuilt with new openssl

* Sun Aug 16 2009 Michal Schmidt <mschmidt@redhat.com> 2.3.0-2
- Require libica-2.0.

* Fri Aug 07 2009 Michal Schmidt <mschmidt@redhat.com> 2.3.0-1
- New upstream release 2.3.0:
  - adds support for RSA 4096 bit keys in the ICA token.

* Tue Jul 21 2009 Michal Schmidt <mschmidt@redhat.com> - 2.2.8-5
- Require arch-specific dependency on -libs.

* Tue Jul 21 2009 Michal Schmidt <mschmidt@redhat.com> - 2.2.8-4
- Return support for crypto hw on s390.
- Renamed to opencryptoki.
- Simplified multilib by putting libs in subpackage as suggested by Dan Horák.

* Tue Jul 21 2009 Michal Schmidt <mschmidt@redhat.com> - 2.2.8-2
- Fedora package based on RHEL-5 package.
