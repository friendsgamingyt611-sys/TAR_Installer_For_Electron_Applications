Name:           tifea
Version:        1.0.0
Release:        1%{?dist}
Summary:        Atomic transactional installer for desktop tarballs
License:        PolyForm-Noncommercial-1.0.0
URL:            https://github.com/yourusername/tifea
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel python3-pip python3-setuptools

%description
A declarative, self-healing CLI installer for software tarballs (.tar.gz, .tar.xz).
Features include atomic execution ledger, LIFO rollback, AppArmor/SELinux confinement,
icon extraction from ASAR bundles, desktop entry registration, and xdg-mime handlers.

%prep
%autosetup

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files tifea

# Install binary, man pages, completions, and metainfo
install -Dp -m 0755 bin/tifea %{buildroot}%{_bindir}/tifea
ln -sf tifea %{buildroot}%{_bindir}/tifiea
ln -sf tifea %{buildroot}%{_bindir}/targz-installer

install -Dp -m 0644 data/man/tifea.1 %{buildroot}%{_mandir}/man1/tifea.1
install -Dp -m 0644 data/completions/tifea.bash %{buildroot}%{_datadir}/bash-completion/completions/tifea
install -Dp -m 0644 data/completions/tifea.zsh %{buildroot}%{_datadir}/zsh/site-functions/_tifea
install -Dp -m 0644 data/completions/tifea.fish %{buildroot}%{_datadir}/fish/vendor_completions.d/tifea.fish
install -Dp -m 0644 data/metainfo/org.example.tifea.metainfo.xml %{buildroot}%{_datadir}/metainfo/org.example.tifea.metainfo.xml

%check
%pyproject_check_import

%files -f %{pyproject_files}
%{_bindir}/tifea
%{_bindir}/tifiea
%{_bindir}/targz-installer
%{_mandir}/man1/tifea.1*
%{_datadir}/bash-completion/completions/tifea
%{_datadir}/zsh/site-functions/_tifea
%{_datadir}/fish/vendor_completions.d/tifea.fish
%{_datadir}/metainfo/org.example.tifea.metainfo.xml

%changelog
* Sat Aug 08 2026 TIFEA Maintainers <maintainers@example.com> - 1.0.0-1
- Standardized release 1.0.0 following Linux packaging standards.
